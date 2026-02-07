import sys
from pathlib import Path
import shutil

import pytest
import pytest_socket
from pytest_homeassistant_custom_component.common import get_test_config_dir

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_sessionstart(session):
    test_config_dir = Path(get_test_config_dir())
    if str(test_config_dir) not in sys.path:
        sys.path.insert(0, str(test_config_dir))

    source_root = ROOT / "custom_components" / "tou_schedule"
    target_root = test_config_dir / "custom_components" / "tou_schedule"
    target_root.parent.mkdir(parents=True, exist_ok=True)
    if target_root.exists():
        shutil.rmtree(target_root)
    shutil.copytree(source_root, target_root)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    if fixturedef.argname == "event_loop":
        pytest_socket.enable_socket()
    yield
