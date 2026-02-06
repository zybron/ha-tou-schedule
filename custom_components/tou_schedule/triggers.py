"""Trigger platform for TOU schedule."""
from __future__ import annotations

from typing import Any, Callable

import voluptuous as vol

from homeassistant.const import CONF_EVENT, CONF_PLATFORM
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.trigger import TriggerActionType
from homeassistant.helpers.typing import ConfigType

from . import TouScheduleCoordinator, get_active_rate_type
from .const import (
    CONF_RATE_TYPE,
    DOMAIN,
    TRIGGER_PERIOD_ENDED,
    TRIGGER_PERIOD_STARTED,
    TRIGGER_RATE_ENTERED,
    TRIGGER_RATE_EXITED,
)

TRIGGER_SCHEMA = cv.TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_PLATFORM): DOMAIN,
        vol.Required(CONF_EVENT): vol.In(
            [
                TRIGGER_RATE_ENTERED,
                TRIGGER_RATE_EXITED,
                TRIGGER_PERIOD_STARTED,
                TRIGGER_PERIOD_ENDED,
            ]
        ),
        vol.Optional(CONF_RATE_TYPE): str,
    }
)


async def async_validate_trigger_config(hass: HomeAssistant, config: ConfigType) -> ConfigType:
    return TRIGGER_SCHEMA(config)


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: dict[str, Any],
) -> Callable[[], None]:
    entries = list(hass.data.get(DOMAIN, {}).values())
    if not entries:
        raise ValueError("No TOU schedule configuration entries found")
    if len(entries) > 1:
        raise ValueError("Multiple TOU schedule entries found; use a single entry for triggers")
    coordinator: TouScheduleCoordinator = entries[0]
    target_event = config[CONF_EVENT]
    target_rate_type = config.get(CONF_RATE_TYPE)
    last_rate = get_active_rate_type(coordinator)

    @callback
    def _handle_coordinator_update() -> None:
        nonlocal last_rate
        current_rate = get_active_rate_type(coordinator)
        events: list[tuple[str, str | None]] = []
        if current_rate.rate_type_id != last_rate.rate_type_id:
            events.append((TRIGGER_RATE_EXITED, last_rate.rate_type_id))
            events.append((TRIGGER_RATE_ENTERED, current_rate.rate_type_id))
        if current_rate.rule_id != last_rate.rule_id:
            if last_rate.rule_id is not None:
                events.append((TRIGGER_PERIOD_ENDED, last_rate.rate_type_id))
            if current_rate.rule_id is not None:
                events.append((TRIGGER_PERIOD_STARTED, current_rate.rate_type_id))
        last_rate = current_rate

        for event, rate_type_id in events:
            if event != target_event:
                continue
            if target_rate_type and rate_type_id != target_rate_type:
                continue
            hass.async_run_hass_job(
                action,
                {
                    "trigger": {
                        **trigger_info,
                        "platform": DOMAIN,
                        "event": event,
                        "rate_type": rate_type_id,
                    }
                },
                hass,
            )

    unsub = coordinator.async_add_listener(_handle_coordinator_update)

    def _unsub() -> None:
        unsub()

    return _unsub
