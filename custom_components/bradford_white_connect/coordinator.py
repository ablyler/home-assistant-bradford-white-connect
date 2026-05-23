"""The data update coordinator for the Bradford White Connect integration."""

import datetime
import json
import logging
from typing import Any

from bradford_white_connect_client import (
    BradfordWhiteConnectAuthenticationError,
    BradfordWhiteConnectClient,
    BradfordWhiteConnectUnknownException,
)
from bradford_white_connect_client.constants import BradfordWhiteConnectHeatingModes
from bradford_white_connect_client.types import Device
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    ENERGY_TYPE_HEAT_PUMP,
    ENERGY_TYPE_RESISTANCE,
    ENERGY_USAGE_INTERVAL,
    FAST_INTERVAL,
    REGULAR_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Ayla datapoint write endpoint (same shape the upstream client uses for
# the two specialised setters - we just parametrise the property name).
_DATAPOINT_URL = (
    "https://ads-field.aylanetworks.com/apiv1/dsns/{dsn}/properties/{name}/datapoints.json"
)


class BradfordWhiteConnectStatusCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Coordinator for device status, updating with a frequent interval."""

    def __init__(self, hass: HomeAssistant, client: BradfordWhiteConnectClient) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=REGULAR_INTERVAL)
        self.client = client
        self.shared_data = {}

    async def async_set_property(
        self, device: Device, name: str, value: Any
    ) -> None:
        """Write a single property's datapoint to the Ayla cloud.

        The upstream ``bradford_white_connect_client`` only exposes
        ``set_device_heat_mode`` and ``update_device_set_point``; this
        helper performs the same POST for any property by name, which
        lets us drive ``clear_alarm_counts``, ``reset_filter``,
        ``set_vacation_mode_days`` etc. via the same Mobile-app codepath.

        Booleans are submitted as ``1`` / ``0``; everything else is
        passed through unchanged. The Ayla API echoes the stored value
        back; we don't optimistically mutate ``device.properties`` because
        the next coordinator refresh will reconcile state with the device.
        """
        headers = self.client.generate_headers(
            {
                "content-type": "application/json",
                "x-ayla-source": "Mobile",
            }
        )
        url = _DATAPOINT_URL.format(dsn=device.dsn, name=name)
        if isinstance(value, bool):
            payload_value: Any = 1 if value else 0
        else:
            payload_value = value
        data = json.dumps({"datapoint": {"value": payload_value}})
        _LOGGER.debug("POST %s value=%r", url, payload_value)
        await self.client.http_post_request(url, headers=headers, data=data)
        # Shorten the polling interval so the user sees feedback sooner.
        self.shared_data["last_api_set_datetime"] = datetime.datetime.now()
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch latest data from the device status endpoint."""
        try:
            devices = await self.client.get_devices()
            for device in devices:
                # check if the last api set call (datatime) is less than REGULAR_INTERVAL
                if self.shared_data.get("last_api_set_datetime") is not None:
                    if (
                        datetime.datetime.now()
                        - self.shared_data.get("last_api_set_datetime")
                    ) < REGULAR_INTERVAL:
                        _LOGGER.debug("Setting fast update interval")
                        self.update_interval = FAST_INTERVAL
                    else:
                        _LOGGER.debug("Setting regular update interval")
                        self.update_interval = REGULAR_INTERVAL

                properties = await self.client.get_device_properties(device)

                remapped_properties = {p.property.name: p.property for p in properties}
                device.properties = remapped_properties

                temp_properties = [
                    "tank_temp",
                    "water_setpoint_out",
                    "water_setpoint_min",
                    "water_setpoint_max",
                ]

                for temp_property in temp_properties:
                    """Validate the temp property is valid"""
                    device_property = device.properties.get(temp_property)
                    if device_property is None:
                        raise UpdateFailed(
                            f"Device property {temp_property} is missing"
                        )

                    if device_property.value < 0 or device_property.value > 200:
                        raise UpdateFailed(
                            f"Device property {temp_property} is invalid: {device_property.value}"
                        )

                """Validate the current heat mode is valid"""
                device_property = device.properties.get("current_heat_mode")
                if device_property is None:
                    raise UpdateFailed("Device property 'current_heat_mode' is missing")

                if not BradfordWhiteConnectHeatingModes.is_valid(device_property.value):
                    raise UpdateFailed(
                        f"Device property 'current_heat_mode' is invalid: {device_property.value}"
                    )

            return {device.dsn: device for device in devices}
        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class BradfordWhiteConnectEnergyCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator for energy usage data, updating with a slower interval."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BradfordWhiteConnectClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=ENERGY_USAGE_INTERVAL
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, map]:
        """Fetch latest data from the energy usage endpoint."""
        energy_usage_by_dsn: dict[str, map] = {}

        # always get the energy usage the current date with a lag of one hour
        # this is to ensure we get the usage for the last hour of the day that
        # can come in after midnight
        usage_date = datetime.datetime.now() - datetime.timedelta(hours=1)

        try:
            devices = await self.client.get_devices()

            for device in devices:

                heatpump_energy = await self.client.get_total_energy_usage_for_day(
                    device, "hp", usage_date
                )
                resistance_energy = await self.client.get_total_energy_usage_for_day(
                    device, "re", usage_date
                )

                energy_usage_by_dsn[device.dsn] = {
                    ENERGY_TYPE_HEAT_PUMP: heatpump_energy,
                    ENERGY_TYPE_RESISTANCE: resistance_energy,
                }

        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return energy_usage_by_dsn
