DOMAIN = "local_meteo"

# Config keys
CONF_NAME = "name"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"

# Default values
DEFAULT_NAME = "Local Meteo"

# Update interval (secondi)
UPDATE_INTERVAL = 300  # 5 minuti

# Sensori disponibili
SENSOR_TYPES = {
    "temperature":          "Temperatura",
    "humidity":             "Umidità",
    "apparent_temperature": "Temperatura percepita",
    "dew_point":            "Punto di rugiada",
    "pressure":             "Pressione",
    "wind_speed":           "Velocità vento",
    "wind_direction":       "Direzione vento",
    "wind_gusts":           "Raffiche vento",
    "rain":                 "Pioggia",
    "rain_radar":           "Pioggia istantanea",
    "uv_index":             "Indice UV",
    "visibility":           "Visibilità",
    "cloudcover":           "Copertura nuvolosa",
    "sky":                  "Condizione cielo",
}
