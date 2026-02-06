"""Scheduling helpers for TOU schedule."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any, Iterable

from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEFAULT,
    CONF_END,
    CONF_ID,
    CONF_MONTHS,
    CONF_PERIODS,
    CONF_RATE,
    CONF_RATE_TYPE,
    CONF_START,
    CONF_WEEKDAYS,
)


@dataclass(frozen=True)
class ActiveRate:
    """Active rate data."""

    rate_type_id: str
    rate_type_name: str
    rate: float
    rule_id: str | None


def _parse_time(value: str) -> time:
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    return time(hour=hour, minute=minute)


def _time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def _periods(rule: dict[str, Any]) -> Iterable[tuple[time, time]]:
    for period in rule.get(CONF_PERIODS, []):
        yield _parse_time(period[CONF_START]), _parse_time(period[CONF_END])


def _matches_month(rule: dict[str, Any], now: datetime) -> bool:
    months = rule.get(CONF_MONTHS, [])
    if not months:
        return True
    return now.month in months


def _matches_weekday(rule: dict[str, Any], now: datetime) -> bool:
    weekdays = rule.get(CONF_WEEKDAYS, [])
    if not weekdays:
        return True
    return now.weekday() in weekdays


def is_rule_active(rule: dict[str, Any], now: datetime) -> bool:
    """Return True if a rule applies at the given datetime."""
    if not _matches_month(rule, now) or not _matches_weekday(rule, now):
        return False
    now_minutes = _time_to_minutes(now.timetz())
    for start, end in _periods(rule):
        if _time_to_minutes(start) <= now_minutes < _time_to_minutes(end):
            return True
    return False


def find_active_rule(rules: list[dict[str, Any]], now: datetime) -> dict[str, Any] | None:
    """Return the active rule or None."""
    for rule in rules:
        if is_rule_active(rule, now):
            return rule
    return None


def default_rate_type(rate_types: list[dict[str, Any]]) -> dict[str, Any]:
    for rate_type in rate_types:
        if rate_type.get(CONF_DEFAULT):
            return rate_type
    raise ValueError("No default rate type configured")


def rate_type_by_id(rate_types: list[dict[str, Any]], rate_type_id: str) -> dict[str, Any]:
    for rate_type in rate_types:
        if rate_type[CONF_ID] == rate_type_id:
            return rate_type
    raise ValueError(f"Unknown rate type: {rate_type_id}")


def get_active_rate(
    rules: list[dict[str, Any]],
    rate_types: list[dict[str, Any]],
    now: datetime,
) -> ActiveRate:
    """Return the active rate at a datetime."""
    active_rule = find_active_rule(rules, now)
    if active_rule is None:
        default = default_rate_type(rate_types)
        return ActiveRate(
            rate_type_id=default[CONF_ID],
            rate_type_name=default["name"],
            rate=float(default[CONF_RATE]),
            rule_id=None,
        )

    rate_type = rate_type_by_id(rate_types, active_rule[CONF_RATE_TYPE])
    return ActiveRate(
        rate_type_id=rate_type[CONF_ID],
        rate_type_name=rate_type["name"],
        rate=float(rate_type[CONF_RATE]),
        rule_id=active_rule[CONF_ID],
    )


def build_prices_for_day(
    start: datetime,
    rules: list[dict[str, Any]],
    rate_types: list[dict[str, Any]],
    tzinfo,
) -> list[dict[str, Any]]:
    """Build hourly prices for a given local day."""
    prices: list[dict[str, Any]] = []
    current = start.replace(minute=0, second=0, microsecond=0, tzinfo=tzinfo)
    for _ in range(24):
        rate = get_active_rate(rules, rate_types, current)
        prices.append(
            {
                "time": current.isoformat(),
                "price": rate.rate,
            }
        )
        current += timedelta(hours=1)
    return prices


def next_transition(
    rules: list[dict[str, Any]],
    rate_types: list[dict[str, Any]],
    now: datetime,
    limit_hours: int = 48,
) -> datetime | None:
    """Return the next transition datetime if any within a window."""
    baseline = get_active_rate(rules, rate_types, now)
    current = now.replace(second=0, microsecond=0)
    for _ in range(limit_hours * 60):
        current += timedelta(minutes=1)
        if get_active_rate(rules, rate_types, current) != baseline:
            return current
    return None


def local_midnight(now: datetime) -> datetime:
    """Return local midnight for the datetime."""
    local = dt_util.as_local(now)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)
