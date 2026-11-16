# Changelog

All notable changes to this **mod/fork** are documented here.
Upstream project: [gendome/home-assistant](https://github.com/gendome/home-assistant). MIT License preserved.

## 1.1.0-mod (2026-11-16)

### Added
- Integration options: configurable polling interval (10–300 s, default 60 s) and transient state event logging.
- Diagnostics export: effective options, poll interval, and recent redacted per-device state changes (`recent_state_changes`, timestamps, changed `raw_keys`) to help investigate brief grid/power transitions.
- Event log tracking for grid/bypass-related keys when reported: `acInputEnabled`, `acChargePowerSetting`, battery protection bounds, `bypassEnabled`, `upsMode`, `gridConnected`, `workMode` (plus existing power/charging/SOC/error/temperature keys).
- Optional read-only binary sensors when reported by API: AC input enabled, AC output state, DC output state, bypass mode, UPS mode, grid-connected.
- Diagnostic sensors when available: firmware version, Wi-Fi version, MCU version, last update timestamp, error code.
- Optional sensors when available: battery temperature, device temperature.
- Scheduled charging switch exposes cached schedule attributes when schedule data is available.

### Changed
- Remaining time sensor: duration device class, numeric minute value, measurement state, localized display text in attributes.
- Online binary sensor: connectivity device class.
- Power and battery sensors: measurement state and integer display precision where appropriate.
- Switches: appropriate device classes; config categories for relevant toggles; scheduled charging entity created only when schedule data exists.
- Wind input power sensor: disabled by default.
- Entity icons expanded/standardized; config/diagnostic entity categories applied.

### Fixed / maintenance
- Cleaned mojibake/encoding issues in integration modules, docs, translations, and tests (no intended behavior changes).

### Documentation
- README, troubleshooting, and OpenAPI contract notes updated for fork/mod status, current entities, diagnostics/options, and limitations (including brief 1–2 s events and bypass/grid visibility).

### Safety / notes
- No new device write commands added. Existing control validation, command result polling, and offline availability safeguards remain in place.
- Optional entities appear only when corresponding state keys are provided by the cloud API. Short events may be missed if not reported between polls.

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
