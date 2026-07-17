# home-assistant-bradford-white-connect

[![GitHub Release][releases-shield]][releases]
[![hacs][hacsbadge]][hacs]

This custom component for Home Assistant adds support for managing your water heater via the Bradford White Connect platform.

## What's new in 0.2.15

Version 0.2.15 expands the integration's telemetry, diagnostics, and
device controls. It also reports the appliance's live operating mode via
`current_heat_mode` and exposes `user_heat_mode` as a separate **Requested
heat mode** diagnostic sensor. The requested and actual modes can differ.

Sensor values are device-pushed telemetry. If the appliance loses power or
network connectivity, values can remain at their last reported state; the
cloud-reported `connection_status` is informational only.

## Installation instructions

### Using HACS

The easiest way to install this integration is with [HACS][hacs]. First, [install HACS][hacs-download] if you don't have it yet.\
Click on the link below or search for `Bradford White Connect` in HACS.\
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ablyler&repository=home-assistant-bradford-white-connect&category=integration)\
Click download and after this, restart Home Assistant.

### Manual installation

1. Update Home Assistant to version 2021.12 or newer.
2. Clone this repository.
3. Copy the `custom_components/bradford_white_connect` folder into your Home Assistant's `custom_components` folder.

## Configuring

1. Add `Bradford White Connect` integration via UI. Using My Home Assistant service, you can click on:\
   [![Add Bradford White Connect][add-integration-badge]][add-integration]\
   Or add it to Home Assistant by going to `Configuration -> Devices & Services`, clicking `+ Add Integration` and searching for `Bradford White Connect`.
2. Enter Bradford White Connect cloud hostname, account id, username, and password.
3. The integration will discover appliance on local network(s).
4. If an appliance is not automatically discovered, but is registered to the cloud account, user is prompted to enter IPv4 address of the appliance.
5. If you want to use integration with air conditioner unit(s), please select the checkbox on `Advanced settings` page.

## Supported entities

This custom component creates the following entities for each discovered water
heater. Entities backed by a device property are only created when the property
is actually reported by the unit, so the exact set varies by model and firmware.

| Platform        | Entity                              | Notes |
| --------------- | ----------------------------------- | --------------------------------- |
| `water_heater`  | Controller                          | Current/target temperature, operation mode, away mode |
| `sensor`        | Heat pump energy usage              | Daily kWh (heat pump) |
| `sensor`        | Resistance energy usage             | Daily kWh (resistance element) |
| `sensor`        | Daily / total energy                | When reported by the unit |
| `sensor`        | Tank temperature (upper, lower)     | Lower only on dual-sensor units |
| `sensor`        | Ambient temperature                 | Air around the appliance |
| `sensor`        | Evaporator inlet / outlet temp      | Heat pump units only (diagnostic) |
| `sensor`        | Compressor discharge temp           | Heat pump units only (diagnostic) |
| `sensor`        | Evaporator superheat                | Heat pump units only (diagnostic) |
| `sensor`        | Water setpoint (current / min / max) | Diagnostic |
| `sensor`        | Heat pump / resistance power        | Live kW |
| `sensor`        | Mains voltage / current             | Diagnostic |
| `sensor`        | Heat pump / upper / lower element current | Diagnostic |
| `sensor`        | Wi-Fi signal strength               | Diagnostic |
| `sensor`        | Air filter dirtiness                | Diagnostic |
| `sensor`        | Appliance runtime / compressor runtime | Total hours, diagnostic |
| `sensor`        | Mode time remaining                 | Minutes, diagnostic |
| `sensor`        | EEV position                        | Heat pump units only (diagnostic) |
| `sensor`        | Hot water availability              | Percent of stored hot water |
| `sensor`        | Stored / maximum thermal capacity   | Capacity readings |
| `sensor`        | Tank size                           | Diagnostic |
| `sensor`        | Appliance type / model              | Diagnostic |
| `sensor`        | Current heat mode                   | Enum: hybrid / electric / heat_pump / high_demand / vacation |
| `sensor`        | Requested heat mode                 | Last requested mode, diagnostic |
| `sensor`        | DRM status                          | Utility load-shedding state |
| `sensor`        | Active alarms                       | Set bit positions of the alarm bitmap (e.g. "bit 13 (tentative F14)"); raw bitmap + tentative descriptions in attributes — see notes below |
| `sensor`        | Connection status                   | Cloud-reported status (informational only) |
| `binary_sensor` | Compressor running                  | Heat pump units only |
| `binary_sensor` | Evaporator fan running              | Heat pump units only (diagnostic) |
| `binary_sensor` | Upper / lower element running       | Electric resistance elements |
| `binary_sensor` | Global error                        | Diagnostic problem indicator |
| `binary_sensor` | Water overheat                      | Diagnostic problem indicator |
| `button`        | Reboot controller                   | Writes `controller_reboot=1` |
| `button`        | Reboot Wi-Fi                        | Writes `wifi_reboot=1` |
| `number`        | Vacation mode days                  | 1-199 days, writes `set_vacation_mode_days` |
| `number`        | Electric mode days                  | 1-99 days, writes `set_electric_mode_days` |
| `number`        | Standard / vacation heat timer      | -1..365 days, writes `set_heat_timer_1` / `set_heat_timer_4` |
| `switch`        | DRM advanced load-up                | Opt-in to utility advanced load-up behavior |
| `switch`        | DRM service                         | Toggle DRM service acknowledgement |
| `text`          | Heater name                         | Friendly name shown in the BW Connect app |

