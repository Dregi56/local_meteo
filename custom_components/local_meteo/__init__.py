from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

from .coordinator import LocalMeteoCoordinator
from .const import DOMAIN

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup via configuration.yaml (non usato, ma richiesto)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup dell'integrazione tramite UI."""

    coordinator = LocalMeteoCoordinator(hass, entry)

    # Primo aggiornamento dati
    await coordinator.async_config_entry_first_refresh()

    # Salva il coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup piattaforme (sensori)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug("Local Meteo setup completato per entry %s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Rimozione integrazione."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        _LOGGER.debug("Local Meteo entry %s rimossa", entry.entry_id)

    return unload_ok
