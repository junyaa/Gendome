"""The Gendome Home Assistant integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .const import (
    CARD_JS_URL,
    CARD_STATIC_PATH,
    CONF_API_BASE_URL,
    CONF_ENVIRONMENT,
    DEFAULT_API_BASE_URL,
    DOMAIN,
    ENVIRONMENT,
    PLATFORMS,
    REVOKE_URL,
)

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

    from .api import GendomeApiClient
    from .coordinator import GendomeDataUpdateCoordinator


@dataclass(slots=True)
class GendomeRuntimeData:
    """Runtime objects for a config entry."""

    api: GendomeApiClient
    coordinator: GendomeDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gendome from an OAuth2 config entry."""
    from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
    from homeassistant.helpers import config_entry_oauth2_flow

    from .api import GendomeApiClient
    from .coordinator import GendomeDataUpdateCoordinator
    from .oauth import async_get_entry_oauth2_implementation

    stored_environment = entry.data.get(CONF_ENVIRONMENT)
    if stored_environment and stored_environment != ENVIRONMENT:
        raise ConfigEntryError(
            "This Gendome entry is not a production entry. Remove it and add "
            "Gendome again to connect to the production service."
        )

    try:
        implementation = await async_get_entry_oauth2_implementation(hass, entry)
    except config_entry_oauth2_flow.ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            "The Gendome OAuth implementation is temporarily unavailable"
        ) from err
    oauth_session = config_entry_oauth2_flow.OAuth2Session(
        hass, entry, implementation
    )
    api = GendomeApiClient(
        oauth_session,
        str(entry.data.get(CONF_API_BASE_URL, DEFAULT_API_BASE_URL)),
    )
    coordinator = GendomeDataUpdateCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = GendomeRuntimeData(api=api, coordinator=coordinator)
    await _async_register_frontend(hass)
    _async_remove_legacy_refresh_buttons(hass, entry)
    if hasattr(entry, "async_on_unload") and hasattr(entry, "add_update_listener"):
        entry.async_on_unload(entry.add_update_listener(_async_update_options))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the Lovelace custom card for this integration."""
    if hass.data.setdefault(DOMAIN, {}).get("_frontend_registered"):
        return

    from pathlib import Path

    frontend_dir = str(Path(__file__).parent / "frontend")
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_STATIC_PATH, frontend_dir, cache_headers=False)]
        )
    except Exception:
        try:
            hass.http.register_static_path(CARD_STATIC_PATH, frontend_dir, False)
        except Exception:
            _LOGGER.debug(
                "Unable to register Gendome frontend static path",
                exc_info=True,
            )
            return

    hass.data[DOMAIN]["_frontend_registered"] = True

    lovelace = hass.data.get("lovelace")
    resources = getattr(lovelace, "resources", None) if lovelace else None
    if resources is None:
        return
    try:
        if not getattr(resources, "loaded", True):
            await resources.async_load()
        for item in resources.async_items() or []:
            if item.get("url") == CARD_JS_URL:
                return
        await resources.async_create_item({"res_type": "module", "url": CARD_JS_URL})
    except Exception:
        _LOGGER.debug(
            "Unable to auto-register Gendome Lovelace resource",
            exc_info=True,
        )


async def _async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_remove_legacy_refresh_buttons(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Remove retired refresh buttons belonging to this config entry."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if (
            entity.domain == "button"
            and entity.platform == DOMAIN
            and entity.unique_id.endswith("_refresh_state")
        ):
            registry.async_remove(entity.entity_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Gendome config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Revoke the Gendome token when the config entry is removed."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    token = entry.data.get("token") or {}
    access_token = token.get("access_token")
    if not access_token:
        return

    try:
        response = await async_get_clientsession(hass).post(
            REVOKE_URL,
            data={"token": access_token},
        )
        if response.status >= 400:
            _LOGGER.warning(
                "Unable to revoke Gendome authorization while removing entry: %s",
                response.status,
            )
    except Exception:
        _LOGGER.warning(
            "Unable to contact Gendome while revoking the removed entry",
            exc_info=True,
        )
