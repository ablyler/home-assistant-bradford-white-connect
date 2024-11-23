"""Constants for the Bradford White Connect integration."""

from datetime import timedelta

DOMAIN = "bradford_white_connect"

CONF_HOSTNAME = "hostname"
CONF_ACCOUNT_NUMBER = "account_number"
CONF_USERNAME = "username"
# trunk-ignore(bandit/B105)
CONF_PASSWORD = "password"

# Update interval to be used for normal background updates.
REGULAR_INTERVAL = timedelta(minutes=5)

# Update interval to be used while a mode or setpoint change is in progress.
FAST_INTERVAL = timedelta(seconds=5)

# Update interval to be used for energy usage data.
ENERGY_USAGE_INTERVAL = timedelta(hours=12)

# energy types
ENERGY_TYPE_RESISTANCE = "resistance"
ENERGY_TYPE_HEAT_PUMP = "heat_pump"
