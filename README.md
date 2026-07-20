# Czytania dnia - Home Assistant Integration

Integracja Home Assistant pobierająca dzisiejsze czytania liturgiczne ze strony [mateusz.pl](https://mateusz.pl/czytania/) i umożliwiająca ich odczytanie poprzez serwis TTS (Text-to-Speech).

## Funkcje

- 📖 Pobieranie czytań liturgicznych na każdy dzień
- 🔔 Udostępnianie czytań jako sensor entity z atrybutami
- 🔊 Serwis do odczytania czytań poprzez TTS
- 🇵🇱 Pełna obsługa języka polskiego
- ⚙️ Automatyczne odświeżanie danych co godzinę

## Instalacja

### Metoda 1: HACS (zalecane)

1. Otwórz Home Assistant
2. Przejdź do HACS → Integrations
3. Kliknij `+ Create custom repository`
4. Wpisz URL: `https://github.com/nocond-jpg/czytania`
5. Kategoria: `Integration`
6. Kliknij `Create`
7. Wyszukaj "Czytania dnia" i kliknij `Download`
8. Zrestartuj Home Assistant

### Metoda 2: Ręczna instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/nocond-jpg/czytania.git
```

2. Skopiuj folder do Home Assistant:
```bash
cp -r czytania/custom_components/czytania_dnia ~/.homeassistant/custom_components/
```

3. Zrestartuj Home Assistant

## Konfiguracja

1. Przejdź do Settings → Devices & Services
2. Kliknij `Create Integration`
3. Wyszukaj i wybierz "Czytania dnia"
4. Potwierdź konfigurację

## Użytkownik

### Sensor

Po zainstalowaniu pojawi się sensor `sensor.czytania_dnia` z następującymi informacjami:

- **Stan**: Data czytań (YYYY-MM-DD)
- **Atrybuty**:
  - `liczba_czytan`: Liczba czytań na dzień
  - `pierwsze_czytanie`: Tekst pierwszego czytania
  - `psalm`: Tekst psalmu
  - `drugie_czytanie`: Tekst drugiego czytania (w niedziele)
  - `ewangelia`: Tekst Ewangelii

### Serwis `czytania_dnia.przeczytaj`

Serwis do odczytania czytań poprzez TTS.

**Parametry:**
- `notify_service` (wymagane): Pełna nazwa serwisu notify, np. `notify.mobile_app_telefon`
- `media_stream` (opcjonalne): Strumień audio, np. `alarm_stream` lub `alarm_stream_max`

**Przykład automacji:**

```yaml
automation:
  - alias: "Przeczytaj czytania o 7:00"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: czytania_dnia.przeczytaj
      data:
        notify_service: notify.mobile_app_moj_telefon
        media_stream: alarm_stream_max
```

**Przykład w script:**

```yaml
script:
  przeczytaj_czytania:
    sequence:
      - service: czytania_dnia.przeczytaj
        data:
          notify_service: notify.mobile_app_moj_telefon
```

## Wymagania

- Home Assistant 2024.1.0 lub nowszy
- beautifulsoup4 (instalowane automatycznie)

## Struktura plików

```
czytania/
├── README.md
├── hacs.json
└── custom_components/
    └── czytania_dnia/
        ├── __init__.py
        ├── manifest.json
        ├── config_flow.py
        ├── const.py
        ├── sensor.py
        ├── strings.json
        └── translations/
            └── pl.json
```

## Rozwiązywanie problemów

### Czytania się nie pobierają
- Sprawdź czy Home Assistant ma dostęp do internetu
- Sprawdź czy serwis mateusz.pl jest dostępny
- Odśwież sensor `sensor.czytania_dnia` w Developer Tools

### Błąd przy konfiguracji
- Usuń integrację i zainstaluj ją ponownie
- Sprawdź logi Home Assistant w Settings → System → Logs

## Autorzy

- [@nocond-jpg](https://github.com/nocond-jpg)

## Licencja

MIT License - siehe LICENSE file

## Благодарности

- [mateusz.pl](https://mateusz.pl/czytania/) za dostarczanie czytań
- Home Assistant Community za wsparcie i narzędzia
