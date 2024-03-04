# home-assistant-bradford-white-connect

[![GitHub Release][releases-shield]][releases]
[![hacs][hacsbadge]][hacs]

This custom component for Home Assistant adds support for managing your water heater via the Bradford White Connect platform.

## Installation instruction

### HACS

The easiest way to install this integration is with [HACS][hacs]. First, install [HACS][hacs-download] if you don't have it yet. In Home Assistant, go to `HACS -> Integrations`, click on `+ Explore & Download Repositories`, search for `Bradford White Connect`, and click download. After download, restart Home Assistant.

Once the integration is installed, you can add it to the Home Assistant by going to `Configuration -> Devices & Services`, clicking `+ Add Integration` and searching for `Bradford White Connect` or, using My Home Assistant service, you can click on:

[![Add Bradford White Connect][add-integration-badge]][add-integration]

### Manual installation

1. Update Home Assistant to version 2021.12 or newer.
2. Clone this repository.
3. Copy the `custom_components/bradford_white_connect` folder into your Home Assistant's `custom_components` folder.

### Configuring

1. Add `Bradford White Connect` integration via UI.
2. Enter Bradford White Connect cloud hostname, account id, username, and password.
3. The integration will discover appliance on local network(s).
4. If an appliance is not automatically discovered, but is registered to the cloud account, user is prompted to enter IPv4 address of the appliance.
5. If you want to use integration with air conditioner unit(s), please select the checkbox on `Advanced settings` page.

## Supported entities

This custom component creates following entities for each discovered dehumidifier:

| Platform       | Description             |
| -------------- | ----------------------- |
| `water_heater` | Controller water heater |

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

[add-integration]: https://my.home-assistant.io/redirect/config_flow_start?domain=bradford_white_connect
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
