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

MODULE_PATH = ROOT / "custom_components" / "tou_schedule" / "validation.py"

spec = importlib.util.spec_from_file_location(
    "custom_components.tou_schedule.validation", MODULE_PATH
)
validation = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validation
assert spec.loader is not None
spec.loader.exec_module(validation)

validate_rate_types = validation.validate_rate_types
validate_rule_overlaps = validation.validate_rule_overlaps
validate_rules = validation.validate_rules


def test_validate_rate_types_requires_default():
    result = validate_rate_types(
        [
            {"id": "offpeak", "name": "Off", "rate": 0.1, "default": False},
            {"id": "peak", "name": "Peak", "rate": 0.2, "default": False},
        ]
    )
    assert not result.valid


def test_validate_rate_types_requires_unique_ids():
    result = validate_rate_types(
        [
            {"id": "peak", "name": "Peak", "rate": 0.2, "default": True},
            {"id": "peak", "name": "Peak2", "rate": 0.3, "default": False},
        ]
    )
    assert not result.valid


def test_validate_rule_overlap_detects_conflict():
    rules = [
        {
            "id": "rule1",
            "name": "Rule 1",
            "rate_type": "peak",
            "months": [1],
            "weekdays": [0],
            "periods": [{"start": "10:00", "end": "12:00"}],
        },
        {
            "id": "rule2",
            "name": "Rule 2",
            "rate_type": "offpeak",
            "months": [1],
            "weekdays": [0],
            "periods": [{"start": "11:00", "end": "13:00"}],
        },
    ]
    result = validate_rule_overlaps(rules)
    assert not result.valid


def test_validate_rules_allows_valid():
    rules = [
        {
            "id": "rule1",
            "name": "Rule 1",
            "rate_type": "peak",
            "months": [1],
            "weekdays": [0],
            "periods": [{"start": "10:00", "end": "12:00"}],
        }
    ]
    rate_types = [{"id": "peak", "name": "Peak", "rate": 0.2, "default": True}]
    result = validate_rules(rules, rate_types)
    assert result.valid
