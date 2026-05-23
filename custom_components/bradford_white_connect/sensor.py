"""The sensor platform for the Bradford White Connect integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bradford_white_connect_client.types import Device
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN, ENERGY_TYPE_HEAT_PUMP, ENERGY_TYPE_RESISTANCE
from .coordinator import (
    BradfordWhiteConnectEnergyCoordinator,
    BradfordWhiteConnectStatusCoordinator,
)
from .entity import (
    BradfordWhiteConnectEnergyEntity,
    BradfordWhiteConnectStatusEntity,
)
from .fault_codes import (
    DESCRIPTION_SOURCE,
    HEAT_MODE_OPTIONS,
    decode_alarm_bitmap,
    heat_mode_to_name,
)
from .helper import get_device_property_value


def _has_property(name: str) -> Callable[[Device], bool]:
    """Build a supported_fn that checks for a property's presence on the device."""
    return lambda device: name in (device.properties or {})


def _stripped(value: Any) -> Any:
    """Strip whitespace from strings; pass through other types unchanged."""
    return value.strip() if isinstance(value, str) else value


@dataclass(frozen=True, kw_only=True)
class BWSensorDescription(SensorEntityDescription):
    """Describes a BW status-coordinator sensor entity.

    Follows the aosmith / vicare HA core pattern:
    - ``value_fn`` extracts the value from a Device on each update
    - ``supported_fn`` decides whether the sensor is created for a device
    - ``extra_state_attributes_fn`` (optional) returns a dict to expose
      as the entity's ``extra_state_attributes`` (used by the alarm
      sensor to attach the raw bitmap and decoded fault list)
    """

    value_fn: Callable[[Device], Any]
    supported_fn: Callable[[Device], bool] = lambda device: True
    extra_state_attributes_fn: Callable[[Device], dict[str, Any]] | None = None


def _decode_active_alarms(device: Device) -> str:
    """Return a compact state describing which alarm bits are set.

    The bit indices are reported as hard facts; we deliberately do NOT
    put the tentative F-code descriptions in the state because the
    older RE2H50/80 mapping has been observed to disagree with newer
    personalities (e.g. ``63A`` on the RE2H65T10). Descriptions are
    surfaced as a tentative attribute instead.
    """
    bitmap = get_device_property_value(device, "alarm")
    active = decode_alarm_bitmap(bitmap)
    if not active:
        return "OK"
    return ", ".join(
        f"bit {a['bit']} (tentative {a['tentative_code']})" for a in active
    )


def _alarm_attributes(device: Device) -> dict[str, Any]:
    """Expose the raw bitmap, bit indices, and tentative descriptions."""
    bitmap = get_device_property_value(device, "alarm")
    active = decode_alarm_bitmap(bitmap)
    return {
        "raw_bitmap": bitmap,
        "active_bits": [a["bit"] for a in active],
        "tentative_codes": [a["tentative_code"] for a in active],
        "tentative_descriptions": [
            f"{a['tentative_code']}: {a['tentative_description']}"
            for a in active
        ],
        "description_source": DESCRIPTION_SOURCE,
    }


