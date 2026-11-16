# Gendome (Mod Junya) for Home Assistant

> **Unofficial mod/fork.** This repository is a community-modified fork of the upstream
> [gendome/home-assistant](https://github.com/gendome/home-assistant) integration.
> It is **not affiliated with or endorsed by Gendome**. Original copyright and
> the [MIT License](LICENSE) are preserved.

This mod (`custom_components/gendome_mod_junya`, domain `gendome_mod_junya`) can
be installed alongside the original `gendome` integration as a separate
integration in Home Assistant.

## What changed vs upstream

Compared to upstream
[gendome/home-assistant](https://github.com/gendome/home-assistant) (1.0.x):

### Identity and coexistence
- Separate integration domain/folder: `gendome_mod_junya` / **Gendome (Mod Junya)** (does not replace or migrate the original `gendome` integration).
- Fork metadata, docs, and mod branding updated; manifest/loggers/version aligned to this mod.

### Added
- **Options flow:** configurable polling interval (10–300 s, default 60 s) and optional transient state event logging.
- **Diagnostics for brief power events:** diagnostics export includes options, effective poll interval, and recent redacted per-device state changes (`recent_state_changes` with timestamps and `raw_keys`) when event logging is enabled.
- **Extra tracked transition keys (when reported):** `acInputEnabled`, `acChargePowerSetting`, battery protection bounds, `bypassEnabled`, `upsMode`, `gridConnected`, `workMode`, plus power/charging/SOC/error/temperature keys.
- **Optional read-only binary sensors (only if API reports keys):** AC input enabled, AC output state, DC output state, bypass mode, UPS mode, grid-connected.
- **Diagnostic sensors (when available):** firmware version, Wi-Fi version, MCU version, last update timestamp, error code.
- **Optional sensors (when available):** battery temperature, device temperature.
- **Scheduled charging:** entity is created only when schedule data is available and exposes cached schedule attributes.
- **Dashboard example:** [`docs/dashboard.md`](docs/dashboard.md) with a ready-to-adapt Lovelace layout for energy/power/status views.

### Changed / improved
- **UI/graph metadata:** remaining time uses duration device class (numeric minutes) with localized display text in attributes; online sensor uses connectivity device class; power/battery/temperature sensors use measurement state and display precision where appropriate for history/statistics.
- **Icons:** expanded and state/range-aware icon mappings (`icons.json`) for battery level, connectivity/charging/discharging states, input/output/bypass/UPS/grid, and controls.
- **Entity categories/classes:** config and diagnostic categories applied where relevant; switch device classes refined.
- **Wind input power:** disabled by default to reduce clutter on devices without wind input.
- **Maintenance:** encoding/mojibake cleanup in modules, docs, translations, and tests; packaging/CI fixes for hassfest/HACS/ruff/pytest compatibility.

### Not changed (vs upstream behavior)
- **No new device write commands.** Existing controls keep validation, non-optimistic command handling, and offline-availability safeguards.
- Cloud OAuth/device control flow and supported write operations remain the same in scope.

### Safety and limitations
- Cloud polling cannot guarantee capture of very short (1–2 s) events if the cloud/device does not report intermediate states between polls; local AC monitoring may be required for root-cause analysis.
- Optional bypass/UPS/grid/temperature/error entities appear only if the Gendome cloud API exposes those keys.
- Running original and mod against the same account increases API polling load; consider increasing the update interval if needed.

## Supported entities

| Platform | Entities |
| --- | --- |
| Sensor | Battery SOC, remaining time (charge/discharge, duration), input/AC/solar/output/AC output/DC output power, AC charge power setting |
| Optional sensor | Wind input power (disabled by default), battery temperature, device temperature, error code (diagnostic) |
| Diagnostic sensor | Firmware version, Wi-Fi version, MCU version, last update timestamp (when available) |
| Binary sensor | Online (connectivity), charging, discharging |
| Optional binary sensor | AC input enabled, AC/DC output state, bypass mode, UPS mode, grid-connected state (when reported by the device) |
| Switch | AC output, DC output |
| Optional/config switch | AC input, buzzer (created only when the API exposes the corresponding state), scheduled charging (created only when schedule data is available; config) |
| Number (config) | AC charge power limit, battery protection lower SOC, battery protection upper SOC |

Entities use `mac + entity_key` as their stable unique ID. Controls are not
optimistic: the integration waits for the Java OpenAPI command result and then
refreshes the coordinated device state.

## Automatic synchronization

Device data syncs automatically about every **60 seconds**.
No refresh automation is needed.

## Connecting your account

1. Download **Gendome** in HACS, then restart Home Assistant service.
2. Open **Settings → Devices & services → Add integration → Gendome**.
3. Home Assistant opens the Gendome authorization website in the browser.
4. Sign in with your Gendome App account, review the requested permissions, and
   select **Allow**.
5. Gendome redirects the browser back to Home Assistant. The integration then
   discovers the devices already bound to that Gendome account.

## User prerequisites

- Home Assistant 2024.8 or newer;
- HACS installed and working;
- a Gendome App account with at least one supported device already bound;
- internet access from the browser and Home Assistant server to Gendome cloud
  services.

To use the **Scheduled charging** switch, first create a charging plan in the
Gendome app. The integration can read and enable or disable an existing plan,
but cannot create or edit the plan in Home Assistant. Cached schedule details
(start/end, target, mode, etc.) are exposed as switch attributes when provided.

## Production backend prerequisites

The Gendome backend must provide the endpoints documented in
[`docs/openapi-contract.md`](docs/openapi-contract.md), and a public OAuth client
with:

- client ID `gendome_home_assistant` and no client secret;
- grant types `authorization_code` and `refresh_token`;
- mandatory PKCE using `S256` for the authorization-code flow;
- the fixed `https://my.home-assistant.io/redirect/oauth` redirect URI;
- read scopes `device:read`, `statistics:read`, and
  `scheduled_charging:read`;
- control scopes `device:control:switch`,
  `device:control:setting`, and `scheduled_charging:write`.

The public client ID is safe to ship in the integration. It must never have a
client secret because every HACS installation can inspect the source code.

## Download and add with HACS

Add the repository to HACS and download the integration:

1. In HACS, open **Integrations**, then **Custom repositories**.
2. Add your fork URL (or `https://github.com/gendome/home-assistant.git` for
   upstream) with category **Integration**.
3. Find and download **Gendome**, then restart Home Assistant service.
4. Open **Settings → Devices & services → Add integration → Gendome** and
   complete the browser authorization flow.

If Gendome is available in the default HACS catalog, search for **Gendome**
directly and download it without adding a custom repository.

Adding the integration immediately opens the Gendome website. Sign in, review
the requested access, and select **Allow**. Gendome then returns to Home
Assistant, which creates the config entry and loads the account's devices.
Users do not create OAuth credentials and do not see an implementation picker.
The Gendome password is entered only on the Gendome-owned authorization page;
it is not entered into or stored by Home Assistant.

This HACS flow uses Gendome's built-in public OAuth client with Authorization
Code + PKCE; it does not depend on Nabu Casa Cloud Account Linking.

For a manual installation, copy `custom_components/gendome` into the Home
Assistant `config/custom_components` directory and restart Home Assistant.

## Safety behavior

- Device commands use a new idempotency key and poll `commandId` for a terminal
  result.
- Offline devices are unavailable for control; the Online binary sensor remains
  available so it can report `off`.
- Battery protection requires `0 ≤ lower SOC < upper SOC ≤ 100` both in Home
  Assistant and on the backend.
- AC charging power limits vary by model. GO1000 supports 60–1000 W and
  GO2000 supports 60–1500 W, both in 1 W increments.
- On GO1000 and GO2000, the battery protection lower limit is 0–30% and the
  upper limit is 50–100%. Both can be set in steps of 1 percentage point.
- Turning off AC or DC output can immediately interrupt connected loads.

## Diagnostics and troubleshooting

Download diagnostics from the Gendome integration page. Tokens, email, IP,
serial number, MAC, and device IDs are redacted or masked. Diagnostics can also
include integration options and (when enabled) a recent log of observed
state/raw-key changes between cloud polls to help investigate brief
transitions (e.g. short grid loss causing output flicker).

Integration options (Settings → Devices & services → Gendome → Configure):
- **Update interval (seconds)**: polling period (10–300, default 60). Shorter
  intervals may capture more transient changes but increase API load/rate-limit risk.
- **Enable transient state event log**: keeps a small in-memory ring of recent
  per-device changes for diagnostics export.

Important limitation: very short events (1–2 s) can still be missed if the cloud
does not report intermediate states between polls. In that case, local power
quality monitoring on the AC input/output side may be required for definitive
root-cause analysis.

See [`docs/troubleshooting.md`](docs/troubleshooting.md) for common failures.

## Current limitations

- The integration is distributed through HACS and is not bundled with Home
  Assistant Core.
- Full scheduled-charging rule editing is intentionally excluded; only an
  existing plan can be read and enabled/disabled.
- Buzzer support stays hidden until the backend returns its semantic state.
- Storm, TOU, self-consumption, reserve SOC, forced discharge, factory reset,
  UPS protection changes, and OTA are not exposed.
- The remaining-time sensor shows an estimate in minutes. Its label changes
  between **Charge remaining time** and **Discharge remaining time**. On
  GO1000 and GO2000, it follows the mode reported by the device when available.
- Product capabilities are inferred from semantic state keys until the backend
  adds an explicit capability object.

## License

MIT License. See [LICENSE](LICENSE). Original copyright and permission notice
are preserved.
