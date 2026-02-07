"""Config flow for TOU schedule."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DEFAULT,
    CONF_END,
    CONF_ID,
    CONF_MONTHS,
    CONF_NAME,
    CONF_PERIODS,
    CONF_RATE,
    CONF_RATE_TYPE,
    CONF_RULES,
    CONF_START,
    CONF_WEEKDAYS,
    CONF_RATE_TYPES,
    DOMAIN,
)
from .validation import validate_rate_types, validate_rules

MONTH_OPTIONS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

WEEKDAY_OPTIONS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}

_LOGGER = logging.getLogger(__name__)



class TouScheduleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TOU schedule."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="TOU Schedule", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return TouScheduleOptionsFlow(config_entry)


class TouScheduleOptionsFlow(config_entries.OptionsFlow):
    """Options flow for TOU schedule."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._options = dict(config_entry.options)
        self._rate_type_id: str | None = None
        self._rule_id: str | None = None
        self._period_index: int | None = None

    @property
    def _rate_types(self) -> list[dict[str, Any]]:
        return list(self._options.get(CONF_RATE_TYPES, []))

    @property
    def _rules(self) -> list[dict[str, Any]]:
        return list(self._options.get(CONF_RULES, []))

    def _select_options(self, options: dict[int, str]) -> list[dict[str, Any]]:
        return [{"label": label, "value": value} for value, label in options.items()]

    def _log_step(self, step_id: str, user_input: dict[str, Any] | None) -> None:
        _LOGGER.debug(
            "Options flow step=%s entry_id=%s rule_id=%s rate_type_id=%s period_index=%s input=%s",
            step_id,
            self._config_entry.entry_id,
            self._rule_id,
            self._rate_type_id,
            self._period_index,
            user_input,
        )

    def _normalize_rate_types(self, rate_types: list[dict[str, Any]]) -> None:
        """Ensure exactly one default rate type is selected."""
        defaults = [rate for rate in rate_types if rate.get(CONF_DEFAULT)]
        if not rate_types:
            return
        if not defaults:
            rate_types[0][CONF_DEFAULT] = True
            return
        # If multiple defaults, keep the first and unset the rest.
        keep_id = defaults[0].get(CONF_ID)
        for rate in rate_types:
            if rate.get(CONF_ID) != keep_id and rate.get(CONF_DEFAULT):
                rate[CONF_DEFAULT] = False

    def _default_rate_type(self) -> dict[str, Any] | None:
        for rate in self._rate_types:
            if rate.get(CONF_DEFAULT):
                return rate
        return None

    async def _save_options(self, return_step: str = "init"):
        self._log_step("_save_options", {"return_step": return_step})
        self.hass.config_entries.async_update_entry(self._config_entry, options=self._options)
        if return_step == "rate_types":
            return await self.async_step_rate_types()
        if return_step == "rules":
            return await self.async_step_rules()
        return await self.async_step_init()

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        self._log_step("init", user_input)
        if not self._rate_types:
            return await self.async_step_default_rate()
        return self.async_show_menu(
            step_id="init",
            menu_options=["rate_types", "rules"],
        )

    async def async_step_default_rate(self, user_input: dict[str, Any] | None = None):
        self._log_step("default_rate", user_input)
        errors: dict[str, str] = {}
        if user_input is not None:
            rate_types = [
                {
                    CONF_ID: "default",
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_RATE: float(user_input[CONF_RATE]),
                    CONF_DEFAULT: True,
                }
            ]
            validation = validate_rate_types(rate_types)
            if validation.valid:
                self._options[CONF_RATE_TYPES] = rate_types
                return await self._save_options(return_step="init")
            errors["base"] = validation.message or "invalid"

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_RATE): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="default_rate", data_schema=schema, errors=errors)

    async def async_step_rate_types(self, user_input: dict[str, Any] | None = None):
        self._log_step("rate_types", user_input)
        return self.async_show_menu(
            step_id="rate_types",
            menu_options=["rate_type_add", "rate_type_edit", "rate_type_delete", "back"],
        )

    async def async_step_rate_type_add(self, user_input: dict[str, Any] | None = None):
        self._log_step("rate_type_add", user_input)
        errors: dict[str, str] = {}
        if user_input is not None:
            rate_types = self._rate_types
            rate_types.append(
                {
                    CONF_ID: user_input[CONF_ID],
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_RATE: float(user_input[CONF_RATE]),
                    CONF_DEFAULT: False,
                }
            )
            validation = validate_rate_types(rate_types)
            if validation.valid:
                self._options[CONF_RATE_TYPES] = rate_types
                return await self._save_options(return_step="rate_types")
            errors["base"] = validation.message or "invalid"

        schema = vol.Schema(
            {
                vol.Required(CONF_ID): str,
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_RATE): vol.Coerce(float),
            }
        )
        return self.async_show_form(step_id="rate_type_add", data_schema=schema, errors=errors)

    async def async_step_rate_type_edit(self, user_input: dict[str, Any] | None = None):
        self._log_step("rate_type_edit", user_input)
        if user_input is None:
            if not self._rate_types:
                return self.async_show_form(
                    step_id="rate_type_edit",
                    data_schema=vol.Schema({}),
                    errors={"base": "Add a rate type first."},
                )
            rate_type_ids = [
                {"label": rate[CONF_NAME], "value": rate[CONF_ID]} for rate in self._rate_types
            ]
            return self.async_show_form(
                step_id="rate_type_edit",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ID): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=rate_type_ids, mode=selector.SelectSelectorMode.DROPDOWN
                            )
                        )
                    }
                ),
            )
        if not self._rate_types:
            return await self.async_step_rate_types()
        self._rate_type_id = user_input[CONF_ID]
        return await self.async_step_rate_type_edit_detail()

    async def async_step_rate_type_edit_detail(self, user_input: dict[str, Any] | None = None):
        self._log_step("rate_type_edit_detail", user_input)
        rate_types = self._rate_types
        target = next(rate for rate in rate_types if rate[CONF_ID] == self._rate_type_id)
        errors: dict[str, str] = {}
        if user_input is not None:
            previous = dict(target)
            target.update(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_RATE: float(user_input[CONF_RATE]),
                }
            )
            validation = validate_rate_types(rate_types)
            if validation.valid:
                self._options[CONF_RATE_TYPES] = rate_types
                return await self._save_options(return_step="rate_types")
            errors["base"] = validation.message or "invalid"
            target.update(previous)

        schema_fields = {
            vol.Required(CONF_NAME, default=target[CONF_NAME]): str,
            vol.Required(CONF_RATE, default=target[CONF_RATE]): vol.Coerce(float),
        }
        schema = vol.Schema(schema_fields)
        return self.async_show_form(step_id="rate_type_edit_detail", data_schema=schema, errors=errors)

    async def async_step_rate_type_delete(self, user_input: dict[str, Any] | None = None):
        self._log_step("rate_type_delete", user_input)
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._rate_types:
                return await self.async_step_rate_types()
            rate_types = self._rate_types
            rate_type_id = user_input[CONF_ID]
            rules = self._rules
            if not rules:
                rules = list(self._config_entry.options.get(CONF_RULES, []))
            if any(rule[CONF_RATE_TYPE] == rate_type_id for rule in rules):
                errors["base"] = "Rate type is used by a rule."
            elif any(rate.get(CONF_DEFAULT) and rate.get(CONF_ID) == rate_type_id for rate in rate_types):
                errors["base"] = "Default rate type cannot be deleted."
            else:
                rate_types = [rate for rate in rate_types if rate[CONF_ID] != rate_type_id]
                self._normalize_rate_types(rate_types)
                validation = validate_rate_types(rate_types)
                if validation.valid:
                    self._options[CONF_RATE_TYPES] = rate_types
                    return await self._save_options(return_step="rate_types")
                errors["base"] = validation.message or "invalid"

        if not self._rate_types:
            return self.async_show_form(
                step_id="rate_type_delete",
                data_schema=vol.Schema({}),
                errors={"base": "Add a rate type first."},
            )
        rate_type_ids = [
            {"label": rate[CONF_NAME], "value": rate[CONF_ID]} for rate in self._rate_types
        ]
        return self.async_show_form(
            step_id="rate_type_delete",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=rate_type_ids, mode=selector.SelectSelectorMode.DROPDOWN
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_rules(self, user_input: dict[str, Any] | None = None):
        self._log_step("rules", user_input)
        return self.async_show_menu(
            step_id="rules",
            menu_options=["rule_add", "rule_edit", "rule_delete", "back"],
        )

    async def async_step_rule_add(self, user_input: dict[str, Any] | None = None):
        self._log_step("rule_add", user_input)
        errors: dict[str, str] = {}
        if not self._rate_types:
            return self.async_show_form(
                step_id="rule_add",
                data_schema=vol.Schema({}),
                errors={"base": "Add a rate type before creating rules."},
            )
        if user_input is not None:
            rule_id = user_input.get(CONF_ID) or str(uuid.uuid4())
            rule = {
                CONF_ID: rule_id,
                CONF_NAME: user_input[CONF_NAME],
                CONF_RATE_TYPE: user_input[CONF_RATE_TYPE],
                CONF_MONTHS: [int(value) for value in user_input.get(CONF_MONTHS, [])],
                CONF_WEEKDAYS: [int(value) for value in user_input.get(CONF_WEEKDAYS, [])],
                CONF_PERIODS: [],
            }
            rules = self._rules + [rule]
            validation = validate_rules(rules, self._rate_types)
            if validation.valid:
                self._options[CONF_RULES] = rules
                self._rule_id = rule_id
                return await self.async_step_rule_periods_menu()
            errors["base"] = validation.message or "invalid"

        schema = self._rule_schema()
        return self.async_show_form(step_id="rule_add", data_schema=schema, errors=errors)

    async def async_step_rule_edit(self, user_input: dict[str, Any] | None = None):
        self._log_step("rule_edit", user_input)
        if user_input is None:
            if not self._rules:
                return self.async_show_form(
                    step_id="rule_edit",
                    data_schema=vol.Schema({}),
                    errors={"base": "Add a rule first."},
                )
            rule_ids = [
                {"label": rule[CONF_NAME], "value": rule[CONF_ID]} for rule in self._rules
            ]
            return self.async_show_form(
                step_id="rule_edit",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_ID): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=rule_ids, mode=selector.SelectSelectorMode.DROPDOWN
                            )
                        )
                    }
                ),
            )
        if not self._rules:
            return await self.async_step_rules()
        self._rule_id = user_input[CONF_ID]
        return await self.async_step_rule_edit_detail()

    async def async_step_rule_edit_detail(self, user_input: dict[str, Any] | None = None):
        self._log_step("rule_edit_detail", user_input)
        rules = self._rules
        rule = next(rule for rule in rules if rule[CONF_ID] == self._rule_id)
        errors: dict[str, str] = {}
        if user_input is not None:
            previous = dict(rule)
            rule.update(
                {
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_RATE_TYPE: user_input[CONF_RATE_TYPE],
                    CONF_MONTHS: [int(value) for value in user_input.get(CONF_MONTHS, [])],
                    CONF_WEEKDAYS: [int(value) for value in user_input.get(CONF_WEEKDAYS, [])],
                }
            )
            validation = validate_rules(rules, self._rate_types)
            if validation.valid:
                self._options[CONF_RULES] = rules
                return await self.async_step_rule_periods_menu()
            errors["base"] = validation.message or "invalid"
            rule.update(previous)

        schema = self._rule_schema(defaults=rule)
        return self.async_show_form(step_id="rule_edit_detail", data_schema=schema, errors=errors)

    async def async_step_rule_delete(self, user_input: dict[str, Any] | None = None):
        self._log_step("rule_delete", user_input)
        if user_input is not None:
            if not self._rules:
                return await self.async_step_rules()
            rule_id = user_input[CONF_ID]
            self._options[CONF_RULES] = [rule for rule in self._rules if rule[CONF_ID] != rule_id]
            return await self._save_options(return_step="rules")

        if not self._rules:
            return self.async_show_form(
                step_id="rule_delete",
                data_schema=vol.Schema({}),
                errors={"base": "Add a rule first."},
            )
        rule_ids = [
            {"label": rule[CONF_NAME], "value": rule[CONF_ID]} for rule in self._rules
        ]
        return self.async_show_form(
            step_id="rule_delete",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=rule_ids, mode=selector.SelectSelectorMode.DROPDOWN
                        )
                    )
                }
            ),
        )

    async def async_step_rule_periods_menu(self, user_input: dict[str, Any] | None = None):
        self._log_step("rule_periods_menu", user_input)
        return self.async_show_menu(
            step_id="rule_periods_menu",
            menu_options=["period_add", "period_edit", "period_delete", "finish_rule", "back"],
        )

    async def async_step_finish_rule(self, user_input: dict[str, Any] | None = None):
        self._log_step("finish_rule", user_input)
        return await self._save_options(return_step="rules")

    async def async_step_period_add(self, user_input: dict[str, Any] | None = None):
        self._log_step("period_add", user_input)
        return await self._period_form("period_add", user_input)

    async def async_step_period_edit(self, user_input: dict[str, Any] | None = None):
        self._log_step("period_edit", user_input)
        if user_input is None:
            rule = self._get_rule()
            periods = rule.get(CONF_PERIODS, [])
            if not periods:
                return await self.async_step_rule_periods_menu()
            period_options = {
                str(index): f"{period[CONF_START]}-{period[CONF_END]}"
                for index, period in enumerate(periods)
            }
            return self.async_show_form(
                step_id="period_edit",
                data_schema=vol.Schema(
                    {
                        vol.Required("index"): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    {"label": label, "value": value}
                                    for value, label in period_options.items()
                                ],
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        )
                    }
                ),
            )
        self._period_index = int(user_input["index"])
        return await self._period_form("period_edit_detail", None)

    async def async_step_period_edit_detail(self, user_input: dict[str, Any] | None = None):
        self._log_step("period_edit_detail", user_input)
        return await self._period_form("period_edit_detail", user_input)

    async def async_step_period_delete(self, user_input: dict[str, Any] | None = None):
        self._log_step("period_delete", user_input)
        rule = self._get_rule()
        if user_input is not None:
            index = int(user_input["index"])
            removed = rule[CONF_PERIODS].pop(index)
            validation = validate_rules(self._rules, self._rate_types)
            if validation.valid:
                return await self.async_step_rule_periods_menu()
            rule[CONF_PERIODS].insert(index, removed)

        periods = rule.get(CONF_PERIODS, [])
        if not periods:
            return await self.async_step_rule_periods_menu()
        period_options = {
            str(index): f"{period[CONF_START]}-{period[CONF_END]}"
            for index, period in enumerate(periods)
        }
        return self.async_show_form(
            step_id="period_delete",
            data_schema=vol.Schema(
                {
                    vol.Required("index"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"label": label, "value": value}
                                for value, label in period_options.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_back(self, user_input: dict[str, Any] | None = None):
        self._log_step("back", user_input)
        return await self.async_step_init()

    def _rule_schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        defaults = defaults or {}
        rate_types = self._rate_types
        rate_type_options = [
            {"label": rate[CONF_NAME], "value": rate[CONF_ID]} for rate in rate_types
        ]
        month_options = [
            {"label": f"{value:02d} - {label}", "value": str(value)}
            for value, label in MONTH_OPTIONS.items()
        ]
        weekday_options = [
            {"label": f"{value + 1} - {label}", "value": str(value)}
            for value, label in WEEKDAY_OPTIONS.items()
        ]
        default_months = [str(value) for value in defaults.get(CONF_MONTHS, [])]
        default_weekdays = [str(value) for value in defaults.get(CONF_WEEKDAYS, [])]
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, "")): str,
                vol.Required(CONF_RATE_TYPE, default=defaults.get(CONF_RATE_TYPE)): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=rate_type_options, mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(CONF_MONTHS, default=default_months): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=month_options, multiple=True, mode=selector.SelectSelectorMode.LIST
                    )
                ),
                vol.Optional(CONF_WEEKDAYS, default=default_weekdays): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=weekday_options, multiple=True, mode=selector.SelectSelectorMode.LIST
                    )
                ),
            }
        )

    def _get_rule(self) -> dict[str, Any]:
        return next(rule for rule in self._rules if rule[CONF_ID] == self._rule_id)

    async def _period_form(self, step_id: str, user_input: dict[str, Any] | None):
        rule = self._get_rule()
        periods = list(rule.get(CONF_PERIODS, []))
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if step_id == "period_edit_detail" and self._period_index is not None:
            defaults = periods[self._period_index]
        if user_input is not None:
            new_period = {CONF_START: user_input[CONF_START], CONF_END: user_input[CONF_END]}
            previous_periods = list(periods)
            if step_id == "period_add":
                periods.append(new_period)
            else:
                periods[self._period_index] = new_period
            rule[CONF_PERIODS] = periods
            validation = validate_rules(self._rules, self._rate_types)
            if validation.valid:
                return await self.async_step_rule_periods_menu()
            errors["base"] = validation.message or "invalid"
            rule[CONF_PERIODS] = previous_periods

        schema = vol.Schema(
            {
                vol.Required(CONF_START, default=defaults.get(CONF_START, "00:00")): selector.TimeSelector(),
                vol.Required(CONF_END, default=defaults.get(CONF_END, "00:00")): selector.TimeSelector(),
            }
        )
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

    async def _async_save_options(self):
        return self.async_create_entry(title="", data=self._options)
