"""Integracja Czytania dnia - pobiera czytania liturgiczne i pozwala je odczytać przez TTS."""
from __future__ import annotations

import asyncio
import datetime
import logging
import re

import aiohttp
import voluptuous as vol
from bs4 import BeautifulSoup

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BASE_URL, DEFAULT_UPDATE_INTERVAL_HOURS, DOMAIN, SERVICE_PRZECZYTAJ

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("notify_service"): str,
        vol.Optional("media_stream"): str,
    }
)


def _parse_html(raw: bytes) -> dict:
    """Parsowanie strony mateusz.pl (działa w wątku wykonawczym, nie w pętli async)."""
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("iso-8859-2", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "iframe", "img"]):
        tag.decompose()
    full_text = soup.get_text("\n", strip=True)

    match = re.search(r"\nCzytania\n(.*?)\nRozważania do czytań\n", full_text, re.S)
    section = match.group(1) if match else full_text
    # usuwamy blok "Aklamacja ... " przed kolejnym odnosnikiem biblijnym
    section = re.sub(r"Aklamacja.*?(?=\()", "", section, flags=re.S)

    # tekst jest podzielony odnosnikami biblijnymi w nawiasach, np. (Mdr 12,13-19)
    parts = re.split(r"\(([^)]{3,60})\)", section)
    readings: list[dict] = []
    
    for i in range(1, len(parts), 2):
        sigla = parts[i] if i < len(parts) else ""  # Źródło np. "Ps 23,1"
        txt = parts[i + 1] if i + 1 < len(parts) else ""
        
        # Zachowaj wiersze - zamień wielokrotne spacje/taby na spacje, ale ZA BARDZO nie czyszcz newlines
        txt = re.sub(r"[ \t]+", " ", txt)  # Zamień wielokrotne spacje/taby na jedną spację
        txt = re.sub(r"\n\s*\n", "\n", txt)  # Usuń puste linie (podwójne newline)
        txt = txt.strip()
        
        if txt:
            # Dodaj sygłę na początku
            formatted_text = f"({sigla})\n{txt}"
            readings.append({"sigla": sigla, "text": formatted_text})

    count = len(readings)
    if count == 4:
        labels = ["Pierwsze czytanie", "Psalm", "Drugie czytanie", "Ewangelia"]
    elif count == 3:
        labels = ["Pierwsze czytanie", "Psalm", "Ewangelia"]
    else:
        labels = [f"Czytanie {i + 1}" for i in range(count)]

    return {
        "date": datetime.date.today().isoformat(),
        "readings": [{"label": label, "text": text["text"], "sigla": text["sigla"]} 
                     for label, text in zip(labels, readings)],
    }


async def _async_fetch_readings(hass: HomeAssistant) -> dict:
    """Pobierz czytania z mateusz.pl."""
    today = datetime.date.today()
    url = BASE_URL.format(year=today.year, ymd=today.strftime("%Y%m%d"))
    session = async_get_clientsession(hass)
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        raw = await resp.read()
    return await hass.async_add_executor_job(_parse_html, raw)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja integracji."""
    async def _async_update_data():
        try:
            return await _async_fetch_readings(hass)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Błąd pobierania czytań: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_data,
        update_interval=datetime.timedelta(hours=DEFAULT_UPDATE_INTERVAL_HOURS),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _handle_przeczytaj(call: ServiceCall) -> None:
        """Obsługa usługi przeczytaj."""
        notify_service = call.data["notify_service"]
        media_stream = call.data.get("media_stream")
        data = coordinator.data or {}
        readings = data.get("readings", [])
        if not readings:
            _LOGGER.warning("Brak pobranych czytań - spróbuj odświeżyć encję przed wywołaniem")
            return

        domain, _, service = notify_service.partition(".")
        domain = domain or "notify"
        service = service or notify_service

        for reading in readings:
            payload = {"tts_text": f"{reading['label']}. {reading['text']}"}
            if media_stream:
                payload["media_stream"] = media_stream
            await hass.services.async_call(
                domain,
                service,
                {"message": "TTS", "data": payload},
                blocking=True,
            )
            words = len(reading["text"].split())
            pause_seconds = max(8, words / 2.3 + 3)
            await asyncio.sleep(pause_seconds)

    if not hass.services.has_service(DOMAIN, SERVICE_PRZECZYTAJ):
        hass.services.async_register(
            DOMAIN, SERVICE_PRZECZYTAJ, _handle_przeczytaj, schema=SERVICE_SCHEMA
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rozładowanie integracji."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
