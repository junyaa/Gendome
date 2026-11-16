"""Switch entities for Gendome device controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import GendomeApiError
from .const import (
    BEIYITONG_PRODUCT_KEYS,
    COMMAND_SET_AC_INPUT,
    COMMAND_SET_AC_OUTPUT,
    COMMAND_SET_BUZZER,
    COMMAND_SET_DC_OUTPUT,
    DOMAIN,
)
from .entity import GendomeEntity


@dataclass(frozen=True, kw_only=True)
class GendomeSwitchDescription(SwitchEntityDescription):
    """Describe a Gendome switch."""

    state_key: str
    command: str
    optional: bool = False


SWITCHES: tuple[GendomeSwitchDescription, ...] = (
    GendomeSwitchDescription(
        key="ac_input",
        translation_key="ac_input",
        state_key="acInputEnabled",
        command=COMMAND_SET_AC_INPUT,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        optional=True,
    ),
    GendomeSwitchDescription(
        key="ac_output",
        translation_key="ac_output",
        state_key="acOutputEnabled",
        command=COMMAND_SET_AC_OUTPUT,
        device_class=SwitchDeviceClass.OUTLET,
    ),
    GendomeSwitchDescription(
        key="dc_output",
        translation_key="dc_output",
        state_key="dcOutputEnabled",
        command=COMMAND_SET_DC_OUTPUT,
        device_class=SwitchDeviceClass.SWITCH,
    ),
    GendomeSwitchDescription(
        key="buzzer",
        translation_key="buzzer",
        state_key="buzzerEnabled",
        command=COMMAND_SET_BUZZER,
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
        optional=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Gendome switch entities."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = []
    for device_id, state in coordinator.data.devices.items():
        for description in SWITCHES:
            if not description.optional or description.state_key in state.states:
                entities.append(GendomeSwitch(coordinator, device_id, description))
        if device_id in coordinator.data.schedules:
            entities.append(GendomeScheduledChargingSwitch(coordinator, device_id))
    async_add_entities(entities)


class GendomeSwitch(GendomeEntity, SwitchEntity):
    """Command-driven Gendome switch."""

    entity_description: GendomeSwitchDescription

    def __init__(self, coordinator, device_id: str, description) -> None:
        super().__init__(coordinator, device_id, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        return state.boolean(self.entity_description.state_key) if state else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_enabled(False)

    async def _async_set_enabled(self, enabled: bool) -> None:
        try:
            await self.coordinator.api.async_send_and_wait(
                self._device_id,
                self.entity_description.command,
                {"enabled": enabled},
            )
        except GendomeApiError as err:
            raise _control_error(err) from err
        await self.coordinator.async_request_refresh()


class GendomeScheduledChargingSwitch(GendomeEntity, SwitchEntity):
    """Enable or disable an existing scheduled charging plan."""

    _attr_translation_key = "scheduled_charging"
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id, "scheduled_charging")

    @property
    def is_on(self) -> bool | None:
        state = self.device_state
        if state is None:
            return None
        if state.device.product_key in BEIYITONG_PRODUCT_KEYS:
            enabled = state.boolean("scheduledChargingEnabled")
            if enabled is not None:
                return enabled
        schedule = self.coordinator.data.schedules.get(self._device_id)
        if not schedule:
            return None
        value = schedule.get("status", schedule.get("open"))
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        return str(value).strip().lower() in {"1", "true", "on"}

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose cached schedule details for the current device."""
        schedule = self.coordinator.data.schedules.get(self._device_id)
        if not schedule:
            return None
        attributes: dict[str, Any] = {}
        for key in (
            "startTime",
            "endTime",
            "start_time",
            "end_time",
            "power",
            "targetSoc",
            "target_soc",
            "days",
            "repeat",
            "mode",
            "timezone",
        ):
            if key in schedule and schedule[key] is not None:
                attributes[key] = schedule[key]
        return attributes or dict(schedule)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_set_enabled(False)

    async def _async_set_enabled(self, enabled: bool) -> None:
        try:
            schedule = await self.coordinator.api.async_set_charging_schedule_enabled(
                self._device_id, enabled
            )
        except GendomeApiError as err:
            raise _control_error(err) from err
        self.coordinator.async_set_schedule(self._device_id, dict(schedule))
        state = self.device_state
        if state is not None and state.device.product_key in BEIYITONG_PRODUCT_KEYS:
            await self.coordinator.async_request_refresh()


def _control_error(err: GendomeApiError) -> HomeAssistantError:
    return HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="command_failed",
        translation_placeholders={"message": str(err)},
    )
