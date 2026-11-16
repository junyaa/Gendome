"""Sensor entities for Gendome energy devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .duration import (
    duration_minutes,
    format_duration_minutes,
    remaining_time_name,
)
from .entity import GendomeEntity
from .models import GendomeDeviceState


@dataclass(frozen=True, kw_only=True)
class GendomeSensorEntityDescription(SensorEntityDescription):
    """Describe a Gendome sensor."""

    state_key: str | None = None
    value_fn: Callable[[GendomeDeviceState], Any] | None = None
    required: bool = True
    format_duration: bool = False


SENSORS: tuple[GendomeSensorEntityDescription, ...] = (
    GendomeSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        state_key="batterySoc",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="remaining_time",
        translation_key="remaining_time",
        state_key="remainingTime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        format_duration=True,
    ),
    GendomeSensorEntityDescription(
        key="input_total_power",
        translation_key="input_total_power",
        state_key="inputTotalPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="ac_input_power",
        translation_key="ac_input_power",
        state_key="acInputPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="solar_input_power",
        translation_key="solar_input_power",
        state_key="solarInputPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="wind_input_power",
        translation_key="wind_input_power",
        state_key="windInputPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="output_total_power",
        translation_key="output_total_power",
        state_key="outputTotalPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="ac_output_power",
        translation_key="ac_output_power",
        state_key="acOutputPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="dc_output_power",
        translation_key="dc_output_power",
        state_key="dcOutputPower",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="ac_charge_power_setting",
        translation_key="ac_charge_power_setting",
        state_key="acChargePowerSetting",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    GendomeSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        value_fn=lambda state: state.device.software_version,
        entity_category=EntityCategory.DIAGNOSTIC,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="wifi_version",
        translation_key="wifi_version",
        value_fn=lambda state: state.device.wifi_version,
        entity_category=EntityCategory.DIAGNOSTIC,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="mcu_version",
        translation_key="mcu_version",
        value_fn=lambda state: state.device.mcu_version,
        entity_category=EntityCategory.DIAGNOSTIC,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="last_update",
        translation_key="last_update",
        value_fn=lambda state: state.update_time,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        state_key="batteryTemperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="device_temperature",
        translation_key="device_temperature",
        state_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        required=False,
    ),
    GendomeSensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        state_key="errorCode",
        entity_category=EntityCategory.DIAGNOSTIC,
        required=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Gendome sensors."""
    coordinator = entry.runtime_data.coordinator
    entity_registry = er.async_get(hass)
    entities = []
    for device_id, state in coordinator.data.devices.items():
        normalized_mac = "".join(
            char for char in state.device.mac.lower() if char.isalnum()
        )
        for legacy_key in (
            "charge_remaining_time",
            "discharge_remaining_time",
            "firmware_version",
        ):
            legacy_entity_id = entity_registry.async_get_entity_id(
                "sensor", DOMAIN, f"{normalized_mac}_{legacy_key}"
            )
            if legacy_entity_id is not None:
                entity_registry.async_remove(legacy_entity_id)
        for description in SENSORS:
            if description.required:
                entities.append(_create_sensor(coordinator, device_id, description))
                continue
            if description.value_fn is not None:
                if description.value_fn(state) is not None:
                    entities.append(_create_sensor(coordinator, device_id, description))
                continue
            if description.state_key and description.state_key in state.states:
                entities.append(_create_sensor(coordinator, device_id, description))
    async_add_entities(entities)


def _create_sensor(
    coordinator: Any, device_id: str, description: GendomeSensorEntityDescription
) -> GendomeSensor:
    """Create the appropriate sensor entity."""
    if description.key == "remaining_time":
        return GendomeRemainingTimeSensor(coordinator, device_id, description)
    return GendomeSensor(coordinator, device_id, description)


class GendomeSensor(GendomeEntity, SensorEntity):
    """Read-only Gendome state value."""

    entity_description: GendomeSensorEntityDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the latest state value from the coordinator."""
        state = self.device_state
        if state is None:
            return None
        if self.entity_description.value_fn is not None:
            value = self.entity_description.value_fn(state)
            if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
                if isinstance(value, str):
                    return dt_util.parse_datetime(value)
                if isinstance(value, datetime):
                    return value
            return value
        if self.entity_description.state_key is None:
            return None
        value = state.value(self.entity_description.state_key)
        if self.entity_description.format_duration:
            return duration_minutes(value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose display text and raw minutes for duration sensors."""
        state = self.device_state
        if not self.entity_description.format_duration or state is None:
            return None
        minutes = duration_minutes(state.value(self.entity_description.state_key))
        if minutes is None:
            return None
        return {
            "minutes": minutes,
            "display": format_duration_minutes(
                minutes,
                self.coordinator.hass.config.language,
            ),
        }


class GendomeRemainingTimeSensor(GendomeSensor):
    """Remaining-time sensor with a dynamic name based on charging state."""

    @property
    def name(self) -> str:
        """Use charge remaining time while charging, otherwise discharge."""
        state = self.device_state
        charging = None
        if state is not None:
            charging = state.boolean("remainingTimeCharging")
            if charging is None:
                charging = state.boolean("charging")
        return remaining_time_name(
            charging,
            self.coordinator.hass.config.language,
        )
