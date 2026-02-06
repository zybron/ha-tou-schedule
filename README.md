# TOU Schedule (Home Assistant Custom Integration)

A Home Assistant custom integration that provides a rule-based Time-of-Use (TOU) schedule with minute-level evaluation, UI-managed rate types and rules, and an EV Smart Charging–compatible price sensor.

## Features

- **Rule-based scheduling**: Seasonal/monthly and weekday recurrence with multiple daily periods per rule.
- **Minute-level evaluation**: Recomputed every minute; no precomputed future arrays stored.
- **Restart-safe**: State is derived from configuration on each update.
- **UI-managed configuration**: Rate types and rules are edited through the Options flow.
- **EV Smart Charging compatibility**: Price sensor with `prices_today` and `prices_tomorrow` attributes.
- **Automation triggers**: Custom trigger platform for rate/period entry/exit events.
- **Diagnostics**: Active rule, active rate type, and next transition sensors.
- **Binary sensors per rate type**: One `on` sensor for the active rate type.

## Installation

1. Copy the `custom_components/tou_schedule` directory into your Home Assistant configuration directory.
2. Restart Home Assistant.
3. Go to **Settings** → **Devices & Services** → **Add Integration** and search for **TOU Schedule**.

## Configuration

### Initial Setup

The config flow only creates the integration entry. All scheduling configuration is done in the Options flow.

### Options Flow

Go to **Settings** → **Devices & Services** → **TOU Schedule** → **Configure**.

You can:

- Add/edit/delete **Rate Types** (must have exactly one default).
- Add/edit/delete **Rules** (no overlaps allowed).
- Add/edit/delete **Periods** for each rule.

### Rate Types

Each rate type includes:

- `id`: Unique identifier (string).
- `name`: Friendly name.
- `rate`: Float (USD/kWh).
- `default`: Exactly one rate type must be marked default.

### Rules

Each rule includes:

- `id`: Unique identifier.
- `name`: Friendly name.
- `rate_type`: Rate type ID.
- `months`: Optional list of months (1–12). If empty, applies to all months.
- `weekdays`: Optional list of weekdays (0–6, Monday=0). If empty, applies to all days.
- `periods`: One or more daily time periods.

Periods have:

- `start`: 24-hour local time.
- `end`: 24-hour local time.

## Validation Rules

The integration enforces the following before saving configuration:

- At least one rate type exists.
- Exactly one default rate type exists.
- Period start time must be before end time.
- Periods within a rule cannot overlap.
- Rules cannot overlap across shared months/weekdays/time ranges.
- Rules must reference valid rate types.

## Entities

### Sensors

- `sensor.tou_ev_price` (EV Smart Charging)
  - **State**: current price (USD/kWh).
  - **Attributes**:
    - `prices_today`: 24 hourly entries for the local day.
    - `prices_tomorrow`: 24 hourly entries for the next local day.

- `sensor.tou_active_rule` (diagnostic)
- `sensor.tou_active_rate_type` (diagnostic)
- `sensor.tou_next_transition` (diagnostic)

### Binary Sensors

- `binary_sensor.tou_rate_<rate_type_id>`
  - `on` when the rate type is active.

## Trigger Platform

Use the `tou_schedule` trigger platform for minute-level events:

```yaml
trigger:
  - platform: tou_schedule
    event: rate_entered
    rate_type: peak
```

Supported events:

- `rate_entered`
- `rate_exited`
- `period_started`
- `period_ended`

`rate_type` is optional for filtering.

## EV Smart Charging Compatibility

`sensor.tou_ev_price` conforms to the EV Smart Charging price sensor contract:

- 24 hourly entries per day.
- ISO-8601 timestamps with Home Assistant local timezone.
- Recomputed every minute.

## Development

### Run tests

```bash
pytest -q
```

## Support

This is a custom integration and not part of Home Assistant Core. Use it at your own risk.
