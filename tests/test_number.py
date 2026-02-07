import pytest
from homeassistant.helpers import entity_registry as er

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tou_schedule.const import (
    CONF_DEFAULT,
    CONF_ID,
    CONF_NAME,
    CONF_RATE,
    CONF_RATE_TYPES,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_rate_type_number_updates_options(hass, enable_custom_integrations):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True},
                {CONF_ID: "peak", CONF_NAME: "Peak", CONF_RATE: 0.25, CONF_DEFAULT: False},
            ]
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id) is True
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    default_unique_id = f"{entry.entry_id}_rate_default"
    peak_unique_id = f"{entry.entry_id}_rate_peak"

    default_entity_id = registry.async_get_entity_id("number", DOMAIN, default_unique_id)
    peak_entity_id = registry.async_get_entity_id("number", DOMAIN, peak_unique_id)

    assert default_entity_id is not None
    assert peak_entity_id is not None

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": peak_entity_id, "value": 0.3},
        blocking=True,
    )

    assert entry.options[CONF_RATE_TYPES][1][CONF_RATE] == 0.3

    assert await hass.config_entries.async_unload(entry.entry_id) is True
    await hass.async_block_till_done()
