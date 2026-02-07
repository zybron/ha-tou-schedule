"""Sensors for TOU schedule."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TouScheduleCoordinator, get_active_rate_type
from .const import (
    ATTR_ACTIVE_RATE_TYPE,
    ATTR_ACTIVE_RATE_TYPE_ID,
    ATTR_ACTIVE_RULE,
    ATTR_NEXT_TRANSITION,
    ATTR_PRICES_TODAY,
    ATTR_PRICES_TOMORROW,
    CONF_NAME,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: TouScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        TouEVPriceSensor(coordinator, entry),
        TouActiveRuleSensor(coordinator, entry),
        TouActiveRateTypeSensor(coordinator, entry),
        TouNextTransitionSensor(coordinator, entry),
    ]
    async_add_entities(entities)


class TouBaseSensor(CoordinatorEntity[TouScheduleCoordinator], SensorEntity):
    """Base sensor for TOU schedule."""

    def __init__(self, coordinator: TouScheduleCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TOU Schedule",
        )


class TouEVPriceSensor(TouBaseSensor):
    """EV Smart Charging price sensor."""

    _attr_name = "TOU EV Price"
    _attr_unique_id = "tou_ev_price"
    _attr_native_unit_of_measurement = "USD/kWh"

    @property
    def native_value(self) -> float:
        return float(get_active_rate_type(self.coordinator).rate)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_PRICES_TODAY: self.coordinator.data[ATTR_PRICES_TODAY],
            ATTR_PRICES_TOMORROW: self.coordinator.data[ATTR_PRICES_TOMORROW],
        }


class TouActiveRuleSensor(TouBaseSensor):
    _attr_name = "TOU Active Rule"
    _attr_unique_id = "tou_active_rule"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data[ATTR_ACTIVE_RULE]


class TouActiveRateTypeSensor(TouBaseSensor):
    _attr_name = "TOU Active Rate Type"
    _attr_unique_id = "tou_active_rate_type"

    @property
    def native_value(self) -> str:
        return self.coordinator.data[ATTR_ACTIVE_RATE_TYPE]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_ACTIVE_RATE_TYPE_ID: self.coordinator.data[ATTR_ACTIVE_RATE_TYPE_ID],
        }


class TouNextTransitionSensor(TouBaseSensor):
    _attr_name = "TOU Next Transition"
    _attr_unique_id = "tou_next_transition"

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data[ATTR_NEXT_TRANSITION]
