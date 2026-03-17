import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE


DOMAIN = "local_meteo"


class LocalMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow Local Meteo con valori default da HA."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Step iniziale: input latitudine e longitudine da UI."""
        errors = {}

        # Valori default: se esistono in Home Assistant
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude

        if user_input is not None:
            lat = user_input[CONF_LATITUDE]
            lon = user_input[CONF_LONGITUDE]
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors["base"] = "invalid_coordinates"
            else:
                return self.async_create_entry(
                    title="Local Meteo",
                    data=user_input,
                )

        # Form UI con valori default da Home Assistant
        data_schema = vol.Schema(
            {
                vol.Required(CONF_LATITUDE, default=default_lat): float,
                vol.Required(CONF_LONGITUDE, default=default_lon): float,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
