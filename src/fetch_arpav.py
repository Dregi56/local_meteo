import requests
import xml.etree.ElementTree as ET

def fetch_arpav(lat, lon):
    url_stazioni = "https://tele.arpav.it/meteoidro/xml/stazioni.xml"
    r = requests.get(url_stazioni)
    root = ET.fromstring(r.content)
    closest_station = None
    min_dist = float("inf")
    for stazione in root.findall("stazione"):
        st_lat = float(stazione.find("latitudine").text)
        st_lon = float(stazione.find("longitudine").text)
        dist = (lat-st_lat)**2 + (lon-st_lon)**2
        if dist < min_dist:
            min_dist = dist
            closest_station = stazione
    st_id = closest_station.find("id").text
    url_data = f"https://tele.arpav.it/meteoidro/xml/{st_id}.xml"
    r = requests.get(url_data)
    data_root = ET.fromstring(r.content)
    temperature = float(data_root.find("temperatura").text)
    humidity = float(data_root.find("umidita").text)
    wind_speed = float(data_root.find("vento_vel").text)
    wind_dir = float(data_root.find("vento_dir").text)
    rain = float(data_root.find("precipitazioni").text)
    return {
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "rain": rain
    }
