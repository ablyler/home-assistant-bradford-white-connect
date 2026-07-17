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
ENERGY_USAGE_INTERVAL = timedelta(minutes=30)

# Hard ceiling for a single coordinator refresh. The upstream
# ``bradford_white_connect_client`` issues its HTTP calls without an explicit
# timeout, so a stalled cloud connection (e.g. a silently dropped keep-alive
# socket) can otherwise wedge a refresh forever, holding the coordinator lock
# and permanently stopping all future updates with no error logged. Bounding
# every refresh keeps the coordinator self-healing: a hung request fails fast
# as ``UpdateFailed`` and the next interval retries.
REQUEST_TIMEOUT = timedelta(seconds=60)

# energy types
ENERGY_TYPE_RESISTANCE = "resistance"
ENERGY_TYPE_HEAT_PUMP = "heat_pump"
