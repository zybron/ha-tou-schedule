import pytest
from homeassistant import loader
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tou_schedule.const import (
    CONF_DEFAULT,
    CONF_END,
    CONF_ID,
    CONF_MONTHS,
    CONF_NAME,
    CONF_PERIODS,
    CONF_RATE,
    CONF_RATE_TYPE,
    CONF_RATE_TYPES,
    CONF_RULES,
    CONF_START,
    CONF_WEEKDAYS,
    DOMAIN,
)


async def _init_options_flow(hass, entry):
    entry.add_to_hass(hass)
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    return await hass.config_entries.options.async_init(entry.entry_id)


async def _goto_menu(hass, flow_id, step_id):
    return await hass.config_entries.options.async_configure(
        flow_id, {"next_step_id": step_id}
    )


@pytest.mark.asyncio
async def test_options_flow_add_rate_type(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})

    result = await _init_options_flow(hass, entry)
    assert result["type"] == FlowResultType.MENU

    result = await _goto_menu(hass, result["flow_id"], "rate_types")
    assert result["type"] == FlowResultType.MENU

    result = await _goto_menu(hass, result["flow_id"], "rate_type_add")
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
async def test_options_flow_add_rate_type_duplicate_id_error(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "peak", CONF_NAME: "Peak", CONF_RATE: 0.25, CONF_DEFAULT: True}
            ]
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rate_types")
    result = await _goto_menu(hass, result["flow_id"], "rate_type_add")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ID: "peak",
            CONF_NAME: "Peak 2",
            CONF_RATE: 0.3,
            CONF_DEFAULT: False,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "Rate type IDs must be unique."


@pytest.mark.asyncio
async def test_options_flow_edit_rate_type(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "offpeak", CONF_NAME: "Off Peak", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ]
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rate_types")
    result = await _goto_menu(hass, result["flow_id"], "rate_type_edit")
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "offpeak"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Super Off Peak",
            CONF_RATE: 0.08,
            CONF_DEFAULT: True,
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rate_types"
    assert entry.options[CONF_RATE_TYPES][0][CONF_NAME] == "Super Off Peak"
    assert entry.options[CONF_RATE_TYPES][0][CONF_RATE] == 0.08


@pytest.mark.asyncio
async def test_options_flow_delete_rate_type(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True},
                {CONF_ID: "peak", CONF_NAME: "Peak", CONF_RATE: 0.3, CONF_DEFAULT: False},
            ]
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rate_types")
    result = await _goto_menu(hass, result["flow_id"], "rate_type_delete")
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "peak"}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rate_types"
    assert len(entry.options[CONF_RATE_TYPES]) == 1
    assert entry.options[CONF_RATE_TYPES][0][CONF_ID] == "default"


@pytest.mark.asyncio
async def test_options_flow_delete_rate_type_used_by_rule_error(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ],
            CONF_RULES: [
                {
                    CONF_ID: "rule1",
                    CONF_NAME: "Rule 1",
                    CONF_RATE_TYPE: "default",
                    CONF_MONTHS: [],
                    CONF_WEEKDAYS: [],
                    CONF_PERIODS: [],
                }
            ],
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rate_types")
    result = await _goto_menu(hass, result["flow_id"], "rate_type_delete")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "default"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "Rate type is used by a rule."


@pytest.mark.asyncio
async def test_options_flow_rule_add_requires_rate_type(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_add")

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "Add a rate type before creating rules."


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

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_add")

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

    result = await _goto_menu(hass, result["flow_id"], "period_add")
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

    result = await _goto_menu(hass, result["flow_id"], "finish_rule")
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rules"
    assert entry.options[CONF_RULES]
    assert entry.options[CONF_RULES][0][CONF_PERIODS][0][CONF_START] == "08:00"


@pytest.mark.asyncio
async def test_options_flow_edit_rule(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ],
            CONF_RULES: [
                {
                    CONF_ID: "rule1",
                    CONF_NAME: "Rule 1",
                    CONF_RATE_TYPE: "default",
                    CONF_MONTHS: [1],
                    CONF_WEEKDAYS: [0],
                    CONF_PERIODS: [{CONF_START: "08:00", CONF_END: "10:00"}],
                }
            ],
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_edit")
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "rule1"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Updated Rule",
            CONF_RATE_TYPE: "default",
            CONF_MONTHS: ["2"],
            CONF_WEEKDAYS: ["1"],
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await _goto_menu(hass, result["flow_id"], "finish_rule")
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rules"
    assert entry.options[CONF_RULES][0][CONF_NAME] == "Updated Rule"
    assert entry.options[CONF_RULES][0][CONF_MONTHS] == [2]
    assert entry.options[CONF_RULES][0][CONF_WEEKDAYS] == [1]


@pytest.mark.asyncio
async def test_options_flow_delete_rule(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ],
            CONF_RULES: [
                {
                    CONF_ID: "rule1",
                    CONF_NAME: "Rule 1",
                    CONF_RATE_TYPE: "default",
                    CONF_MONTHS: [],
                    CONF_WEEKDAYS: [],
                    CONF_PERIODS: [],
                }
            ],
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_delete")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "rule1"}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rules"
    assert entry.options[CONF_RULES] == []


@pytest.mark.asyncio
async def test_options_flow_period_edit_and_delete(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ],
            CONF_RULES: [
                {
                    CONF_ID: "rule1",
                    CONF_NAME: "Rule 1",
                    CONF_RATE_TYPE: "default",
                    CONF_MONTHS: [],
                    CONF_WEEKDAYS: [],
                    CONF_PERIODS: [
                        {CONF_START: "08:00", CONF_END: "10:00"},
                        {CONF_START: "18:00", CONF_END: "20:00"},
                    ],
                }
            ],
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_edit")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "rule1"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Rule 1",
            CONF_RATE_TYPE: "default",
            CONF_MONTHS: [],
            CONF_WEEKDAYS: [],
        },
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await _goto_menu(hass, result["flow_id"], "period_edit")
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"index": "0"}
    )
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_START: "07:00", CONF_END: "09:00"},
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await _goto_menu(hass, result["flow_id"], "period_delete")
    assert result["type"] == FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"index": "1"}
    )
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rule_periods_menu"

    result = await _goto_menu(hass, result["flow_id"], "finish_rule")
    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "rules"
    assert entry.options[CONF_RULES][0][CONF_PERIODS][0][CONF_START] == "07:00"
    assert len(entry.options[CONF_RULES][0][CONF_PERIODS]) == 1


@pytest.mark.asyncio
async def test_options_flow_period_add_invalid_time(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            CONF_RATE_TYPES: [
                {CONF_ID: "default", CONF_NAME: "Default", CONF_RATE: 0.1, CONF_DEFAULT: True}
            ],
            CONF_RULES: [
                {
                    CONF_ID: "rule1",
                    CONF_NAME: "Rule 1",
                    CONF_RATE_TYPE: "default",
                    CONF_MONTHS: [],
                    CONF_WEEKDAYS: [],
                    CONF_PERIODS: [],
                }
            ],
        },
    )

    result = await _init_options_flow(hass, entry)
    result = await _goto_menu(hass, result["flow_id"], "rules")
    result = await _goto_menu(hass, result["flow_id"], "rule_edit")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_ID: "rule1"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Rule 1",
            CONF_RATE_TYPE: "default",
            CONF_MONTHS: [],
            CONF_WEEKDAYS: [],
        },
    )
    assert result["step_id"] == "rule_periods_menu"

    result = await _goto_menu(hass, result["flow_id"], "period_add")
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_START: "10:00", CONF_END: "08:00"},
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "Period start must be before end."
