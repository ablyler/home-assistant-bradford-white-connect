"""The Bradford White Connect integration."""

from __future__ import annotations

from dataclasses import dataclass

from bradford_white_connect_client import BradfordWhiteConnectClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    aiohttp_client,
    device_registry as dr,
    entity_registry as er,
)

from .const import DOMAIN
from .coordinator import (
    BradfordWhiteConnectEnergyCoordinator,
    BradfordWhiteConnectStatusCoordinator,
)
from .helper import get_device_property_value

REMOVED_BUTTON_SUFFIXES: tuple[str, ...] = (
    "_clear_alarm_counts",
    "_reset_filter",
)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.WATER_HEATER,
]


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
    energy_coordinator = BradfordWhiteConnectEnergyCoordinator(hass, client)
    await status_coordinator.async_config_entry_first_refresh()
    await energy_coordinator.async_config_entry_first_refresh()

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
        client, status_coordinator, energy_coordinator
    )

    _async_cleanup_removed_buttons(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def _async_cleanup_removed_buttons(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Delete entity-registry rows for buttons that were removed in 0.5.0.

    Without this, users who upgrade from 0.4.x see permanent ``unavailable``
    entries for ``button.*_clear_alarm_counts`` and ``button.*_reset_filter``
    until they delete them manually. We only touch entities owned by this
    config entry and whose ``unique_id`` matches the well-known suffixes.
    """
    entity_reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_reg, entry.entry_id)
    for entity in entries:
        if entity.unique_id.endswith(REMOVED_BUTTON_SUFFIXES):
            entity_reg.async_remove(entity.entity_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
