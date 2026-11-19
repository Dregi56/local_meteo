import logging
import xml.etree.ElementTree as ET

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import arpav
from .const import CONF_STATION, DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_CITY = "city"
STATION_AUTO = "auto"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocationFlowMixin:
    """Logica condivisa tra config flow e options flow."""

    _results: list
    _pending: dict
    _stations: list

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
            return await self._after_location(entry)
        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required("location"): vol.In(options)}),
        )

    async def _after_location(self, entry: dict):
        """Dopo la località: propone la scelta della stazione ARPAV."""
        self._pending = entry
        try:
            session = async_get_clientsession(self.hass)
            stations = await arpav.async_get_stations(session)
            self._stations = arpav.nearest_stations(
                stations, entry["data"][CONF_LATITUDE], entry["data"][CONF_LONGITUDE]
            )
        except (aiohttp.ClientError, TimeoutError, ET.ParseError):
            self._stations = []
        if not self._stations:
            return self._finish(entry)  # nessuna scelta possibile: automatica
        return await self.async_step_station()

    async def async_step_station(self, user_input=None):
        if user_input is not None:
            data = dict(self._pending["data"])
            if user_input[CONF_STATION] != STATION_AUTO:
                data[CONF_STATION] = user_input[CONF_STATION]
            return self._finish({"title": self._pending["title"], "data": data})

        options = {STATION_AUTO: "Automatica (la più vicina)"}
        for s in self._stations:
            options[s["id"]] = (
                f"{s['name']} ({s['comune']}, {s['type']}) – {s['distance_km']:.1f} km"
            )
        default = self._default_station()
        if default not in options:
            default = STATION_AUTO
        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {vol.Required(CONF_STATION, default=default): vol.In(options)}
            ),
        )


class LocalMeteoConfigFlow(LocationFlowMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow Local Meteo."""

    VERSION = 1

    def __init__(self):
        self._results = []
        self._pending = {}
        self._stations = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return LocalMeteoOptionsFlow()

    def _default_station(self):
        return STATION_AUTO

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
                return await self._after_location(entry)

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
    """Cambio località e stazione dopo l'installazione (pulsante Configura)."""

    def __init__(self):
        self._results = []
        self._pending = {}
        self._stations = []

    def _default_station(self):
        return self.config_entry.data.get(CONF_STATION, STATION_AUTO)

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
                return await self._after_location(entry)

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
