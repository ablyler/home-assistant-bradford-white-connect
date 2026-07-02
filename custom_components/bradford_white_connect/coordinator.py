"""The data update coordinator for the Bradford White Connect integration."""

from __future__ import annotations

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

# Properties worth warning about when the cloud returns obviously bad data.
# These checks are diagnostic only. We still keep the device in coordinator
# data so HA entities remain available and can surface whatever values the
# cloud did return.
_REQUIRED_TEMP_PROPERTIES: tuple[str, ...] = (
    "tank_temp",
    "water_setpoint_out",
    "water_setpoint_min",
    "water_setpoint_max",
)


def _coerce_float(value: Any) -> float | None:
    """Parse telemetry that may arrive as number-like strings."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    """Parse integer-like telemetry values safely."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class BradfordWhiteConnectStatusCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """Coordinator for device status, updating with a frequent interval."""

    def __init__(self, hass: HomeAssistant, client: BradfordWhiteConnectClient) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=REGULAR_INTERVAL)
        self.client = client
        self.shared_data: dict[str, Any] = {}

    async def async_set_property(
        self, device: Device, name: str, value: Any
    ) -> None:
        """Write a single property's datapoint to the Ayla cloud.

        The upstream ``bradford_white_connect_client`` only exposes
        ``set_device_heat_mode`` and ``update_device_set_point``; this
        helper performs the same POST for any property by name, which
        lets us drive things like ``set_vacation_mode_days``,
        ``controller_reboot``, and ``heater_name`` via the same
        Mobile-app codepath.

        Booleans are submitted as ``1`` / ``0``; everything else is
        passed through unchanged. We deliberately do **not** optimistically
        mutate ``device.properties[name].value`` after a successful write,
        because the Ayla cloud is the source of truth: the next coordinator
        refresh (shortened to ``FAST_INTERVAL`` for the next ~5 minutes
        via ``last_api_set_datetime``) will reconcile state.
        """
        await self._post_datapoint(device, name, value)
        self.shared_data["last_api_set_datetime"] = datetime.datetime.now(
            datetime.timezone.utc
        )
        await self.async_request_refresh()

    async def _post_datapoint(self, device: Device, name: str, value: Any) -> None:
        """POST a single datapoint to the Ayla cloud via the upstream client.

        Going through ``self.client.http_post_request`` (rather than calling
        ``aiohttp`` directly) inherits the upstream client's retry-on-401
        re-authentication behaviour.
        """
        headers = self.client.generate_headers(
            {
                "content-type": "application/json",
                "x-ayla-source": "Mobile",
            }
        )
        url = _DATAPOINT_URL.format(dsn=device.dsn, name=name)
        payload_value: Any = (1 if value else 0) if isinstance(value, bool) else value
        data = json.dumps({"datapoint": {"value": payload_value}})
        _LOGGER.info("Writing %s=%r to device %s", name, payload_value, device.dsn)
        await self.client.http_post_request(url, headers=headers, data=data)

    def _refresh_update_interval(self) -> None:
        """Shorten the polling interval after a recent write, otherwise relax it."""
        last_set = self.shared_data.get("last_api_set_datetime")
        if last_set is None:
            self.update_interval = REGULAR_INTERVAL
            return
        if (
            datetime.datetime.now(datetime.timezone.utc) - last_set
        ) < REGULAR_INTERVAL:
            _LOGGER.debug("Setting fast update interval")
            self.update_interval = FAST_INTERVAL
        else:
            _LOGGER.debug("Setting regular update interval")
            self.update_interval = REGULAR_INTERVAL

    @staticmethod
    def _log_device_warnings(device: Device) -> None:
        """Log suspicious telemetry without dropping the device from HA."""
        for temp_property in _REQUIRED_TEMP_PROPERTIES:
            device_property = device.properties.get(temp_property)
            if device_property is None:
                _LOGGER.warning(
                    "Device %s missing expected property %s",
                    device.dsn,
                    temp_property,
                )
                continue
            raw_value = device_property.value
            value = _coerce_float(raw_value)
            if value is None or value < 0 or value > 200:
                _LOGGER.warning(
                    "Device %s property %s out of range: %r",
                    device.dsn,
                    temp_property,
                    raw_value,
                )

        heat_mode = device.properties.get("current_heat_mode")
        if heat_mode is None:
            _LOGGER.warning(
                "Device %s missing expected property current_heat_mode",
                device.dsn,
            )
            return
        raw_mode = heat_mode.value
        mode = _coerce_int(raw_mode)
        if raw_mode is not None and mode is None:
            _LOGGER.warning(
                "Device %s reported non-integer current_heat_mode %r",
                device.dsn,
                raw_mode,
            )
        elif mode is not None and not BradfordWhiteConnectHeatingModes.is_valid(mode):
            _LOGGER.warning(
                "Device %s reported unknown current_heat_mode %r",
                device.dsn,
                raw_mode,
            )

    async def _async_update_data(self) -> dict[str, Device]:
        """Fetch latest data from the device status endpoint."""
        self._refresh_update_interval()
        try:
            devices = await self.client.get_devices()
            valid_devices: dict[str, Device] = {}
            for device in devices:
                properties = await self.client.get_device_properties(device)
                device.properties = {p.property.name: p.property for p in properties}
                self._log_device_warnings(device)
                valid_devices[device.dsn] = device
            return valid_devices
        except BradfordWhiteConnectAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BradfordWhiteConnectUnknownException as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class BradfordWhiteConnectEnergyCoordinator(
    DataUpdateCoordinator[dict[str, dict[str, float]]]
):
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

    async def _async_update_data(self) -> dict[str, dict[str, float]]:
        """Fetch latest data from the energy usage endpoint."""
        energy_usage_by_dsn: dict[str, dict[str, float]] = {}

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
