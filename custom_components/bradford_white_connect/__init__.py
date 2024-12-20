"""The Bradford White Connect integration."""

from __future__ import annotations

from dataclasses import dataclass

from bradford_white_connect_client import BradfordWhiteConnectClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, device_registry as dr

from .const import DOMAIN
from .coordinator import (
    BradfordWhiteConnectEnergyCoordinator,
    BradfordWhiteConnectStatusCoordinator,
)
from .helper import get_device_property_value

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WATER_HEATER]


@dataclass
class BradfordWhiteConnectData:
    """Data for the Bradford White Connect integration."""

    client: BradfordWhiteConnectClient
    status_coordinator: BradfordWhiteConnectStatusCoordinator
    energy_coordinator: BradfordWhiteConnectEnergyCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bradford White Connect from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    session = aiohttp_client.async_get_clientsession(hass)
    client = BradfordWhiteConnectClient(email, password, session)
    await client.authenticate()

    status_coordinator = BradfordWhiteConnectStatusCoordinator(hass, client)
    energy_corodinator = BradfordWhiteConnectEnergyCoordinator(hass, client)
    await status_coordinator.async_config_entry_first_refresh()
    await energy_corodinator.async_config_entry_first_refresh()

    device_registry = dr.async_get(hass)
    for dsn, device in status_coordinator.data.items():
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, dsn)},
            manufacturer="Bradford White",
            name=get_device_property_value(device, "product_name"),
            model=get_device_property_value(device, "appliance_model_out"),
            serial_number=get_device_property_value(
                device, "appliance_serial_number_out"
            ),
            sw_version=get_device_property_value(device, "controller_sw"),
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = BradfordWhiteConnectData(
        client, status_coordinator, energy_corodinator
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
