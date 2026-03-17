import yaml
from fetch_dpc import fetch_dpc
from fetch_arpav import fetch_arpav
from process_data import sky_condition
from publish_homeassistant import publish_mqtt

with open("../config/config.yaml") as f:
    cfg = yaml.safe_load(f)

lat = cfg["location"]["latitude"]
lon = cfg["location"]["longitude"]
name = cfg["location"]["name"]

sri = fetch_dpc(lat, lon) if cfg["services"].get("dpc", True) else 0
arpav_data = fetch_arpav(lat, lon) if cfg["services"].get("arpav", True) else {
    "temperature": None, "humidity": None, "wind_speed": None, "wind_dir": None, "rain": 0
}

cielo = sky_condition(sri, arpav_data["temperature"], arpav_data["rain"])

sensor_data = {
    "sky": cielo,
    "temperature": arpav_data["temperature"],
    "humidity": arpav_data["humidity"],
    "wind_speed": arpav_data["wind_speed"],
    "wind_dir": arpav_data["wind_dir"],
    "rain_instant": arpav_data["rain"]
}

topic = f"{cfg['mqtt']['topic_prefix']}/{name}/meteo"
publish_mqtt(cfg['mqtt']['broker'], topic, str(sensor_data),
             username=cfg['mqtt'].get("username"),
             password=cfg['mqtt'].get("password"))

print(sensor_data)
