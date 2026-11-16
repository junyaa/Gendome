# Troubleshooting

## Authorization expired or revoked (401)

Home Assistant starts a reauthentication flow. Open the Gendome integration,
choose **Reconfigure**, and sign in again. If reauthentication loops, confirm
the OAuth redirect URI and refresh-token policy on the backend.

## Missing permission (403)

Authorize the scope required by the entity:

- device state: `device:read`, `statistics:read`;
- AC/DC/buzzer switches: `device:control:switch`;
- power and battery settings: `device:control:setting`;
- schedule state/control: `scheduled_charging:read` and
  `scheduled_charging:write`.

## Rate limited (429)

The coordinator honors the backend `Retry-After` response. Avoid automations
that repeatedly write the same switch or number. The backend should also apply
token, device-command cooldown, and HA-instance limits.

## Device is unavailable

Check the Online binary sensor and the Gendome App. Other entities become
unavailable when the backend reports the device offline. Confirm that the
device belongs to the authorized App user and supports the requested state key.

## Command timeout or failure

The integration polls the returned `commandId` for up to 30 seconds. Export
diagnostics and correlate its masked identifier and error code with
`iot_home_assistant_command`. Check cloud-to-device delivery, device online
state, and whether the expected property was reported.

## State differs from the App

Wait for the next automatic sync (based on the configured update interval) or
reload the integration, then compare the batched `/devices/states` response with
the App. Confirm data-point mappings and units, especially charge/discharge
remaining time, charging/discharging, and firmware fields.

## Brief grid/power events (output drops for 1–2 seconds)

If loads briefly turn off and on during a grid transition but the app shows no
error, the cloud API may not report intermediate states between polls.

Recommended steps:

1. Open **Settings → Devices & services → Gendome → Configure** and temporarily
   lower **Update interval** (e.g. 10–15 seconds). This increases the chance of
   catching a state transition but may increase API load.
2. Keep **Enable transient state event log** enabled.
3. Reproduce the event, then download diagnostics immediately. Check
   `recent_state_changes` for the device (online, AC input/output, power,
   raw key changes, timestamps).
4. Compare with physical symptoms and, if possible, a local power monitor on the
   AC input/output lines. If available, also watch `ac_input_enabled`,
   `grid_connected`, `bypass_enabled`/`ups_mode` binary sensors and power/charging
   trends around 100%↔99% SOC.

## Grid present but bypass/UPS pass-through stops at 100% SOC

Some stations may switch behavior when SOC reaches 100% after a brief grid loss
and resume bypass/charging behavior after dropping to 99%. This can be a device
firmware/control policy rather than a Home Assistant issue.

Use diagnostics/event logs to correlate:
- `acInputPower` / `inputTotalPower` (is grid input still detected?)
- `acInputEnabled` and `gridConnected` (if reported)
- `charging`, `discharging`, `batterySoc`, `outputTotalPower`/`acOutputPower`
- `bypassEnabled`, `upsMode`, `workMode` (if reported)
- `errorCode` and `update_time`

If the API reports stable grid input and no bypass/UPS state keys (or no change)
while behavior changes, the required telemetry may not be exposed by cloud/API.
Collect timestamps, firmware versions, diagnostics export, and contact Gendome
support; this cannot be safely "fixed" from the integration side without an
official command/state from the backend.
