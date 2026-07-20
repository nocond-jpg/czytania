"""Encja sensor pokazująca dzisiejsze czytania jako atrybuty."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Konfiguracja sensora."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CzytaniaDniaSensor(coordinator)])


class CzytaniaDniaSensor(CoordinatorEntity, SensorEntity):
    """Stan = data czytań, atrybuty = treść poszczególnych czytań."""

    _attr_name = "Czytania dnia"
    _attr_icon = "mdi:book-cross"
    _attr_unique_id = "czytania_dnia_sensor"

    @property
    def native_value(self):
        """Zwróć datę jako stan."""
        return (self.coordinator.data or {}).get("date")

    @property
    def extra_state_attributes(self):
        """Zwróć czytania jako atrybuty."""
        data = self.coordinator.data or {}
        readings = data.get("readings", [])
        attrs = {"liczba_czytan": len(readings)}
        for reading in readings:
            key = reading["label"].lower().replace(" ", "_")
            attrs[key] = reading["text"]
        return attrs
