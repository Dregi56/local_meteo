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

        # === Open-Meteo (dati attuali + pioggia istantanea) ===
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
        """Scarica dati attuali e pioggia istantanea da Open-Meteo."""
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={self.lat}&longitude={self.lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
            f"precipitation,cloud_cover,wind_speed_10m,wind_direction_10m,"
            f"wind_gusts_10m,pressure_msl,uv_index,visibility,dew_point_2m"
            f"&minutely_15=precipitation"
            f"&forecast_days=1"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                raw = await resp.json()

        current = raw.get("current", {})
        minutely = raw.get("minutely_15", {})
        rain_radar = None
        if "precipitation" in minutely and len(minutely["precipitation"]) > 0:
            rain_radar = minutely["precipitation"][0]

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

    # =========================
    # ARPAV (sincrono in executor)
    # =========================
    def _fetch_arpav(self):
        """Recupera dati dalla stazione ARPAV più vicina."""
        import requests

        url_stazioni = "https://tele.arpav.it/meteoidro/xml/stazioni.xml"
        r = requests.get(url_stazioni, timeout=10)
        root = ET.fromstring(r.content)

        closest_station = None
        min_dist = float("inf")
        for stazione in root.findall("stazione"):
            try:
                st_lat = float(stazione.find("latitudine").text)
                st_lon = float(stazione.find("longitudine").text)
                dist = (self.lat - st_lat) ** 2 + (self.lon - st_lon) ** 2
                if dist < min_dist:
                    min_dist = dist
                    closest_station = stazione
            except (TypeError, ValueError):
                continue

        if closest_station is None:
            _LOGGER.warning("ARPAV: nessuna stazione trovata")
            return {}

        st_id = closest_station.find("id").text
        url_data = f"https://tele.arpav.it/meteoidro/xml/{st_id}.xml"
        r = requests.get(url_data, timeout=10)
        data_root = ET.fromstring(r.content)

        result = {}
        mapping = {
            "temperature":    "temperatura",
            "humidity":       "umidita",
            "wind_speed":     "vento_vel",
            "wind_direction": "vento_dir",
            "rain":           "precipitazioni",
        }
        for key, tag in mapping.items():
            node = data_root.find(tag)
            if node is not None and node.text:
                try:
                    result[key] = float(node.text)
                except ValueError:
                    pass
        return result

    # =========================
    # Sky condition
    # =========================
    def _compute_sky(self, data: dict) -> str:
        """Calcola la condizione del cielo in base a pioggia e copertura nuvolosa."""
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
