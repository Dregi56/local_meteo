import logging
from datetime import timedelta

import requests
import xml.etree.ElementTree as ET
import xarray as xr

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant

from .const import DOMAIN, UPDATE_INTERVAL, CONF_LATITUDE, CONF_LONGITUDE

_LOGGER = logging.getLogger(__name__)


class LocalMeteoCoordinator(DataUpdateCoordinator):
    """Coordinator per gestione dati meteo multi-sorgente."""

    def __init__(self, hass: HomeAssistant, entry):
        self.hass = hass
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

        # === DPC (pioggia radar) ===
        try:
            sri = await self.hass.async_add_executor_job(self._fetch_dpc)
            data["rain_radar"] = sri
        except Exception as e:
            _LOGGER.warning("Errore DPC: %s", e)
            data["rain_radar"] = None

        # === ARPAV (stazione reale) ===
        try:
            arpav_data = await self.hass.async_add_executor_job(self._fetch_arpav)
            data.update(arpav_data)
        except Exception as e:
            _LOGGER.warning("Errore ARPAV: %s", e)

        # === Open-Meteo (fallback + forecast) ===
        try:
            openmeteo = await self.hass.async_add_executor_job(self._fetch_openmeteo)
            data["forecast"] = openmeteo
        except Exception as e:
            _LOGGER.warning("Errore Open-Meteo: %s", e)

        # === Calcolo condizione cielo ===
        data["sky"] = self._compute_sky(data)

        return data

    # =========================
    # 🔹 DPC radar
    # =========================
    def _fetch_dpc(self):
        url = "https://dati.protezionecivile.gov.it/radar/SRI/latest.nc"
        r = requests.get(url, timeout=10)
        with open("/tmp/latest.nc", "wb") as f:
            f.write(r.content)

        ds = xr.open_dataset("/tmp/latest.nc")
        sri = ds.sel(latitude=self.lat, longitude=self.lon, method="nearest")["SRI"].values.item()
        return float(sri)

    # =========================
    # 🔹 ARPAV
    # =========================
    def _fetch_arpav(self):
        url_stazioni = "https://tele.arpav.it/meteoidro/xml/stazioni.xml"
        r = requests.get(url_stazioni, timeout=10)
        root = ET.fromstring(r.content)

        closest_station = None
        min_dist = float("inf")

        for stazione in root.findall("stazione"):
            st_lat = float(stazione.find("latitudine").text)
            st_lon = float(stazione.find("longitudine").text)
            dist = (self.lat - st_lat) ** 2 + (self.lon - st_lon) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_station = stazione

        st_id = closest_station.find("id").text
        url_data = f"https://tele.arpav.it/meteoidro/xml/{st_id}.xml"

        r = requests.get(url_data, timeout=10)
        data_root = ET.fromstring(r.content)

        return {
            "temperature": float(data_root.find("temperatura").text),
            "humidity": float(data_root.find("umidita").text),
            "wind_speed": float(data_root.find("vento_vel").text),
            "wind_direction": float(data_root.find("vento_dir").text),
            "rain": float(data_root.find("precipitazioni").text),
        }

    # =========================
    # 🔹 Open-Meteo
    # =========================
    def _fetch_openmeteo(self):
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={self.lat}&longitude={self.lon}"
            f"&current=temperature_2m,wind_speed_10m,wind_direction_10m"
        )

        r = requests.get(url, timeout=10)
        data = r.json()

        return data.get("current", {})

    # =========================
    # 🔹 Sky condition
    # =========================
    def _compute_sky(self, data):
        rain = data.get("rain_radar") or data.get("rain") or 0

        if rain == 0:
            return "sereno"
        elif rain <= 1:
            return "nuvoloso"
        elif rain <= 5:
            return "pioggia moderata"
        else:
            return "temporale"
