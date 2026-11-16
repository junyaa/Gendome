# Changelog

## Unreleased

- Improved Home Assistant UI representation:
  - Remaining time sensor now uses duration device class with numeric minute values and localized display text in attributes.
  - Added diagnostic sensors for firmware, Wi-Fi, MCU versions, last update timestamp, and error code when available.
  - Added optional temperature sensors (battery/device) when reported by the device.
  - Online binary sensor now uses connectivity device class.
  - Added optional output-state binary sensors (AC/DC output) when reported by the device.
  - Expanded and standardized entity icons.
  - Power and battery sensors now report measurement state with integer display precision.
  - AC/DC output and control switches now expose appropriate switch device classes.
  - Scheduled charging switch is created only when schedule data is available and exposes cached schedule attributes.
  - Wind input power sensor is disabled by default to reduce clutter when unsupported.
  - Configuration controls (charge limit, battery protection, input/buzzer/schedule toggles) are categorized as config entities.
- Diagnostics and troubleshooting for brief power events:
  - Added integration options for polling interval and transient state event logging.
  - Diagnostics export now includes options, effective poll interval, and recent redacted state-change events per device (when enabled).
  - Event log tracks additional keys relevant to grid/bypass behavior when reported (`acInputEnabled`, `acChargePowerSetting`, battery protection bounds, `bypassEnabled`, `upsMode`, `gridConnected`, `workMode`).
  - Added optional binary sensors for AC input enabled, bypass mode, UPS mode, and grid-connected state when the API reports them.
- Documentation and maintenance:
  - Updated README/troubleshooting/OpenAPI notes for fork and current entity behavior.
  - Cleaned mojibake/encoding issues in integration modules, docs, translations, and tests (logic unchanged).
  - MIT License preserved (`LICENSE` unchanged).

## 1.0.1 - 2026-11-10

- Fully redact account identifiers and omit API request URLs and error messages
  from exported diagnostics.
- Mark entities as unavailable when a device is removed from the account.
- Use the plain Online entity name without a sorting prefix.

## 1.0.0 - 2026-10-14

- Added browser-based OAuth2 account linking with Authorization Code and S256
  PKCE, automatic token refresh, reauthentication, and authorization revocation.
- Added Gendome Home 3000 and Go series device discovery.
- Added coordinated battery, remaining-time, power, connectivity, charging, and
  firmware entities.
- Added AC input, AC output, DC output, charge-power, battery-protection, and
  scheduled-charging controls.
- Added command idempotency, final-result polling, manual refresh, error mapping,
  and privacy-safe diagnostics.
- Added HACS metadata, brand assets, translations, automated validation, user
  documentation, and troubleshooting guidance.
