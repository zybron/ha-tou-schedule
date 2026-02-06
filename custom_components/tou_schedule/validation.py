"""Validation helpers for TOU schedule."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any

from .const import (
    CONF_DEFAULT,
    CONF_END,
    CONF_ID,
    CONF_MONTHS,
    CONF_PERIODS,
    CONF_RATE_TYPE,
    CONF_START,
    CONF_WEEKDAYS,
)


@dataclass(frozen=True)
class ValidationResult:
    """Validation result."""

    valid: bool
    message: str | None = None


def _parse_time(value: str) -> time:
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    return time(hour=hour, minute=minute)


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def validate_rate_types(rate_types: list[dict[str, Any]]) -> ValidationResult:
    if not rate_types:
        return ValidationResult(False, "At least one rate type is required.")
    default_count = sum(1 for rate in rate_types if rate.get(CONF_DEFAULT))
    if default_count != 1:
        return ValidationResult(False, "Exactly one rate type must be default.")
    ids = [rate[CONF_ID] for rate in rate_types]
    if len(ids) != len(set(ids)):
        return ValidationResult(False, "Rate type IDs must be unique.")
    return ValidationResult(True)


def validate_rule_periods(rule: dict[str, Any]) -> ValidationResult:
    periods = rule.get(CONF_PERIODS, [])
    seen: list[tuple[int, int]] = []
    for period in periods:
        start = _parse_time(period[CONF_START])
        end = _parse_time(period[CONF_END])
        if _minutes(start) >= _minutes(end):
            return ValidationResult(False, "Period start must be before end.")
        start_min = _minutes(start)
        end_min = _minutes(end)
        for existing_start, existing_end in seen:
            if max(start_min, existing_start) < min(end_min, existing_end):
                return ValidationResult(False, "Periods within a rule cannot overlap.")
        seen.append((start_min, end_min))
    return ValidationResult(True)


def _rule_dimensions(rule: dict[str, Any]) -> tuple[set[int], set[int]]:
    months = set(rule.get(CONF_MONTHS, []))
    weekdays = set(rule.get(CONF_WEEKDAYS, []))
    if not months:
        months = set(range(1, 13))
    if not weekdays:
        weekdays = set(range(7))
    return months, weekdays


def validate_rule_overlaps(rules: list[dict[str, Any]]) -> ValidationResult:
    for index, rule in enumerate(rules):
        result = validate_rule_periods(rule)
        if not result.valid:
            return result
        rule_months, rule_weekdays = _rule_dimensions(rule)
        rule_periods = [
            (_minutes(_parse_time(period[CONF_START])), _minutes(_parse_time(period[CONF_END])))
            for period in rule.get(CONF_PERIODS, [])
        ]
        for other in rules[index + 1 :]:
            other_months, other_weekdays = _rule_dimensions(other)
            if not (rule_months & other_months) or not (rule_weekdays & other_weekdays):
                continue
            other_periods = [
                (
                    _minutes(_parse_time(period[CONF_START])),
                    _minutes(_parse_time(period[CONF_END])),
                )
                for period in other.get(CONF_PERIODS, [])
            ]
            for start, end in rule_periods:
                for other_start, other_end in other_periods:
                    if max(start, other_start) < min(end, other_end):
                        return ValidationResult(False, "Rules cannot overlap in time.")
    return ValidationResult(True)


def validate_rules(
    rules: list[dict[str, Any]],
    rate_types: list[dict[str, Any]],
) -> ValidationResult:
    rate_type_ids = {rate_type[CONF_ID] for rate_type in rate_types}
    for rule in rules:
        if rule.get(CONF_RATE_TYPE) not in rate_type_ids:
            return ValidationResult(False, "Rule references unknown rate type.")
    return validate_rule_overlaps(rules)
