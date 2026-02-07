"""Number entities for TOU schedule rate types."""
from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ID, CONF_NAME, CONF_RATE, CONF_RATE_TYPES, DOMAIN
from .helpers import get_options
from . import TouScheduleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: TouScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]
    rate_types, _ = get_options(entry)
    entities = [
        TouRateTypeNumber(coordinator, entry, rate_type) for rate_type in rate_types
    ]
    async_add_entities(entities)


class TouRateTypeNumber(CoordinatorEntity[TouScheduleCoordinator], NumberEntity):
    """Number entity to edit a rate type price."""

    _attr_has_entity_name = True
    _attr_native_step = 0.001
    _attr_native_min_value = 0.0

    def __init__(
        self,
        coordinator: TouScheduleCoordinator,
        entry: ConfigEntry,
        rate_type: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._rate_type_id = rate_type[CONF_ID]
        self._attr_unique_id = f"{entry.entry_id}_rate_{self._rate_type_id}"
        self._attr_name = rate_type[CONF_NAME]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "TOU Schedule",
        }

    @property
    def native_value(self) -> float | None:
        rate_types, _ = get_options(self._entry)
        for rate_type in rate_types:
            if rate_type[CONF_ID] == self._rate_type_id:
                return float(rate_type[CONF_RATE])
        return None

    async def async_set_native_value(self, value: float) -> None:
        options = dict(self._entry.options)
        rate_types = list(options.get(CONF_RATE_TYPES, []))
        for rate_type in rate_types:
            if rate_type[CONF_ID] == self._rate_type_id:
                rate_type[CONF_RATE] = float(value)
                break
        options[CONF_RATE_TYPES] = rate_types
        self.hass.config_entries.async_update_entry(self._entry, options=options)
