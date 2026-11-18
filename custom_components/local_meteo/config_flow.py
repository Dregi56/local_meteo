import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_CITY = "city"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


class LocalMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow Local Meteo con ricerca per nome città."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        self._results = []

    async def _geocode(self, city: str) -> list[dict]:
        """Cerca la città su Open-Meteo Geocoding e ritorna la lista dei risultati."""
        session = async_get_clientsession(self.hass)
        params = {
            "name": city,
            "count": 10,
            "language": "it",
            "format": "json",
        }
        async with session.get(
            GEOCODING_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
        return data.get("results", [])

    @staticmethod
    def _label(r: dict) -> str:
        """Etichetta leggibile: Comune (Provincia, Regione, Paese)."""
        parts = [r.get("admin2"), r.get("admin1"), r.get("country")]
        extra = ", ".join(p for p in parts if p)
        return f"{r['name']} ({extra})" if extra else r["name"]

    def _create(self, r: dict):
        return self.async_create_entry(
            title=self._label(r),
            data={
                CONF_LATITUDE: r["latitude"],
                CONF_LONGITUDE: r["longitude"],
                CONF_CITY: r["name"],
            },
        )

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            city = (user_input.get(CONF_CITY) or "").strip()

            if city:
                try:
                    self._results = await self._geocode(city)
                except (aiohttp.ClientError, TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    if not self._results:
                        errors["base"] = "city_not_found"
                    elif len(self._results) == 1:
                        return self._create(self._results[0])
                    else:
                        return await self.async_step_select()
            else:
                # Fallback manuale: città vuota -> coordinate
                lat = user_input.get(CONF_LATITUDE)
                lon = user_input.get(CONF_LONGITUDE)
                if lat is None or lon is None:
                    errors["base"] = "city_or_coordinates"
                elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    errors["base"] = "invalid_coordinates"
                else:
                    return self.async_create_entry(
                        title="Local Meteo",
                        data={CONF_LATITUDE: lat, CONF_LONGITUDE: lon},
                    )

        schema = vol.Schema(
            {
                vol.Optional(CONF_CITY): str,
                vol.Optional(CONF_LATITUDE): float,
                vol.Optional(CONF_LONGITUDE): float,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_select(self, user_input=None):
        """Più risultati: l'utente sceglie quello giusto."""
        options = {str(i): self._label(r) for i, r in enumerate(self._results)}

        if user_input is not None:
            return self._create(self._results[int(user_input["location"])])

        return self.async_show_form(
            step_id="select",
            data_schema=vol.Schema({vol.Required("location"): vol.In(options)}),
        )
