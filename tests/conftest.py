"""Pytest setup: keep the unit tests self-contained.

The integration's package ``__init__`` imports the full Home Assistant +
upstream-client stack at import time, which would force every test run
to install the entire HA dev environment. These tests deliberately only
exercise the pure-function modules (``fault_codes``, ``helper``), so we
add the integration directory directly to ``sys.path`` and import them
as flat modules. We also install a minimal stub for the
``bradford_white_connect_client`` submodules they import, so the tests
run with nothing more than ``pytest`` installed.

In CI, ``pipenv install --dev`` will provide the real upstream client.
The stub is registered into ``sys.modules`` before the real package is
ever imported, so the stub wins for the duration of the test session;
its surface is intentionally a superset of what the modules-under-test
touch, so the test outcome is identical against either.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types


def _install_upstream_client_stub() -> None:
    if "bradford_white_connect_client" in sys.modules:
        return

    root = types.ModuleType("bradford_white_connect_client")

    types_mod = types.ModuleType("bradford_white_connect_client.types")

    class _Device:
        """Minimal stand-in for the real Device dataclass."""

        properties: dict | None = None

    types_mod.Device = _Device
    root.types = types_mod

    constants_mod = types.ModuleType("bradford_white_connect_client.constants")

    class _BradfordWhiteConnectHeatingModes:
        HYBRID = 1
        ELECTRIC = 2
        HEAT_PUMP = 3
        HYBRID_PLUS = 4
        VACATION = 5

        @staticmethod
        def is_valid(value: int) -> bool:
            return value in (1, 2, 3, 4, 5)

    constants_mod.BradfordWhiteConnectHeatingModes = _BradfordWhiteConnectHeatingModes
    root.constants = constants_mod

    sys.modules["bradford_white_connect_client"] = root
    sys.modules["bradford_white_connect_client.types"] = types_mod
    sys.modules["bradford_white_connect_client.constants"] = constants_mod


_install_upstream_client_stub()


_INTEGRATION_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "bradford_white_connect"
)
if str(_INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_DIR))
