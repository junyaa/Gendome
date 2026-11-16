"""Binary sensor entities for Gendome devices."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import GendomeEntity


@dataclass(frozen=True, kw_only=True)
class GendomeBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Gendome binary sensor."""

    state_key: str


BINARY_SENSORS: tuple[GendomeBinarySensorDescription, ...] = (
    GendomeBinarySensorDescription(
        key="online",
        translation_key="online",
        state_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    GendomeBinarySensorDescription(
        key="charging",
        translation_key="charging",
        state_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    GendomeBinarySensorDescription(
        key="discharging",
        translation_key="discharging",
        state_key="discharging",
    ),
    GendomeBinarySensorDescription(
        key="ac_input_enabled",
        translation_key="ac_input_enabled",
        state_key="acInputEnabled",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    GendomeBinarySensorDescription(
        key="ac_output_enabled",
        translation_key="ac_output_enabled",
        state_key="acOutputEnabled",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    GendomeBinarySensorDescription(
        key="dc_output_enabled",
        translation_key="dc_output_enabled",
        state_key="dcOutputEnabled",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    GendomeBinarySensorDescription(
        key="bypass_enabled",
        translation_key="bypass_enabled",
        state_key="bypassEnabled",
    ),
    GendomeBinarySensorDescription(
        key="ups_mode",
        translation_key="ups_mode",
        state_key="upsMode",
    ),
    GendomeBinarySensorDescription(
        key="grid_connected",
        translation_key="grid_connected",
        state_key="gridConnected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Gendome binary sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        GendomeBinarySensor(coordinator, device_id, description)
        for device_id, state in coordinator.data.devices.items()
        for description in BINARY_SENSORS
        if description.state_key in state.states or description.key == "online"
    )


class GendomeBinarySensor(GendomeEntity, BinarySensorEntity):
    """Gendome boolean state entity."""

    entity_description: GendomeBinarySensorDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(
            coordinator,
            device_id,
            description.key,
            available_when_offline=description.state_key == "online",
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the latest boolean state value."""
        state = self.device_state
        return state.boolean(self.entity_description.state_key) if state else None
