import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

package = types.ModuleType("custom_components")
package.__path__ = [str(ROOT / "custom_components")]
sys.modules.setdefault("custom_components", package)

subpkg = types.ModuleType("custom_components.tou_schedule")
subpkg.__path__ = [str(ROOT / "custom_components" / "tou_schedule")]
sys.modules.setdefault("custom_components.tou_schedule", subpkg)

homeassistant = types.ModuleType("homeassistant")
homeassistant.__path__ = []
sys.modules.setdefault("homeassistant", homeassistant)

ha_util = types.ModuleType("homeassistant.util")
ha_util.__path__ = []
sys.modules.setdefault("homeassistant.util", ha_util)

dt_util = types.ModuleType("homeassistant.util.dt")


def as_local(value):
    return value


dt_util.as_local = as_local
sys.modules.setdefault("homeassistant.util.dt", dt_util)

MODULE_PATH = ROOT / "custom_components" / "tou_schedule" / "scheduler.py"

spec = importlib.util.spec_from_file_location(
    "custom_components.tou_schedule.scheduler", MODULE_PATH
)
scheduler = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scheduler
assert spec.loader is not None
spec.loader.exec_module(scheduler)

ActiveRate = scheduler.ActiveRate
build_prices_for_day = scheduler.build_prices_for_day
get_active_rate = scheduler.get_active_rate
local_midnight = scheduler.local_midnight
next_transition = scheduler.next_transition


def test_get_active_rate_default_when_no_rule():
    rate_types = [{"id": "default", "name": "Default", "rate": 0.1, "default": True}]
    rules = []

    result = get_active_rate(rules, rate_types, datetime(2024, 1, 1, 0, 30))

    assert result == ActiveRate(
        rate_type_id="default",
        rate_type_name="Default",
        rate=0.1,
        rule_id=None,
    )


def test_get_active_rate_rule_match():
    rate_types = [
        {"id": "default", "name": "Default", "rate": 0.1, "default": True},
        {"id": "peak", "name": "Peak", "rate": 0.2, "default": False},
    ]
    rules = [
        {
            "id": "rule1",
            "name": "Peak Hours",
            "rate_type": "peak",
            "months": [],
            "weekdays": [],
            "periods": [{"start": "10:00", "end": "12:00"}],
        }
    ]

    result = get_active_rate(rules, rate_types, datetime(2024, 1, 1, 10, 30))

    assert result.rule_id == "rule1"
    assert result.rate_type_id == "peak"
    assert result.rate == 0.2


def test_build_prices_for_day_hourly():
    rate_types = [
        {"id": "default", "name": "Default", "rate": 0.1, "default": True},
        {"id": "peak", "name": "Peak", "rate": 0.2, "default": False},
    ]
    rules = [
        {
            "id": "rule1",
            "name": "Peak Hour",
            "rate_type": "peak",
            "months": [],
            "weekdays": [],
            "periods": [{"start": "01:00", "end": "02:00"}],
        }
    ]

    prices = build_prices_for_day(datetime(2024, 1, 1, 0, 0), rules, rate_types, timezone.utc)

    assert len(prices) == 24
    assert prices[0]["price"] == 0.1
    assert prices[1]["price"] == 0.2
    assert prices[2]["price"] == 0.1


def test_next_transition_detects_change():
    rate_types = [
        {"id": "default", "name": "Default", "rate": 0.1, "default": True},
        {"id": "peak", "name": "Peak", "rate": 0.2, "default": False},
    ]
    rules = [
        {
            "id": "rule1",
            "name": "Peak Hour",
            "rate_type": "peak",
            "months": [],
            "weekdays": [],
            "periods": [{"start": "01:00", "end": "02:00"}],
        }
    ]

    result = next_transition(rules, rate_types, datetime(2024, 1, 1, 0, 30))

    assert result == datetime(2024, 1, 1, 1, 0)


def test_local_midnight():
    value = datetime(2024, 1, 1, 13, 45)

    result = local_midnight(value)

    assert result == datetime(2024, 1, 1, 0, 0)
