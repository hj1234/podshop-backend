# Message Content Schema

This document describes the unified message structure for all game content (newswire, emails, ledger).

## Message Structure

```json
{
  "id": "unique-message-id",
  "channel": "newswire" | "email" | "ledger",
  "creation_trigger": "random" | "game_event",
  "creation_trigger_config": {
    // For random: { "probability": 0.03 }
    // For game_event: { "event_type": "leverage_threshold", "conditions": {...} }
  },
  "features": {
    "read_only": boolean,
    "requires_response": boolean
  },
  "impact": {
    "type": "none" | "simulation" | "user_action",
    "simulation": { ... },  // For simulation impacts
    "user_action": { ... }  // For user response impacts
  },
  "content": {
    // Channel-specific content structure
  },
  "active": boolean
}
```

## Channel: Newswire

**Features:**
- Always `read_only: true`
- Never `requires_response: true`

**Creation Triggers:**
- `random`: Probability-based (e.g., 0.03 = 3% chance per day)
- `game_event`: Triggered by specific game events

**Impact Types:**
- `none`: Informational only
- `simulation`: Affects market/fund simulation
  - `volatility_spike`: Number (e.g., 0.008)
  - `market_halt`: Boolean
  - `investor_equity_multiplier`: Number

**Content Structure:**
```json
{
  "type": "flavor" | "info" | "alert" | "breaking",
  "text": "Simple text message",  // For flavor type
  "headline": "News headline",   // For news type
  "body": "News body text"       // For news type
}
```

**Example:**
```json
{
  "id": "newswire-news-1",
  "channel": "newswire",
  "creation_trigger": "random",
  "creation_trigger_config": { "probability": 0.03 },
  "features": { "read_only": true },
  "impact": {
    "type": "simulation",
    "simulation": { "volatility_spike": 0.008 }
  },
  "content": {
    "type": "info",
    "headline": "Fed Signals Rate Cut",
    "body": "Federal Reserve hints at potential rate cuts..."
  },
  "active": true
}
```

## Channel: Email

**Features:**
- `read_only`: true for informational emails, false for actionable
- `requires_response`: true if user must respond (hire, fire, etc.)

**Creation Triggers:**
- `random`: Probability-based
- `game_event`: Triggered by game events (leverage, drawdown, etc.)

**Impact Types:**
- `none`: Informational emails
- `user_action`: Response-dependent impacts
  - `hire`: Action when user clicks "Hire"
  - `fire`: Action when user clicks "Fire"
  - `reject`: Action when user clicks "Reject"

**Content Structure:**
```json
{
  "sender": "Email sender name",
  "subject": "Email subject (supports {variable} interpolation)",
  "body": "Email body (supports {variable} interpolation)",
  "type": "standard" | "alert" | "recruitment",
  "data": {
    // Additional data passed to frontend
    // Supports {variable} interpolation
  }
}
```

**Example:**
```json
{
  "id": "email-drawdown-warning",
  "channel": "email",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "pod_drawdown",
    "conditions": { "drawdown": { "lte": -0.05 } }
  },
  "features": {
    "read_only": false,
    "requires_response": true
  },
  "impact": {
    "type": "user_action",
    "user_action": {
      "fire": { "type": "fire_pod" },
      "monitor": { "type": "none" }
    }
  },
  "content": {
    "sender": "Risk Management",
    "subject": "Drawdown Alert: {pod_name}",
    "body": "RISK MANAGEMENT ALERT\n\nPod: {pod_name}\nCurrent Drawdown: {drawdown_display}%",
    "type": "alert",
    "data": {
      "pod_id": "{pod_id}",
      "pod_name": "{pod_name}",
      "drawdown_display": "{drawdown_display}"
    }
  },
  "active": true
}
```

## Channel: Ledger

**Features:**
- Always `read_only: true`
- Never `requires_response: true`

**Creation Triggers:**
- Always `game_event` (never random)
- Common events: `month_end`, `pod_hired`, `pod_fired`, `bonus_paid`

**Impact Types:**
- Always `none` (ledger is read-only record)

**Content Structure:**
```json
{
  "description": "Transaction description (supports {variable} interpolation)",
  "amount": number | {
    "formula": "formula_string"  // e.g., "total_salaries / 12"
  },
  "affect_cash": boolean  // true = affects firm_cash, false = affects NAV only
}
```

**Example:**
```json
{
  "id": "ledger-monthly-salaries",
  "channel": "ledger",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "month_end"
  },
  "features": {
    "read_only": true
  },
  "impact": {
    "type": "none"
  },
  "content": {
    "description": "Monthly Salaries ({pod_count} pods)",
    "amount": {
      "formula": "total_salaries / 12"
    },
    "affect_cash": false
  },
  "active": true
}
```

## Game Events

Common game event types:
- `game_start`: When game initializes
- `month_end`: End of month processing
- `leverage_threshold`: When leverage crosses thresholds (8x, 10x, 12.5x, 15x)
- `pod_drawdown`: When pod drawdown exceeds threshold
- `pod_hired`: When user hires a pod
- `pod_fired`: When user fires a pod
- `margin_call`: When leverage hits 15x
- `insolvency`: When firm cash goes negative

## Conditions

Conditions allow messages to trigger only when specific criteria are met:

```json
{
  "conditions": {
    "leverage": { "gte": 8.0, "lt": 10.0 },
    "drawdown": { "lte": -0.05 },
    "pod_count": { "eq": 5 }
  }
}
```

Operators:
- `gte`: Greater than or equal
- `lte`: Less than or equal
- `gt`: Greater than
- `lt`: Less than
- `eq`: Equal

## Variable Interpolation

Messages support `{variable}` interpolation in:
- Email subject/body
- Ledger descriptions
- Content data fields

Variables are provided in `eventData` when triggering game events.

