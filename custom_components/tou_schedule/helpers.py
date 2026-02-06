"""Helper utilities for TOU schedule."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_RATE_TYPES, CONF_RULES


def get_options(entry: ConfigEntry) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return rate types and rules from entry options."""
    options = entry.options
    return list(options.get(CONF_RATE_TYPES, [])), list(options.get(CONF_RULES, []))
