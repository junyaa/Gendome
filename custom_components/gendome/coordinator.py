"""Coordinator for Gendome device data."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import replace
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import (
    GendomeApiClient,
    GendomeApiError,
    GendomeAuthError,
    GendomePermissionError,
    GendomeRateLimitError,
)
from .const import (
    CONF_ENABLE_EVENT_LOG,
    CONF_SCAN_INTERVAL,
    DEFAULT_ENABLE_EVENT_LOG,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_EVENT_LOG_ENTRIES,
)
from .models import GendomeCoordinatorData, GendomeDevice, GendomeDeviceState

_LOGGER = logging.getLogger(__name__)

_TRACKED_STATE_KEYS = (
    "online",
    "acInputEnabled",
    "acOutputEnabled",
    "dcOutputEnabled",
    "charging",
    "discharging",
    "batterySoc",
    "acInputPower",
    "inputTotalPower",
    "outputTotalPower",
    "acOutputPower",
    "dcOutputPower",
    "acChargePowerSetting",
    "batteryProtectionLowerSoc",
    "batteryProtectionUpperSoc",
    "bypassEnabled",
    "upsMode",
    "gridConnected",
    "workMode",
    "errorCode",
    "batteryTemperature",
    "temperature",
)


class GendomeDataUpdateCoordinator(DataUpdateCoordinator[GendomeCoordinatorData]):
    """Fetch account devices and semantic states in coordinated polls."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: GendomeApiClient,
    ) -> None:
        scan_seconds = entry.options.get(
            CONF_SCAN_INTERVAL, int(DEFAULT_SCAN_INTERVAL.total_seconds())
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(scan_seconds)),
            always_update=False,
        )
        self.api = api
        self._profile = None
        self._schedules: dict[str, dict[str, Any]] = {}
        self._event_logs: dict[str, deque[dict[str, Any]]] = {}
        self._last_snapshots: dict[str, dict[str, Any]] = {}

    @property
    def event_log_enabled(self) -> bool:
        """Return whether transient state change logging is enabled."""
        if self.config_entry is None:
            return DEFAULT_ENABLE_EVENT_LOG
        return bool(
            self.config_entry.options.get(
                CONF_ENABLE_EVENT_LOG, DEFAULT_ENABLE_EVENT_LOG
            )
        )

    def async_get_event_log(self, device_id: str) -> list[dict[str, Any]]:
        """Return recent tracked state changes for a device."""
        return list(self._event_logs.get(device_id, []))

    async def _async_setup(self) -> None:
        """Load account metadata and initial charging schedules once."""
        try:
            self._profile = await self.api.async_get_profile()
            devices = await self.api.async_get_devices()
        except GendomeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GendomeApiError as err:
            raise UpdateFailed(str(err)) from err

        schedule_results = await asyncio.gather(
            *(self._async_get_schedule(device) for device in devices)
        )
        self._schedules = {
            device_id: schedule
            for device_id, schedule in schedule_results
            if schedule is not None
        }

    async def _async_get_schedule(
        self, device: GendomeDevice
    ) -> tuple[str, dict[str, Any] | None]:
        try:
            schedule = await self.api.async_get_charging_schedule(device.device_id)
            return device.device_id, dict(schedule)
        except (GendomePermissionError, GendomeApiError):
            _LOGGER.debug(
                "Charging schedule is unavailable for device %s", device.device_id
            )
            return device.device_id, None

    async def _async_update_data(self) -> GendomeCoordinatorData:
        """Fetch device discovery metadata and semantic states."""
        try:
            devices = await self.api.async_get_devices()
            device_map = {device.device_id: device for device in devices}
            states = await self.api.async_get_states(device_map)
        except GendomeAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except GendomeRateLimitError as err:
            raise UpdateFailed(str(err)) from err
        except GendomeApiError as err:
            raise UpdateFailed(str(err)) from err

        for device in devices:
            if device.device_id not in states:
                offline_device = replace(device, online=False)
                states[device.device_id] = GendomeDeviceState(
                    device=offline_device,
                    states={"online": False},
                )

        self._update_event_logs(states)

        if self._profile is None:
            raise UpdateFailed("Gendome profile was not initialized")
        return GendomeCoordinatorData(
            profile=self._profile,
            devices=states,
            schedules=self._schedules,
        )

    def _update_event_logs(self, states: dict[str, GendomeDeviceState]) -> None:
        """Record tracked state transitions to help diagnose brief power events."""
        if not self.event_log_enabled:
            return
        now = dt_util.utcnow().isoformat()
        for device_id, state in states.items():
            snapshot = self._build_snapshot(state)
            previous = self._last_snapshots.get(device_id)
            self._last_snapshots[device_id] = snapshot
            if previous is None:
                continue
            changes = {
                key: {"from": previous.get(key), "to": value}
                for key, value in snapshot.items()
                if previous.get(key) != value
            }
            if not changes:
                continue
            log = self._event_logs.setdefault(
                device_id, deque(maxlen=MAX_EVENT_LOG_ENTRIES)
            )
            log.appendleft(
                {
                    "time": now,
                    "update_time": state.update_time,
                    "changes": changes,
                }
            )
            _LOGGER.debug(
                "Gendome state changes for %s: %s", device_id, changes
            )

    @staticmethod
    def _build_snapshot(state: GendomeDeviceState) -> dict[str, Any]:
        snapshot = {key: state.states.get(key) for key in _TRACKED_STATE_KEYS}
        snapshot["raw_keys"] = sorted(state.raw_properties.keys())
        return snapshot

    def async_set_schedule(self, device_id: str, schedule: dict[str, Any]) -> None:
        """Update cached schedule for a device after a successful control request."""
        self._schedules = {**self._schedules, device_id: dict(schedule)}
        if self.data is not None:
            self.async_set_updated_data(
                replace(self.data, schedules=dict(self._schedules))
            )
