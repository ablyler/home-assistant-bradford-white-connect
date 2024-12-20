"""The water heater platform for the Bradford White Connect integration."""

from datetime import datetime
import logging
from typing import Any

from bradford_white_connect_client.constants import BradfordWhiteConnectHeatingModes
from bradford_white_connect_client.helper import BradfordWhiteConnectHelper
from bradford_white_connect_client.types import Device
from homeassistant.components.water_heater import (
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_HEAT_PUMP,
    STATE_HIGH_DEMAND,
    STATE_OFF,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN
from .coordinator import BradfordWhiteConnectStatusCoordinator
from .entity import BradfordWhiteConnectStatusEntity

MODE_HA_TO_BRADFORDWHITE = {
    STATE_ECO: BradfordWhiteConnectHeatingModes.HYBRID,
    STATE_ELECTRIC: BradfordWhiteConnectHeatingModes.ELECTRIC,
    STATE_HEAT_PUMP: BradfordWhiteConnectHeatingModes.HEAT_PUMP,
    STATE_HIGH_DEMAND: BradfordWhiteConnectHeatingModes.HYBRID_PLUS,
    STATE_OFF: BradfordWhiteConnectHeatingModes.VACATION,
}
MODE_BRADFORDWHITE_TO_HA = {
    BradfordWhiteConnectHeatingModes.ELECTRIC: STATE_ELECTRIC,
    BradfordWhiteConnectHeatingModes.HEAT_PUMP: STATE_HEAT_PUMP,
    BradfordWhiteConnectHeatingModes.HYBRID_PLUS: STATE_HIGH_DEMAND,
    BradfordWhiteConnectHeatingModes.HYBRID: STATE_ECO,
    BradfordWhiteConnectHeatingModes.VACATION: STATE_OFF,
}

# Priority list for operation mode to use when exiting away mode
# Will use the first mode that is supported by the device
DEFAULT_OPERATION_MODE_PRIORITY = [
    BradfordWhiteConnectHeatingModes.HEAT_PUMP,
    BradfordWhiteConnectHeatingModes.HYBRID,
    BradfordWhiteConnectHeatingModes.ELECTRIC,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Bradford White Connect water heater platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]

    # Add water heater entities for each device
    async_add_entities(
        BradfordWhiteConnectWaterHeaterEntity(data.status_coordinator, dsn, device)
        for dsn, device in data.status_coordinator.data.items()
    )


class BradfordWhiteConnectWaterHeaterEntity(
    BradfordWhiteConnectStatusEntity, WaterHeaterEntity
):
    """The water heater entity for the Bradford White Connect integration."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self._attr_unique_id = dsn
        self._device = device

    @property
    def operation_list(self) -> list[str]:
        """Return the list of supported operation modes."""

        # Get the appliance model for the device
        appliance_model = self.device.properties.get(
            "appliance_model_out"
        ).value.strip()

        # Get the heating modes for the appliance model
        appliance_heating_modes = (
            BradfordWhiteConnectHelper.get_appliance_model_heating_modes(
                appliance_model
            )
        )

        # Translate the bradford white heating modes to HA modes
        ha_modes = [
            MODE_BRADFORDWHITE_TO_HA.get(mode)
            for mode in appliance_heating_modes
            if MODE_BRADFORDWHITE_TO_HA.get(mode)
        ]
        return ha_modes

    @property
    def supported_features(self) -> WaterHeaterEntityFeature:
        """Return the list of supported features."""
        support_flags = WaterHeaterEntityFeature.TARGET_TEMPERATURE

        # Operation mode only supported if there is more than one mode
        if len(self.operation_list) > 1:
            support_flags |= WaterHeaterEntityFeature.OPERATION_MODE

        support_flags |= WaterHeaterEntityFeature.AWAY_MODE

        return support_flags

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        tank_temp = self.device.properties.get("tank_temp")
        return tank_temp.value if tank_temp else None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        water_setpoint_out = self.device.properties.get("water_setpoint_out")
        return water_setpoint_out.value if water_setpoint_out else None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        water_setpoint_min = self.device.properties.get("water_setpoint_min")
        return water_setpoint_min.value if water_setpoint_min else None

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        water_setpoint_max = self.device.properties.get("water_setpoint_max")
        return water_setpoint_max.value if water_setpoint_max else None

    @property
    def current_operation(self) -> str:
        """Return the current operation mode."""
        current_heat_mode = self.device.properties.get("current_heat_mode")
        if current_heat_mode:
            return MODE_BRADFORDWHITE_TO_HA.get(
                self.device.properties["current_heat_mode"].value, STATE_OFF
            )
        else:
            return STATE_OFF

    @property
    def is_away_mode_on(self):
        """Return True if away mode is on."""
        current_heat_mode = self.device.properties.get("current_heat_mode")
        if current_heat_mode:
            return (
                self.device.properties["current_heat_mode"].value
                == BradfordWhiteConnectHeatingModes.VACATION
            )
        else:
            return False

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        """Set new target operation mode."""
        if operation_mode not in self.operation_list:
            raise HomeAssistantError("Operation mode not supported")

        vendor_mode = MODE_HA_TO_BRADFORDWHITE.get(operation_mode)
        if vendor_mode is not None:
            _LOGGER.info("Setting operation mode to %s", operation_mode)
            await self.client.set_device_heat_mode(self.device, vendor_mode)
            self.coordinator.shared_data["last_api_set_datetime"] = datetime.now()
            await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is not None:
            _LOGGER.info("Setting temperature to %s", temperature)
            await self.client.update_device_set_point(self.device, temperature)
            self.coordinator.shared_data["last_api_set_datetime"] = datetime.now()
            await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_on(self) -> None:
        """Turn away mode on."""
        _LOGGER.info("Setting away mode on")
        await self.client.set_device_heat_mode(
            self.device, BradfordWhiteConnectHeatingModes.VACATION
        )
        self.coordinator.shared_data["last_api_set_datetime"] = datetime.now()
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_off(self) -> None:
        """Turn away mode off."""
        for mode in DEFAULT_OPERATION_MODE_PRIORITY:
            _LOGGER.info("Setting away mode off, trying mode: %s", mode)
            await self.client.set_device_heat_mode(self.device, mode)
            self.coordinator.shared_data["last_api_set_datetime"] = datetime.now()
            await self.coordinator.async_request_refresh()
            break
