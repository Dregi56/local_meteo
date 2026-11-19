"""Client per i dati aperti ARPAV (Veneto)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from math import asin, cos, radians, sin, sqrt

import aiohttp

BASE_URL = "https://meteo.arpa.veneto.it/meteo/dati_meteo/xml/"
STATIONS_URL = BASE_URL + "stazioni.xml"
STATION_TYPES = ("METEO", "AGRO")
TIMEOUT = aiohttp.ClientTimeout(total=15)

# Codice <TYPE> del sensore ARPAV -> chiave interna dell'integrazione.
# Verificato solo TEMP: gli altri codici vanno aggiunti dopo aver letto
# quelli reali della stazione (vedi comando in fondo alla risposta).
SENSOR_MAP = {
    "TEMP": "temperature",
}


def distance_km(lat1, lon1, lat2, lon2) -> float:
    """Distanza in km tra due punti (formula di Haversine)."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


async def _get_xml(session: aiohttp.ClientSession, url: str) -> ET.Element:
    async with session.get(url, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        content = await resp.read()
    return ET.fromstring(content)


async def async_get_stations(session) -> list[dict]:
    """Elenco delle stazioni ARPAV con coordinate e file dei dati."""
    root = await _get_xml(session, STATIONS_URL)
    stations = []
    for s in root.findall("STAZIONE"):
        try:
            stations.append(
                {
                    "id": s.findtext("IDSTAZ").strip(),
                    "name": (s.findtext("NOME") or "").strip(),
                    "comune": (s.findtext("COMUNE") or "").strip().title(),
                    "type": (s.findtext("TIPOSTAZ") or "").strip(),
                    "lon": float(s.findtext("X")),
                    "lat": float(s.findtext("Y")),
                    "link": s.findtext("LINKSTAZ").strip(),
                }
            )
        except (AttributeError, TypeError, ValueError):
            continue
    return stations


def nearest_stations(stations, lat, lon, limit=8) -> list[dict]:
    """Le stazioni più vicine, con la distanza in km."""
    candidates = [
        dict(s, distance_km=distance_km(lat, lon, s["lat"], s["lon"]))
        for s in stations
        if s["type"] in STATION_TYPES
    ]
    candidates.sort(key=lambda s: s["distance_km"])
    return candidates[:limit]


async def async_get_station_data(session, link: str) -> dict:
    """Ultimo valore disponibile per ogni sensore noto della stazione."""
    root = await _get_xml(session, BASE_URL + link)
    station = root.find("STAZIONE")
    result: dict = {}
    if station is None:
        return result

    for sensor in station.findall("SENSORE"):
        key = SENSOR_MAP.get((sensor.findtext("TYPE") or "").strip())
        if key is None:
            continue
        latest = None  # (istante, valore)
        for dati in sensor.findall("DATI"):
            try:
                value = float(dati.findtext("VM"))
            except (TypeError, ValueError):
                continue
            instant = dati.get("ISTANTE", "")
            if latest is None or instant > latest[0]:
                latest = (instant, value)
        if latest is not None:
            result[key] = latest[1]
    return result
