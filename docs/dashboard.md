# Gendome (Mod Junya) dashboard example

Home Assistant dashboards are configured in Lovelace (UI), not by the
integration itself. This example uses built-in cards and the entities exposed by
**Gendome (Mod Junya)** (`gendome_mod_junya`) to show energy, power, status, and
controls.

## How to use

1. Open **Settings → Dashboards → Add dashboard** (or edit an existing one).
2. Add a view with **Sections** (or Grid) layout.
3. Replace every `ENTITY_ID_*` placeholder below with your actual entity IDs from
   **Developer tools → States** (filter by `gendome_mod_junya` or your device).
4. Remove cards for entities that are not available on your device (optional
   sensors/binary sensors are created only when the API reports them).

## Example (YAML)

```yaml
title: Gendome
views:
  - title: Power station
    type: sections
    sections:
      - type: grid
        cards:
          - type: gauge
            entity: ENTITY_ID_SENSOR_BATTERY_SOC
            name: Battery
            min: 0
            max: 100
            severity:
              green: 50
              yellow: 20
              red: 10
          - type: entities
            title: Status
            show_header_toggle: false
            entities:
              - entity: ENTITY_ID_BINARY_SENSOR_ONLINE
                name: Online
              - entity: ENTITY_ID_BINARY_SENSOR_CHARGING
                name: Charging
              - entity: ENTITY_ID_BINARY_SENSOR_DISCHARGING
                name: Discharging
              - entity: ENTITY_ID_BINARY_SENSOR_GRID_CONNECTED
                name: Grid connected
              - entity: ENTITY_ID_BINARY_SENSOR_BYPASS_ENABLED
                name: Bypass
              - entity: ENTITY_ID_BINARY_SENSOR_UPS_MODE
                name: UPS mode
              - entity: ENTITY_ID_SENSOR_REMAINING_TIME
                name: Remaining time

      - type: grid
        cards:
          - type: history-graph
            title: Power flow (24 h)
            hours_to_show: 24
            entities:
              - entity: ENTITY_ID_SENSOR_AC_INPUT_POWER
                name: AC input
              - entity: ENTITY_ID_SENSOR_AC_OUTPUT_POWER
                name: AC output
              - entity: ENTITY_ID_SENSOR_OUTPUT_TOTAL_POWER
                name: Output total
              - entity: ENTITY_ID_SENSOR_DC_OUTPUT_POWER
                name: DC output
          - type: history-graph
            title: Battery (24 h)
            hours_to_show: 24
            entities:
              - entity: ENTITY_ID_SENSOR_BATTERY_SOC
                name: SOC

      - type: grid
        cards:
          - type: entities
            title: Controls
            show_header_toggle: false
            entities:
              - entity: ENTITY_ID_SWITCH_AC_OUTPUT
                name: AC output
              - entity: ENTITY_ID_SWITCH_DC_OUTPUT
                name: DC output
              - entity: ENTITY_ID_SWITCH_AC_INPUT
                name: AC input
              - entity: ENTITY_ID_SWITCH_SCHEDULED_CHARGING
                name: Scheduled charging
              - entity: ENTITY_ID_NUMBER_AC_CHARGE_POWER_LIMIT
                name: AC charge power limit
              - entity: ENTITY_ID_NUMBER_BATTERY_PROTECTION_LOWER_SOC
                name: Battery protection lower SOC
              - entity: ENTITY_ID_NUMBER_BATTERY_PROTECTION_UPPER_SOC
                name: Battery protection upper SOC

      - type: grid
        cards:
          - type: history-graph
            title: Temperature and diagnostics (24 h)
            hours_to_show: 24
            entities:
              - entity: ENTITY_ID_SENSOR_BATTERY_TEMPERATURE
                name: Battery temperature
              - entity: ENTITY_ID_SENSOR_DEVICE_TEMPERATURE
                name: Device temperature
          - type: entities
            title: Diagnostics
            show_header_toggle: false
            entities:
              - entity: ENTITY_ID_SENSOR_LAST_UPDATE
                name: Last update
              - entity: ENTITY_ID_SENSOR_ERROR_CODE
                name: Error code
              - entity: ENTITY_ID_SENSOR_FIRMWARE_VERSION
                name: Firmware
              - entity: ENTITY_ID_SENSOR_WIFI_VERSION
                name: Wi-Fi
              - entity: ENTITY_ID_SENSOR_MCU_VERSION
                name: MCU
```

## Notes

- Power/battery/temperature sensors include `device_class` and `state_class`
  metadata for history and statistics graphs. `remaining_time` is a duration
  sensor (minutes) with a localized display attribute.
- For advanced visuals (energy flow, custom charts), you can use optional
  frontend cards from HACS (for example ApexCharts/mini-graph) with the same
  entities; those cards are not provided by this integration.
- If an entity is unavailable, confirm the integration is loaded, the device is
  online, and the entity belongs to **Gendome (Mod Junya)** (not the original
  integration).
