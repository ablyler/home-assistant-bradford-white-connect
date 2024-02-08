"""Constants for the Bradford White Connect integration."""

from datetime import timedelta
from enum import Enum

DOMAIN = "bradford-white-connect"

CONF_HOSTNAME = "hostname"
CONF_ACCOUNT_NUMBER = "account_number"
CONF_USERNAME = "username"
# trunk-ignore(bandit/B105)
CONF_PASSWORD = "password"

# Update interval to be used for normal background updates.
REGULAR_INTERVAL = timedelta(seconds=30)

# Update interval to be used while a mode or setpoint change is in progress.
FAST_INTERVAL = timedelta(seconds=1)