PROPERTY_SENSORS: tuple[BWSensorDescription, ...] = (
    # ----- TEMPERATURE -----
    BWSensorDescription(
        key="tank_temp",
        translation_key="tank_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(device, "tank_temp"),
        supported_fn=_has_property("tank_temp"),
    ),
    BWSensorDescription(
        key="tank_temp_lower",
        translation_key="tank_temp_lower",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(device, "tank_temp_lower"),
        supported_fn=_has_property("tank_temp_lower"),
    ),
    BWSensorDescription(
        key="ambient_temp",
        translation_key="ambient_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(
            device, "appliance_ambient_out"
        ),
        supported_fn=_has_property("appliance_ambient_out"),
    ),
    BWSensorDescription(
        key="evap_inlet_temp",
        translation_key="evap_inlet_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(device, "evap_inlet_temp"),
        supported_fn=_has_property("evap_inlet_temp"),
    ),
    BWSensorDescription(
        key="evap_outlet_temp",
        translation_key="evap_outlet_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(device, "evap_outlet_temp"),
        supported_fn=_has_property("evap_outlet_temp"),
    ),
    BWSensorDescription(
        key="comp_discharge_temp",
        translation_key="comp_discharge_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda device: get_device_property_value(
            device, "comp_discharge_temp"
        ),
        supported_fn=_has_property("comp_discharge_temp"),
    ),
    BWSensorDescription(
        key="evap_superheat",
        translation_key="evap_superheat",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "superheat_evap"),
        supported_fn=_has_property("superheat_evap"),
    ),
    # ----- SETPOINTS -----
    BWSensorDescription(
        key="water_setpoint",
        translation_key="water_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda device: get_device_property_value(device, "water_setpoint_out"),
        supported_fn=_has_property("water_setpoint_out"),
    ),
    BWSensorDescription(
        key="water_setpoint_min",
        translation_key="water_setpoint_min",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda device: get_device_property_value(device, "water_setpoint_min"),
        supported_fn=_has_property("water_setpoint_min"),
    ),
    BWSensorDescription(
        key="water_setpoint_max",
        translation_key="water_setpoint_max",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda device: get_device_property_value(device, "water_setpoint_max"),
        supported_fn=_has_property("water_setpoint_max"),
    ),
    # ----- POWER -----
    BWSensorDescription(
        key="hp_power",
        translation_key="hp_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "hp_power"),
        supported_fn=_has_property("hp_power"),
    ),
    BWSensorDescription(
        key="re_power",
        translation_key="re_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "re_power"),
        supported_fn=_has_property("re_power"),
    ),
    # ----- ELECTRICAL (diagnostic) -----
    BWSensorDescription(
        key="mains_voltage",
        translation_key="mains_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda device: get_device_property_value(device, "mains_voltage"),
        supported_fn=_has_property("mains_voltage"),
    ),
    BWSensorDescription(
        key="mains_current",
        translation_key="mains_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "mains_current"),
        supported_fn=_has_property("mains_current"),
    ),
    BWSensorDescription(
        key="hp_current",
        translation_key="hp_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "hp_current"),
        supported_fn=_has_property("hp_current"),
    ),
    BWSensorDescription(
        key="upper_element_current",
        translation_key="upper_element_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "ue_current"),
        supported_fn=_has_property("ue_current"),
    ),
    BWSensorDescription(
        key="lower_element_current",
        translation_key="lower_element_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "le_current"),
        supported_fn=_has_property("le_current"),
    ),
    # ----- DIAGNOSTIC TELEMETRY -----
    BWSensorDescription(
        key="wifi_signal_strength",
        translation_key="wifi_signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(
            device, "wifi_signal_strength"
        ),
        supported_fn=_has_property("wifi_signal_strength"),
    ),
    BWSensorDescription(
        key="filter_percentage",
        translation_key="filter_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "filter_percentage"),
        supported_fn=_has_property("filter_percentage"),
    ),
    BWSensorDescription(
        key="appliance_hours",
        translation_key="appliance_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "appliance_hours"),
        supported_fn=_has_property("appliance_hours"),
    ),
    BWSensorDescription(
        key="comp_hours",
        translation_key="comp_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "comp_hours"),
        supported_fn=_has_property("comp_hours"),
    ),
    BWSensorDescription(
        key="mode_time_remaining",
        translation_key="mode_time_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(
            device, "mode_time_remaining"
        ),
        supported_fn=_has_property("mode_time_remaining"),
    ),
    BWSensorDescription(
        key="eev_position",
        translation_key="eev_position",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "eev_pos"),
        supported_fn=_has_property("eev_pos"),
    ),
    # ----- HOT WATER CAPACITY -----
    BWSensorDescription(
        # Key is preserved from PR #61 to keep existing entity IDs stable;
        # translation_key matches HA core aosmith naming for friendlier UI display.
        key="available_thermal_capacity",
        translation_key="hot_water_availability",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: get_device_property_value(
            device, "available_thermal_capacity"
        ),
        supported_fn=_has_property("available_thermal_capacity"),
    ),
    BWSensorDescription(
        key="stored_thermal_capacity",
        translation_key="stored_thermal_capacity",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: get_device_property_value(
            device, "stored_thermal_capacity"
        ),
        supported_fn=_has_property("stored_thermal_capacity"),
    ),
    BWSensorDescription(
        key="max_thermal_capacity",
        translation_key="max_thermal_capacity",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(
            device, "max_thermal_capacity"
        ),
        supported_fn=_has_property("max_thermal_capacity"),
    ),
    # ----- ENERGY -----
    BWSensorDescription(
        key="daily_total_energy",
        translation_key="daily_total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "daily_total_energy"),
        supported_fn=_has_property("daily_total_energy"),
    ),
    BWSensorDescription(
        key="total_energy",
        translation_key="total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda device: get_device_property_value(device, "total_energy"),
        supported_fn=_has_property("total_energy"),
    ),
    # ----- TANK / APPLIANCE INFO -----
    BWSensorDescription(
        key="tank_size",
        translation_key="tank_size",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "tank_size_out"),
        supported_fn=_has_property("tank_size_out"),
    ),
    BWSensorDescription(
        key="appliance_type",
        translation_key="appliance_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "type_out"),
        supported_fn=_has_property("type_out"),
    ),
    BWSensorDescription(
        key="appliance_model",
        translation_key="appliance_model",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: _stripped(
            get_device_property_value(device, "appliance_model_out")
        ),
        supported_fn=_has_property("appliance_model_out"),
    ),
    # ----- DIAGNOSTIC TEXT / STATUS -----
    BWSensorDescription(
        key="alarm",
        translation_key="alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_decode_active_alarms,
        extra_state_attributes_fn=_alarm_attributes,
        supported_fn=_has_property("alarm"),
    ),
    BWSensorDescription(
        key="drm_status",
        translation_key="drm_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: get_device_property_value(device, "drm_status"),
        supported_fn=_has_property("drm_status"),
    ),
    BWSensorDescription(
        key="current_heat_mode",
        translation_key="current_heat_mode",
        device_class=SensorDeviceClass.ENUM,
        options=HEAT_MODE_OPTIONS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: heat_mode_to_name(
            get_device_property_value(device, "current_heat_mode")
        ),
        supported_fn=_has_property("current_heat_mode"),
    ),
    BWSensorDescription(
        key="connection_status",
        translation_key="connection_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda device: getattr(device, "connection_status", None),
        # The Device object always has this attr; create unconditionally.
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bradford White Connect sensor platform."""
    data: BradfordWhiteConnectData = hass.data[DOMAIN][entry.entry_id]

    energy_entities = [
        BradfordWhiteConnectEnergySensorEntity(
            data.energy_coordinator, dsn, device, energy_type
        )
        for dsn, device in data.status_coordinator.data.items()
        for energy_type in (ENERGY_TYPE_RESISTANCE, ENERGY_TYPE_HEAT_PUMP)
    ]

    property_entities = [
        BradfordWhiteConnectPropertySensor(data.status_coordinator, dsn, device, desc)
        for dsn, device in data.status_coordinator.data.items()
        for desc in PROPERTY_SENSORS
        if desc.supported_fn(device)
    ]

    async_add_entities([*energy_entities, *property_entities])


class BradfordWhiteConnectEnergySensorEntity(
    BradfordWhiteConnectEnergyEntity, SensorEntity
):
    """Daily energy usage sensor backed by the energy coordinator."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: BradfordWhiteConnectEnergyCoordinator,
        dsn: str,
        device: Device,
        energy_type: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self._attr_translation_key = f"{energy_type}_energy_usage"
        self._attr_unique_id = f"{energy_type}_{dsn}"
        self._device = device
        self._dsn = dsn
        self._energy_type = energy_type

    @property
    def native_value(self) -> float | None:
        """Return the daily energy usage."""
        return self.energy_usage


class BradfordWhiteConnectPropertySensor(
    BradfordWhiteConnectStatusEntity, SensorEntity
):
    """Sensor backed by a device property exposed through the status coordinator."""

    entity_description: BWSensorDescription

    def __init__(
        self,
        coordinator: BradfordWhiteConnectStatusCoordinator,
        dsn: str,
        device: Device,
        description: BWSensorDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator, dsn, device)
        self.entity_description = description
        self._attr_unique_id = f"{dsn}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the current value extracted via the description's value_fn."""
        try:
            return self.entity_description.value_fn(self.device)
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return optional extra attributes (e.g. raw bitmap on the alarm sensor)."""
        attrs_fn = self.entity_description.extra_state_attributes_fn
        if attrs_fn is None:
            return None
        try:
            return attrs_fn(self.device)
        except (AttributeError, KeyError, TypeError, ValueError):
            return None
