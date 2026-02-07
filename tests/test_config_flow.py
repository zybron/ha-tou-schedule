import pytest
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tou_schedule.const import (
    CONF_DEFAULT,
    CONF_ID,
    CONF_MONTHS,
    CONF_NAME,
    CONF_RATE,
    CONF_RATE_TYPE,
    CONF_RATE_TYPES,
    CONF_RULES,
    CONF_START,
    CONF_END,
    CONF_WEEKDAYS,
    DOMAIN,
)


@pytest.mark.asyncio
async def test_options_flow_add_rate_type(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "rate_types"}
    )
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "rate_type_add"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ID: "peak",
            CONF_NAME: "Peak",
            CONF_RATE: 0.25,
            CONF_DEFAULT: True,
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rate_types"
    assert entry.options[CONF_RATE_TYPES][0][CONF_ID] == "peak"
    assert entry.options[CONF_RATE_TYPES][0][CONF_DEFAULT] is True


@pytest.mark.asyncio
async def test_options_flow_add_rule_with_period(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ]
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "rules"}
    )
    assert result["type"] == FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "rule_add"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Weekday Peak",
            CONF_RATE_TYPE: "default",
            CONF_MONTHS: ["1", "2"],
            CONF_WEEKDAYS: ["1", "2", "3", "4", "5"],
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "period_add"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_START: "08:00",
            CONF_END: "10:00",
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "finish_rule"}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rules"
    assert entry.options[CONF_RULES]
    assert entry.options[CONF_RULES][0][CONF_PERIODS][0][CONF_START] == "08:00"
