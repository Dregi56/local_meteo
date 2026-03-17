from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_TYPES


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensori."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        LocalMeteoSensor(coordinator, entry, sensor_type)
        for sensor_type in SENSOR_TYPES
    ]
    async_add_entities(sensors)


class LocalMeteoSensor(CoordinatorEntity, SensorEntity):
    """Sensore generico Local Meteo."""

    def __init__(self, coordinator, entry, sensor_type):
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = f"{entry.data.get('name', 'Local Meteo')} {SENSOR_TYPES[sensor_type]}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"

    @property
    def device_info(self):
        """Info dispositivo."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.data.get("name", "Local Meteo"),
            manufacturer="Local Meteo",
            model="Multi-source weather",
        )

    @property
    def native_value(self):
        """Valore del sensore."""
        data = self.coordinator.data or {}
        return data.get(self._sensor_type)

    @property
    def unit_of_measurement(self):
        """Unità di misura."""
        units = {
            "temperature":          "°C",
            "humidity":             "%",
            "apparent_temperature": "°C",
            "dew_point":            "°C",
            "pressure":             "hPa",
            "wind_speed":           "km/h",
            "wind_direction":       "°",
            "wind_gusts":           "km/h",
            "rain":                 "mm",
            "rain_radar":           "mm/h",
            "uv_index":             "UV",
            "visibility":           "m",
            "cloudcover":           "%",
        }
        return units.get(self._sensor_type)

    @property
    def icon(self):
        """Icona sensore."""
        icons = {
            "temperature":          "mdi:thermometer",
            "humidity":             "mdi:water-percent",
            "apparent_temperature": "mdi:thermometer-lines",
            "dew_point":            "mdi:thermometer-water",
            "pressure":             "mdi:gauge",
            "wind_speed":           "mdi:weather-windy",
            "wind_direction":       "mdi:compass",
            "wind_gusts":           "mdi:weather-windy-variant",
            "rain":                 "mdi:weather-rainy",
            "rain_radar":           "mdi:radar",
            "uv_index":             "mdi:sun-wireless",
            "visibility":           "mdi:eye",
            "cloudcover":           "mdi:cloud",
            "sky":                  "mdi:weather-partly-cloudy",
        }
        return icons.get(self._sensor_type)
