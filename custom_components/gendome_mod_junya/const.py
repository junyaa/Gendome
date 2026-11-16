"""Constants for the Gendome integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "gendome_mod_junya"
NAME: Final = "Gendome (Mod Junya)"
MANUFACTURER: Final = "Gendome"

PRODUCT_KEY_GO_1000: Final = "woibp7yhn3w9qqr2"
PRODUCT_KEY_GO_2000: Final = "qvwckuhm3ykiomiz"
BEIYITONG_PRODUCT_KEYS: Final = frozenset(
    {PRODUCT_KEY_GO_1000, PRODUCT_KEY_GO_2000}
)

PLATFORMS: Final = (
    "sensor",
    "binary_sensor",
    "switch",
    "number",
)

ENVIRONMENT_PROD: Final = "prod"
ENVIRONMENT: Final = ENVIRONMENT_PROD
DEFAULT_API_BASE_URL: Final = "https://api.gendome.cloud"
DEFAULT_OAUTH_BASE_URL: Final = "https://oauth.gendome.cloud"
AUTHORIZE_URL: Final = f"{DEFAULT_OAUTH_BASE_URL}/oauth/authorize"
TOKEN_URL: Final = f"{DEFAULT_OAUTH_BASE_URL}/oauth/token"
REVOKE_URL: Final = f"{DEFAULT_OAUTH_BASE_URL}/oauth/revokeToken"
OPENAPI_PREFIX: Final = "/aiot-devicecenter/openapi/home-assistant"

PUBLIC_OAUTH_CLIENT_ID: Final = "gendome_home_assistant"
PUBLIC_OAUTH_IMPLEMENTATION: Final = "gendome_public_pkce"

CONF_API_BASE_URL: Final = "api_base_url"
CONF_ENVIRONMENT: Final = "environment"
CONF_REGION: Final = "region"

OAUTH_SCOPES: Final = (
    "device:read",
    "statistics:read",
    "device:control:switch",
    "device:control:setting",
    "scheduled_charging:read",
    "scheduled_charging:write",
)
OAUTH_SCOPE: Final = " ".join(OAUTH_SCOPES)

DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=60)
MIN_SCAN_INTERVAL_SECONDS: Final = 10
MAX_SCAN_INTERVAL_SECONDS: Final = 300
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ENABLE_EVENT_LOG: Final = "enable_event_log"
DEFAULT_ENABLE_EVENT_LOG: Final = True
MAX_EVENT_LOG_ENTRIES: Final = 20
REQUEST_TIMEOUT_SECONDS: Final = 15
COMMAND_TIMEOUT_SECONDS: Final = 30
COMMAND_POLL_INTERVAL_SECONDS: Final = 2

COMMAND_SET_AC_INPUT: Final = "SET_AC_INPUT_ENABLED"
COMMAND_SET_AC_OUTPUT: Final = "SET_AC_OUTPUT_ENABLED"
COMMAND_SET_DC_OUTPUT: Final = "SET_DC_OUTPUT_ENABLED"
COMMAND_SET_BUZZER: Final = "SET_BUZZER_ENABLED"
COMMAND_SET_AC_CHARGE_POWER: Final = "SET_AC_CHARGE_POWER"
COMMAND_SET_BATTERY_RANGE: Final = "SET_BATTERY_PROTECTION_RANGE"

TERMINAL_COMMAND_STATUSES: Final = frozenset(
    {"SUCCESS", "FAILED", "TIMEOUT", "REJECTED"}
)
FAILED_COMMAND_STATUSES: Final = frozenset({"FAILED", "TIMEOUT", "REJECTED"})
