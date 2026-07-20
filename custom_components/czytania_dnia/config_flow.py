"""Config flow dla integracji Czytania dnia."""
from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class CzytaniaDniaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Prosty flow - integracja nie wymaga żadnych danych konfiguracyjnych."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok konfiguracji użytkownika."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Czytania dnia", data={})

        return self.async_show_form(step_id="user")