### Notes on the alarm sensor and remote clear buttons

The state of the **Active alarms** sensor reports the **bit positions**
set in the raw `alarm` bitmap (e.g. `bit 13 (tentative F14)`). The raw
bitmap is preserved on the sensor's `raw_bitmap` attribute alongside
`active_bits`, `tentative_codes`, and `tentative_descriptions`.

The F-code labels and English descriptions are a **best-guess** based on
the Bradford White AeroTherm RE2H50/RE2H80 service quick-reference guide
(P/N 31-75036-1, 03-15), which covers personalities up to 86A. Newer
personalities (such as 63A on the RE2H65T10) appear to extend the fault
table with codes BW has not published publicly, and the older mapping
has been observed to disagree with field behavior on those units. Treat
the description attribute as a hypothesis, not as authoritative.

Bradford White's cloud API has no write permission for the latched
`alarm` bitmap, `global_error`, or `water_overheat_notify` outputs:
the **Clear alarm counts** button only resets the controller's stored
`alarm_count` value and does not clear a latched fault. Field testing on
personality 63A also shows that **Reset filter** does not clear the
latched alarm bit. Use the keypad Service Mode procedure below to clear
latched faults at the unit.

### How to clear a latched fault at the unit

If `Active alarms`, `Global error`, or `Water overheat` remains
asserted after the underlying problem is resolved, the latch has to be
cleared at the heater itself:

1. **Verify there is no live fault first.** Look at the front-panel
   LEDs. If a fault is actively shown (not just latched in history),
   resolve the underlying cause before clearing.
2. **Enter Service Mode.** On the front panel, press and hold the
   **UP arrow + Enter** buttons simultaneously for ~5 seconds. You'll
   hear a single beep when the buttons register, then a two-tone
   acknowledgement.
3. **Navigate to "View Faults and Counters."** Press **Mode** to cycle
   through the five Service Mode functions until the **Hybrid** LED is
   lit (that's the Faults function). The display shows the active fault
   code or `- - -` if none.
4. **Clear the fault history.** Press and hold **Enter** for ~5 seconds
   and listen for the beep. This clears all stored fault codes and
   counters on the controller.
5. **Exit Service Mode.** Press and hold the **UP + Down arrows**
   simultaneously for ~5 seconds (two beeps), or just wait 15 minutes
   for the timeout.
6. **For an actual TCO (over-temperature) trip**, the red TCO reset
   button behind the upper access panel must also be physically pressed
   before the latch will clear. The TCO opens at ~180°F and cuts power
   to its element until reset.

After the latch clears at the unit, the cloud-side output properties
will follow within one or two Bradford White Connect refresh cycles
and the HA sensors will update on the next coordinator update.

Source: Bradford White AeroTherm RE2H50/RE2H80 service quick-reference
guide (P/N 31-75036-1, 03-15). The procedure is the same on the newer
RE2H65T10 / personality 63A.

### Diagnostics

A redacted snapshot of the cloud API data — including every device property
the API returns — is available via **Settings → Devices & Services →
Bradford White Connect → Download diagnostics**. PII such as the DSN, MAC,
LAN IP, geographic coordinates, and serial number are redacted before the
file is written.

## Contributors

Thanks to [@disruptivepatternmaterial](https://github.com/disruptivepatternmaterial)
for the expanded entity coverage, diagnostics, controls, and supporting tests
merged in version 0.2.15. See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the
project's contributor acknowledgements.

## Troubleshooting

If there are problems with the integration setup, advanced debug logging can be activated via the `Advanced settings` page.

Once activated, logs can be seen by:

Select `Load Full Home Assistant Log` to see all debug mode logs. Please include as much logs as possible if you open an [issue](https://github.com/ablyler/home-assistant-bradford-white-connect/issues/new?assignees=&labels=&template=issue.md).

[![Home Assistant Logs][ha-logs-badge]][ha-logs]

Debug logging can be activated without going through setup process:

[![Logging service][ha-service-badge]][ha-service]

On entry page, paste following content:

```yaml
service: logger.set_level
data:
  custom_components.bradford_white_connect: DEBUG
```

It is possible to activate debug logging on Home Assistent start. To do this, open Home Assistant's `configuration.yaml` file on your machine, and add following to `logger` configuration:

```yaml
logger:
  # Begging of lines to add
  logs:
    custom_components.bradford_white_connect: debug
  # End of lines to add
```

Home Assistant needs to be restarted after this change.

## Notice

Bradford White Connect and other names are trademarks of their respective owners.

[add-integration]: https://my.home-assistant.io/redirect/config_flow_start/?domain=bradford_white_connect
[add-integration-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[hacs]: https://hacs.xyz
[hacs-download]: https://hacs.xyz/docs/setup/download
[hacsbadge]: https://img.shields.io/badge/HACS-Default-blue.svg?style=flat
[ha-logs]: https://my.home-assistant.io/redirect/logs
[ha-logs-badge]: https://my.home-assistant.io/badges/logs.svg
[ha-service]: https://my.home-assistant.io/redirect/developer_call_service/?service=logger.set_level
[ha-service-badge]: https://my.home-assistant.io/badges/developer_call_service.svg
[releases-shield]: https://img.shields.io/github/release/ablyler/home-assistant-bradford-white-connect.svg?style=flat
[releases]: https://github.com/ablyler/home-assistant-bradford-white-connect/releases
