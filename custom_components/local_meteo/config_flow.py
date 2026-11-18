import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_CITY = "city"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocationFlowMixin:
    """Logica di ricerca città condivisa tra config flow e options flow."""

    _results: list

    async def _geocode(self, city: str) -> list:
        session = async_get_clientsession(self.hass)
        params = {"name": city, "count": 10, "language": "it", "format": "json"}
        async with session.get(
            GEOCODING_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data.get("results", [])

    @staticmethod
    def _label(r: dict) -> str:
        parts = [r.get("admin2"), r.get("admin1"), r.get("country")]
        extra = ", ".join(p for p in parts if p)
        return f"{r['name']} ({extra})" if extra else r["name"]

    def _entry_from_result(self, r: dict) -> dict:
        return {
            "title": self._label(r),
            "data": {
                CONF_LATITUDE: r["latitude"],
                CONF_LONGITUDE: r["longitude"],
                CONF_CITY: r["name"],
            },
        }

    def _home_entry(self) -> dict:
        return {
            "title": "Local Meteo",
            "data": {
                CONF_LATITUDE: self.hass.config.latitude,
                CONF_LONGITUDE: self.hass.config.longitude,
            },
        }

    async def _resolve(self, city: str | None):
        """Ritorna (entry, errore). entry == {} significa: serve scegliere."""
        city = (city or "").strip()
        if not city:
            return self._home_entry(), None
        try:
            self._results = await self._geocode(city)
        except (aiohttp.ClientError, TimeoutError):
            return None, "cannot_connect"
        if not self._results:
            return None, "city_not_found"
        if len(self._results) == 1:
            return self._entry_from_result(self._results[0]), None
        return {}, None

    async def async_step_select(self, user_input=None):
        options = {str(i): self._label(r) for i, r in enumerate(self._results)}
        if user_input is not None:
            entry = self._entry_from_result(self._results[int(user_input["location"])])
            return self._finish(entry)
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required("location"): vol.In(options)}),
        )


class LocalMeteoConfigFlow(LocationFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow Local Meteo."""

    VERSION = 1

    def __init__(self):
        self._results = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LocalMeteoOptionsFlow()

    def _finish(self, entry: dict):
        return self.async_create_entry(title=entry["title"], data=entry["data"])

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            entry, error = await self._resolve(user_input.get(CONF_CITY))
            if error:
                errors["base"] = error
            elif not entry:
                return await self.async_step_select()
            else:
                return self._finish(entry)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Optional(CONF_CITY): str}),
            description_placeholders={
                "lat": f"{self.hass.config.latitude:.4f}",
                "lon": f"{self.hass.config.longitude:.4f}",
            },
            errors=errors,
        )


class LocalMeteoOptionsFlow(LocationFlowMixin, config_entries.OptionsFlow):
    """Cambio località dopo l'installazione (pulsante Configura)."""

    def __init__(self):
        self._results = []

    def _finish(self, entry: dict):
        self.hass.config_entries.async_update_entry(
            self.config_entry, title=entry["title"], data=entry["data"]
        )
        return self.async_create_entry(title="", data={})

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            entry, error = await self._resolve(user_input.get(CONF_CITY))
            if error:
                errors["base"] = error
            elif not entry:
                return await self.async_step_select()
            else:
                return self._finish(entry)

        current = self.config_entry.data.get(CONF_CITY)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Optional(CONF_CITY, description={"suggested_value": current}): str}
            ),
            description_placeholders={
                "lat": f"{self.hass.config.latitude:.4f}",
                "lon": f"{self.hass.config.longitude:.4f}",
            },
            errors=errors,
        )
