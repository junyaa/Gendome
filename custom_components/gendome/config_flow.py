"""OAuth2 config flow for Gendome."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, OptionsFlow, SOURCE_REAUTH
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    GendomeApiClient,
    GendomeApiError,
    GendomeAuthError,
    GendomeConnectionError,
)
from .const import (
    CONF_API_BASE_URL,
    CONF_ENABLE_EVENT_LOG,
    CONF_ENVIRONMENT,
    CONF_REGION,
    CONF_SCAN_INTERVAL,
    DEFAULT_API_BASE_URL,
    DEFAULT_ENABLE_EVENT_LOG,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENVIRONMENT,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
    OAUTH_SCOPE,
)
from .oauth import create_public_oauth2_implementation

_LOGGER = logging.getLogger(__name__)


class _BearerRequester:
    """Lightweight requester used only to validate a new OAuth token."""

    def __init__(self, hass: HomeAssistant, access_token: str) -> None:
        self._session = async_get_clientsession(hass)
        self._access_token = access_token

    async def async_request(self, method: str, url: str, **kwargs: Any):
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self._access_token}"
        headers.setdefault("Accept", "application/json")
        return await self._session.request(method, url, headers=headers, **kwargs)


class GendomeConfigFlow(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle the Gendome OAuth2 config flow."""

    VERSION = 1
    MINOR_VERSION = 1
    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return the logger used by the OAuth2 config flow."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Request only the scopes actually used by the integration."""
        return {"scope": OAUTH_SCOPE}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Start the public PKCE flow without an implementation picker."""
        return await self._async_start_public_oauth()

    async def _async_start_public_oauth(self) -> FlowResult:
        """Start a flow-scoped public PKCE authorization."""
        # Use a fresh verifier for every authorization flow. The implementation
        # is selected directly, so locally stored credentials cannot make the
        # normal HACS setup show an implementation selection screen.
        self.flow_impl = create_public_oauth2_implementation(self.hass)
        return await self.async_step_auth()

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> FlowResult:
        """Start reauthentication for a revoked or expired token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user to confirm reauthentication."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=vol.Schema({})
            )

        return await self._async_start_public_oauth()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Validate the authorization result and create or update an entry."""
        token = data.get("token") or {}
        access_token = token.get("access_token")
        if not access_token:
            return self.async_abort(reason="invalid_auth")

        api = GendomeApiClient(
            _BearerRequester(self.hass, str(access_token)), DEFAULT_API_BASE_URL
        )
        try:
            profile = await api.async_get_profile()
        except GendomeAuthError as err:
            _LOGGER.warning(
                "Gendome profile authentication failed: code=%s message=%s",
                err.code,
                err,
            )
            return self.async_abort(reason="invalid_auth")
        except GendomeConnectionError as err:
            _LOGGER.warning("Unable to connect to Gendome profile endpoint: %s", err)
            return self.async_abort(reason="cannot_connect")
        except GendomeApiError as err:
            details = api.last_error or {}
            _LOGGER.error(
                "Gendome profile request failed: code=%s endpoint=%s message=%s",
                details.get("code") or err.code,
                details.get("endpoint") or "profile",
                details.get("message") or str(err),
            )
            return self.async_abort(reason="unknown")

        region = profile.region.upper()
        entry_data = {
            **data,
            CONF_ENVIRONMENT: ENVIRONMENT,
            CONF_REGION: region,
            CONF_API_BASE_URL: DEFAULT_API_BASE_URL,
        }
        await self.async_set_unique_id(f"{region}:{profile.user_id}")
        title = profile.username or profile.email or f"Gendome {profile.user_id}"

        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=entry_data
            )

        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=title, data=entry_data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return GendomeOptionsFlow(config_entry)


class GendomeOptionsFlow(OptionsFlow):
    """Handle Gendome options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(
                            CONF_SCAN_INTERVAL,
                            int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_SECONDS,
                            max=MAX_SCAN_INTERVAL_SECONDS,
                        ),
                    ),
                    vol.Required(
                        CONF_ENABLE_EVENT_LOG,
                        default=options.get(
                            CONF_ENABLE_EVENT_LOG, DEFAULT_ENABLE_EVENT_LOG
                        ),
                    ): bool,
                }
            ),
        )
