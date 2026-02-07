"""Constants for the TOU schedule integration."""

DOMAIN = "tou_schedule"
PLATFORMS = ["sensor", "binary_sensor"]

CONF_RATE_TYPES = "rate_types"
CONF_RULES = "rules"

CONF_ID = "id"
CONF_NAME = "name"
CONF_RATE = "rate"
CONF_DEFAULT = "default"
CONF_RATE_TYPE = "rate_type"
CONF_MONTHS = "months"
CONF_WEEKDAYS = "weekdays"
CONF_PERIODS = "periods"
CONF_START = "start"
CONF_END = "end"

TRIGGER_RATE_ENTERED = "rate_entered"
TRIGGER_RATE_EXITED = "rate_exited"
TRIGGER_PERIOD_STARTED = "period_started"
TRIGGER_PERIOD_ENDED = "period_ended"

ATTR_PRICES_TODAY = "prices_today"
ATTR_PRICES_TOMORROW = "prices_tomorrow"
ATTR_ACTIVE_RULE = "active_rule_id"
ATTR_ACTIVE_RATE_TYPE = "active_rate_type"
ATTR_ACTIVE_RATE_TYPE_ID = "active_rate_type_id"
ATTR_NEXT_TRANSITION = "next_transition"
