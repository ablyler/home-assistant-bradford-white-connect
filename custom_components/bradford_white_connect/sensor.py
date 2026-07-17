"""The sensor platform for the Bradford White Connect integration."""

from dataclasses import dataclass
from typing import Any, Callable

from bradford_white_connect_client.types import Device
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BradfordWhiteConnectData
from .const import DOMAIN, ENERGY_TYPE_HEAT_PUMP, ENERGY_TYPE_RESISTANCE
from .coordinator import BradfordWhiteConnectEnergyCoordinator, BradfordWhiteConnectStatusCoordinator
from .entity import BradfordWhiteConnectEnergyEntity, BradfordWhiteConnectStatusEntity


@dataclass(frozen=True, kw_only=True)
class BWSensorDescription(SensorEntityDescription):
    """Describes a BW property exposed as a sensor."""

    property_name: str
    value_fn: Callable[[Any], Any] | None = None


PROPERTY_SENSORS: tuple[BWSensorDescription, ...] = (
    # ----- TEMPERATURE -----
    BWSensorDescription(
        key="tank_temp_lower",
        property_name="tank_temp_lower",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    BWSensorDescription(
        key="ambient_temp",
        property_name="appliance_ambient_out",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    BWSensorDescription(
        key="evap_inlet_temp",
        property_name="evap_inlet_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    BWSensorDescription(
        key="evap_outlet_temp",
        property_name="evap_outlet_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    BWSensorDescription(
        key="comp_discharge_temp",
        property_name="comp_discharge_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
    ),
    # ----- POWER -----
    BWSensorDescription(
        key="hp_power",
        property_name="hp_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    BWSensorDescription(
        key="re_power",
        property_name="re_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    # ----- ELECTRICAL -----
    BWSensorDescription(
        key="mains_voltage",
        property_name="mains_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
    ),
    BWSensorDescription(
        key="mains_current",
        property_name="mains_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
    ),
    BWSensorDescription(
        key="hp_current",
        property_name="hp_current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
    ),
    # ----- DIAGNOSTIC TELEMETRY -----
    BWSensorDescription(
        key="wifi_signal_strength",
        property_name="wifi_signal_strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BWSensorDescription(
        key="filter_percentage",
        property_name="filter_percentage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BWSensorDescription(
        key="appliance_hours",
        property_name="appliance_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BWSensorDescription(
        key="comp_hours",
        property_name="comp_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ----- HOT WATER CAPACITY -----
    BWSensorDescription(
        key="available_thermal_capacity",
        property_name="available_thermal_capacity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BWSensorDescription(
        key="stored_thermal_capacity",
        property_name="stored_thermal_capacity",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ----- DAILY TOTAL ENERGY -----
    BWSensorDescription(
        key="daily_total_energy",
        property_name="daily_total_energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
    ),
    # ----- DIAGNOSTIC TEXT -----
    BWSensorDescription(
        key="alarm",
        property_name="alarm",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BWSensorDescription(
        key="drm_status",
        property_name="drm_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
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
        if desc.property_name in (device.properties or {})
    ]

    async_add_entities(energy_entities + property_entities)


class BradfordWhiteConnectEnergySensorEntity(
    BradfordWhiteConnectEnergyEntity, SensorEntity
):
    """Class for the energy sensor entity."""

    _attr_translation_key = "energy_usage"
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
        energy_type_title = " ".join(energy_type.split("_")).title()
        # has_entity_name=True is on base class — let HA prepend device name.
        self._attr_name = f"{energy_type_title} Energy Usage"
        self._attr_unique_id = f"{energy_type}_{dsn}"
        self._device = device
        self._dsn = dsn
        self._energy_type = energy_type

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.energy_usage


class BradfordWhiteConnectPropertySensor(
    BradfordWhiteConnectStatusEntity, SensorEntity
):
    """Sensor for any device property exposed by the status coordinator."""

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
        # has_entity_name=True is set on base class — HA will prepend the device
        # name automatically, so just supply the suffix here.
        self._attr_name = description.key.replace("_", " ").title()

    @property
    def native_value(self) -> Any:
        """Return the current value of the property."""
        prop = self.device.properties.get(self.entity_description.property_name)
        if prop is None:
            return None
        val = getattr(prop, "value", None)
        if val is None:
            return None
        if self.entity_description.value_fn:
            try:
                val = self.entity_description.value_fn(val)
            except Exception:  # noqa: BLE001
                return None
        return val
