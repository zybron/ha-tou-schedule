"""TOU schedule integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ACTIVE_RATE_TYPE,
    ATTR_ACTIVE_RULE,
    ATTR_NEXT_TRANSITION,
    ATTR_PRICES_TODAY,
    ATTR_PRICES_TOMORROW,
    CONF_DEFAULT,
    CONF_ID,
    CONF_NAME,
    CONF_RATE,
    CONF_RATE_TYPES,
    CONF_RULES,
    DOMAIN,
    PLATFORMS,
)
from .helpers import get_options
from .scheduler import ActiveRate, build_prices_for_day, get_active_rate, local_midnight, next_transition
from .validation import validate_rate_types

DEFAULT_RATE_TYPE = {
    CONF_ID: "default",
    CONF_NAME: "Default",
    CONF_RATE: 0.0,
    CONF_DEFAULT: True,
}


LOGGER = logging.getLogger(__name__)


class TouScheduleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for TOU schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=1),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        rate_types, rules = get_options(self.entry)
        validation = validate_rate_types(rate_types)
        if not validation.valid:
            raise UpdateFailed(validation.message or "Invalid rate types")

        now = dt_util.now()
        active_rate = get_active_rate(rules, rate_types, now)
        midnight = local_midnight(now)
        tzinfo = dt_util.get_time_zone(self.hass.config.time_zone)
        prices_today = build_prices_for_day(midnight, rules, rate_types, tzinfo)
        prices_tomorrow = build_prices_for_day(midnight + timedelta(days=1), rules, rate_types, tzinfo)
        next_change = next_transition(rules, rate_types, now)

        return {
            "active_rate": active_rate,
            ATTR_ACTIVE_RULE: active_rate.rule_id,
            ATTR_ACTIVE_RATE_TYPE: active_rate.rate_type_id,
            ATTR_NEXT_TRANSITION: next_change.isoformat() if next_change else None,
            ATTR_PRICES_TODAY: prices_today,
            ATTR_PRICES_TOMORROW: prices_tomorrow,
        }


def _ensure_default_rate_type(entry: ConfigEntry) -> None:
    options = dict(entry.options)
    rate_types = list(options.get(CONF_RATE_TYPES, []))
    if not rate_types:
        options[CONF_RATE_TYPES] = [DEFAULT_RATE_TYPE]
        entry.hass.config_entries.async_update_entry(entry, options=options)


def _ensure_default_rate_selection(entry: ConfigEntry) -> None:
    options = dict(entry.options)
    rate_types = list(options.get(CONF_RATE_TYPES, []))
    if not rate_types:
        return
    if not any(rate.get(CONF_DEFAULT) for rate in rate_types):
        rate_types[0][CONF_DEFAULT] = True
        options[CONF_RATE_TYPES] = rate_types
        entry.hass.config_entries.async_update_entry(entry, options=options)


def get_active_rate_type(coordinator: TouScheduleCoordinator) -> ActiveRate:
    return coordinator.data["active_rate"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _ensure_default_rate_type(entry)
    _ensure_default_rate_selection(entry)
    coordinator = TouScheduleCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
