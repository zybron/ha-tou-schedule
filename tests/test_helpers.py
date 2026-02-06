import importlib.util
import sys
import types
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

config_entries = types.ModuleType("homeassistant.config_entries")


class ConfigEntry:
    def __init__(self, options):
        self.options = options


config_entries.ConfigEntry = ConfigEntry
sys.modules.setdefault("homeassistant.config_entries", config_entries)

MODULE_PATH = ROOT / "custom_components" / "tou_schedule" / "helpers.py"

spec = importlib.util.spec_from_file_location(
    "custom_components.tou_schedule.helpers", MODULE_PATH
)
helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helpers
assert spec.loader is not None
spec.loader.exec_module(helpers)

get_options = helpers.get_options


def test_get_options_returns_lists():
    entry = ConfigEntry(
        options={
            "rate_types": [{"id": "default", "name": "Default", "rate": 0.1, "default": True}],
            "rules": [{"id": "rule1"}],
        }
    )

    rate_types, rules = get_options(entry)

    assert rate_types == [{"id": "default", "name": "Default", "rate": 0.1, "default": True}]
    assert rules == [{"id": "rule1"}]
