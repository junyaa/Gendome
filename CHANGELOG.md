# Changelog

All notable changes to **Gendome (Mod Junya)** (gendome_mod_junya) are documented here.
Upstream project: [gendome/home-assistant](https://github.com/gendome/home-assistant). MIT License preserved.

## 1.1.0-mod (2026-11-16)

Compared to upstream 1.0.x:

### Added
- Separate integration identity for coexistence: domain/folder gendome_mod_junya, display name **Gendome (Mod Junya)** (no migration from original gendome).
- Integration options: configurable polling interval (10–300 s, default 60 s) and optional transient state event logging.
- Diagnostics export: effective options, poll interval, and recent redacted per-device state changes (
ecent_state_changes, timestamps, changed 
aw_keys) for brief power/grid investigations.
- Event log tracking for additional keys when reported: cInputEnabled, cChargePowerSetting, battery protection bounds, ypassEnabled, upsMode, gridConnected, workMode (plus power/charging/SOC/error/temperature keys).
- Optional read-only binary sensors when reported by API: AC input enabled, AC output state, DC output state, bypass mode, UPS mode, grid-connected.
- Diagnostic sensors when available: firmware version, Wi-Fi version, MCU version, last update timestamp, error code.
- Optional sensors when available: battery temperature, device temperature.
- Scheduled charging entity created only when schedule data is available; cached schedule details exposed as attributes.
- Dashboard example: docs/dashboard.md.

### Changed
- Remaining time sensor: duration device class, numeric minute value, measurement state, localized display text in attributes.
- Online binary sensor: connectivity device class.
- Power/battery/temperature sensors: measurement state and display precision where appropriate for history/statistics.
- Switches: appropriate device classes; config categories for relevant toggles.
- Wind input power sensor: disabled by default.
- Icons: expanded, state- and range-aware mappings in icons.json.

### Fixed / maintenance
- Encoding/mojibake cleanup in integration modules, docs, translations, and tests.
- Packaging/CI fixes for hassfest, HACS, ruff, and pytest compatibility in this fork.
- Tests updated for renamed domain/package and diagnostics/options behavior.

### Documentation
- README, troubleshooting, and OpenAPI contract notes updated to reflect mod identity, coexistence, options/diagnostics, entities, and limitations.

### Safety / notes
- No new device write commands added. Existing control validation, command result polling, and offline availability safeguards remain in place.
- Optional entities appear only when corresponding state keys are provided by the cloud API. Short events (1–2 s) may be missed if not reported between polls.

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
