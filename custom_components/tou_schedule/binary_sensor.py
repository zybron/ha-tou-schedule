"""Binary sensors for TOU schedule."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TouScheduleCoordinator, get_active_rate_type
from .const import CONF_ID, CONF_NAME, DOMAIN
from .helpers import get_options


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: TouScheduleCoordinator = hass.data[DOMAIN][entry.entry_id]
    rate_types, _ = get_options(entry)
    entities = [
        TouRateTypeBinarySensor(coordinator, entry, rate_type)
        for rate_type in rate_types
    ]
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
