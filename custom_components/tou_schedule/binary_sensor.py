"""Binary sensors for TOU schedule."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TouScheduleCoordinator, get_active_rate_type
from .const import (
    ATTR_ACTIVE_RULE,
    CONF_ID,
    CONF_MONTHS,
    CONF_NAME,
    CONF_PERIODS,
    CONF_RATE_TYPE,
    CONF_WEEKDAYS,
    DOMAIN,
)
from .helpers import get_options


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: TouScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]
    rate_types, rules = get_options(entry)
    entities = [
        TouRateTypeBinarySensor(coordinator, entry, rate_type)
        for rate_type in rate_types
    ]
    entities.extend(
        TouRuleBinarySensor(coordinator, entry, rule, rate_types) for rule in rules
    )
    async_add_entities(entities)


class TouRateTypeBinarySensor(CoordinatorEntity[TouScheduleCoordinator], BinarySensorEntity):
    """Binary sensor that is on for the active rate type."""

    def __init__(
        self,
        coordinator: TouScheduleCoordinator,
        entry: ConfigEntry,
        rate_type: dict,
    ) -> None:
        super().__init__(coordinator)
        self._rate_type_id = rate_type[CONF_ID]
        self._attr_name = f"TOU Rate {rate_type[CONF_NAME]}"
        self._attr_unique_id = f"tou_rate_{self._rate_type_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TOU Schedule",
        )

    @property
    def is_on(self) -> bool:
        return get_active_rate_type(self.coordinator).rate_type_id == self._rate_type_id


class TouRuleBinarySensor(CoordinatorEntity[TouScheduleCoordinator], BinarySensorEntity):
    """Binary sensor that is on for the active rule."""

    def __init__(
        self,
        coordinator: TouScheduleCoordinator,
        entry: ConfigEntry,
        rule: dict,
        rate_types: list[dict],
    ) -> None:
        super().__init__(coordinator)
        self._rule_id = rule[CONF_ID]
        self._rule = rule
        self._rate_type_name = self._resolve_rate_type_name(rate_types)
        self._attr_name = f"TOU Rule {rule[CONF_NAME]}"
        self._attr_unique_id = f"tou_rule_{self._rule_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TOU Schedule",
        )

    def _resolve_rate_type_name(self, rate_types: list[dict]) -> str | None:
        for rate_type in rate_types:
            if rate_type[CONF_ID] == self._rule.get(CONF_RATE_TYPE):
                return rate_type[CONF_NAME]
        return None

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get(ATTR_ACTIVE_RULE) == self._rule_id

    @property
    def extra_state_attributes(self) -> dict:
        return {
            CONF_RATE_TYPE: self._rule.get(CONF_RATE_TYPE),
            "rate_type_name": self._rate_type_name,
            CONF_MONTHS: self._rule.get(CONF_MONTHS, []),
            CONF_WEEKDAYS: self._rule.get(CONF_WEEKDAYS, []),
            CONF_PERIODS: self._rule.get(CONF_PERIODS, []),
        }
