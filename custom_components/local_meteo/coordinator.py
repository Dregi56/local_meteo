import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import arpav
from .const import (
    ARPAV_MAX_KM,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION,
    DOMAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class LocalMeteoCoordinator(DataUpdateCoordinator):
    """Coordinator per gestione dati meteo multi-sorgente."""

    def __init__(self, hass: HomeAssistant, entry):
        self.lat = entry.data[CONF_LATITUDE]
        self.lon = entry.data[CONF_LONGITUDE]
        self.station_id = entry.data.get(CONF_STATION)  # None = automatica
        self._session = async_get_clientsession(hass)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        data = {}

        try:
            data.update(await self._fetch_openmeteo())
        except Exception as e:
            _LOGGER.warning("Errore Open-Meteo: %s", e)

        try:
            data.update(await self._fetch_arpav())
        except Exception as e:
            _LOGGER.warning("Errore ARPAV: %s", e)

        data["sky"] = self._compute_sky(data)
        return data

    async def _fetch_openmeteo(self):
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.lat}&longitude={self.lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,cloud_cover,wind_speed_10m,wind_direction_10m,"
            f"wind_gusts_10m,pressure_msl,uv_index,visibility,dew_point_2m"
            f"&minutely_15=precipitation"
            f"&forecast_days=1"
        )
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            raw = await resp.json()

        current = raw.get("current", {})
        minutely = raw.get("minutely_15", {})
        times = minutely.get("time", [])
        values = minutely.get("precipitation", [])
        now = current.get("time")
        rain_radar = values[times.index(now)] if now in times else None

        return {
            "temperature":          current.get("temperature_2m"),
            "humidity":             current.get("relative_humidity_2m"),
            "apparent_temperature": current.get("apparent_temperature"),
            "dew_point":            current.get("dew_point_2m"),
            "pressure":             current.get("pressure_msl"),
            "wind_speed":           current.get("wind_speed_10m"),
            "wind_direction":       current.get("wind_direction_10m"),
            "wind_gusts":           current.get("wind_gusts_10m"),
            "rain":                 current.get("precipitation", 0),
            "rain_radar":           rain_radar,
            "uv_index":             current.get("uv_index"),
            "visibility":           current.get("visibility"),
            "cloudcover":           current.get("cloud_cover"),
        }

    async def _fetch_arpav(self):
        """Dati dalla stazione ARPAV scelta (o dalla più vicina)."""
        stations = await arpav.async_get_stations(self._session)

        if self.station_id:
            station = next((s for s in stations if s["id"] == self.station_id), None)
        else:
            nearest = arpav.nearest_stations(stations, self.lat, self.lon, limit=1)
            station = nearest[0] if nearest else None
            if station and station["distance_km"] > ARPAV_MAX_KM:
                _LOGGER.debug(
                    "ARPAV: stazione più vicina a %.0f km, la ignoro", station["distance_km"]
                )
                return {}

        if station is None:
            _LOGGER.warning("ARPAV: stazione non trovata")
            return {}

        data = await arpav.async_get_station_data(self._session, station["link"])
        if data:
            data["arpav_station"] = station["name"]
        return data

    def _compute_sky(self, data: dict) -> str:
        rain = data.get("rain") or 0
        cloudcover = data.get("cloudcover")

        if rain > 5:
            return "temporale"
        elif rain > 0:
            return "pioggia leggera"

        if cloudcover is not None:
            if cloudcover < 20:
                return "sereno"
            elif cloudcover < 50:
                return "poco nuvoloso"
            else:
                return "nuvoloso"

        return "sereno"
