import logging
from datetime import timedelta
import aiohttp
import xml.etree.ElementTree as ET
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from .const import DOMAIN, UPDATE_INTERVAL, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)


class LocalMeteoCoordinator(DataUpdateCoordinator):
    """Coordinator per gestione dati meteo multi-sorgente."""

    def __init__(self, hass: HomeAssistant, entry):
        self.lat = entry.data[CONF_LATITUDE]
        self.lon = entry.data[CONF_LONGITUDE]
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Aggiorna tutti i dati meteo."""
        data = {}

        # === Open-Meteo (dati attuali + forecast + pioggia) ===
        try:
            openmeteo = await self._fetch_openmeteo()
            data.update(openmeteo)
        except Exception as e:
            _LOGGER.warning("Errore Open-Meteo: %s", e)

        # === ARPAV (stazione reale) ===
        try:
            arpav_data = await self.hass.async_add_executor_job(self._fetch_arpav)
            data.update(arpav_data)
        except Exception as e:
            _LOGGER.warning("Errore ARPAV: %s", e)

        # === Calcolo condizione cielo ===
        data["sky"] = self._compute_sky(data)

        return data

    # =========================
    # Open-Meteo (async nativo)
    # =========================
    async def _fetch_openmeteo(self):
        """Scarica dati attuali, previsioni e precipitazioni da Open-Meteo."""
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.lat}&longitude={self.lon}"
            f"&current=temperature_2m,relative_humidity_2m,"
            f"precipitation,cloud_cover,wind_speed_10m,wind_direction_10m"
            f"&minutely_15=precipitation"
            f"&forecast_days=1"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
