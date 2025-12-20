# Migration Guide: Existing Features to Unified Message System

This guide shows how existing game features map to the new unified message framework.

## Overview

The new system unifies all game content (newswire, emails, ledger) into a single structure with:
- **Channels**: `newswire`, `email`, `ledger`
- **Creation Triggers**: `random` or `game_event`
- **Features**: `read_only`, `requires_response`
- **Impact**: `none`, `simulation`, or `user_action`

## Existing Features Mapping

### 1. Newswire Messages

#### Flavor Text (Random)
**Old**: Hardcoded in `EventSystem.js`, triggered randomly (5% probability)

**New**:
```json
{
  "id": "newswire-flavor-1",
  "channel": "newswire",
  "creation_trigger": "random",
  "creation_trigger_config": { "probability": 0.05 },
  "features": { "read_only": true },
  "impact": { "type": "none" },
  "content": {
    "type": "flavor",
    "text": "Analyst spotted crying in the bathroom."
  },
  "active": true
}
```

#### Market News (Random)
**Old**: Templates in `NewsWire.js`, checked daily with probability

**New**:
```json
{
  "id": "newswire-news-1",
  "channel": "newswire",
  "creation_trigger": "random",
  "creation_trigger_config": { "probability": 0.03 },
  "features": { "read_only": true },
  "impact": {
    "type": "simulation",
    "simulation": {
      "volatility_spike": 0.008
    }
  },
  "content": {
    "type": "info",
    "headline": "Fed Signals Rate Cut",
    "body": "Federal Reserve hints at potential rate cuts..."
  },
  "active": true
}
```

#### Holiday Events (Game Event)
**Old**: Calendar-based in `EventSystem.js`

**New**:
```json
{
  "id": "newswire-holiday-1",
  "channel": "newswire",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "holiday",
    "conditions": { "date": { "eq": "2024-12-25" } }
  },
  "features": { "read_only": true },
  "impact": {
    "type": "simulation",
    "simulation": { "market_halt": true }
  },
  "content": {
    "type": "info",
    "headline": "Market Holiday: Christmas",
    "body": "Markets are closed today."
  },
  "active": true
}
```

### 2. Email Messages

#### Welcome Leverage Email (Game Event)
**Old**: `createWelcomeLeverageEmail()` in `Email.js`, triggered on first leverage use

**New**:
```json
{
  "id": "email-welcome-leverage",
  "channel": "email",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "first_leverage_use"
  },
  "features": {
    "read_only": true,
    "requires_response": false
  },
  "impact": { "type": "none" },
  "content": {
    "sender": "Goldman Sachs Prime",
    "subject": "Welcome to Prime Services",
    "body": "Dear Client,\n\nWe noticed you have begun utilizing your margin facility...",
    "type": "standard"
  },
  "active": true
}
```

#### Leverage Warning Emails (Game Event)
**Old**: `createWarningEmail(level)` in `Email.js`, triggered at 8x, 10x, 12.5x, 15x

**New** (8x example):
```json
{
  "id": "email-leverage-warning-8x",
  "channel": "email",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "leverage_threshold",
    "conditions": {
      "leverage": { "gte": 8.0, "lt": 10.0 }
    }
  },
  "features": {
    "read_only": true,
    "requires_response": false
  },
  "impact": { "type": "none" },
  "content": {
    "sender": "GS Risk Desk",
    "subject": "Risk Alert: Elevated Leverage",
    "body": "Dear Client,\n\nYour effective leverage has crossed 8.0x...",
    "type": "alert"
  },
  "active": true
}
```

**New** (15x margin call):
```json
{
  "id": "email-margin-call",
  "channel": "email",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "leverage_threshold",
    "conditions": {
      "leverage": { "gte": 15.0 }
    }
  },
  "features": {
    "read_only": true,
    "requires_response": false
  },
  "impact": {
    "type": "simulation",
    "simulation": { "game_over": true, "reason": "margin_call" }
  },
  "content": {
    "sender": "GS Risk Desk",
    "subject": "MARGIN CALL: AUTOMATIC LIQUIDATION",
    "body": "MARGIN CALL EXECUTED\n\nYour effective leverage has exceeded 15.0x...",
    "type": "alert"
  },
  "active": true
}
```

#### Recruitment Emails (Random)
**Old**: `checkRecruitment()` in `EmailManager.js`, 7.2% probability

**New**:
```json
{
  "id": "email-recruitment",
  "channel": "email",
  "creation_trigger": "random",
  "creation_trigger_config": { "probability": 0.072 },
  "features": {
    "read_only": false,
    "requires_response": true
  },
  "impact": {
    "type": "user_action",
    "user_action": {
      "hire": { "type": "hire_pod" },
      "reject": { "type": "none" }
    }
  },
  "content": {
    "sender": "Headhunter",
    "subject": "Candidate: {candidate_name} ({specialism})",
    "body": "Hey,\n\nThought you might like {candidate_name}'s profile...",
    "type": "recruitment",
    "data": {
      "candidate_name": "{candidate_name}",
      "specialism": "{specialism}",
      "alpha_display": "{alpha_display}",
      "beta": "{beta}",
      "last_drawdown": "{last_drawdown}",
      "lifetime_pnl": "{lifetime_pnl}",
      "signing_bonus": "{signing_bonus}",
      "salary": "{salary}",
      "pnl_cut": "{pnl_cut}",
      "bio": "{bio}"
    }
  },
  "active": true
}
```

#### Drawdown Warning Emails (Game Event)
**Old**: `createDrawdownWarningEmail()` in `Email.js`, triggered when pod drawdown <= -5%

**New**:
```json
{
  "id": "email-drawdown-warning",
  "channel": "email",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "pod_drawdown",
    "conditions": {
      "drawdown": { "lte": -0.05 }
    }
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
    "body": "RISK MANAGEMENT ALERT\n\nPod: {pod_name}\nCurrent Drawdown: {drawdown_display}%...",
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

### 3. Ledger Entries

#### Monthly Salaries (Game Event)
**Old**: `processMonthEnd()` in `Fund.js`, hardcoded description

**New**:
```json
{
  "id": "ledger-monthly-salaries",
  "channel": "ledger",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "month_end"
  },
  "features": { "read_only": true },
  "impact": { "type": "none" },
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

#### Management Fee (Game Event)
**Old**: `processMonthEnd()` in `Fund.js`, hardcoded description

**New**:
```json
{
  "id": "ledger-management-fee",
  "channel": "ledger",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "month_end"
  },
  "features": { "read_only": true },
  "impact": { "type": "none" },
  "content": {
    "description": "Management Fee (2% annual)",
    "amount": {
      "formula": "investor_equity * 0.02 / 12"
    },
    "affect_cash": true
  },
  "active": true
}
```

#### Sign-on Bonus (Game Event)
**Old**: Triggered when pod is hired, hardcoded in `GameState.js`

**New**:
```json
{
  "id": "ledger-sign-on-bonus",
  "channel": "ledger",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "pod_hired"
  },
  "features": { "read_only": true },
  "impact": { "type": "none" },
  "content": {
    "description": "Sign-on Bonus: {pod_name}",
    "amount": {
      "formula": "-signing_bonus"
    },
    "affect_cash": true
  },
  "active": true
}
```

#### Bonus Payouts (Game Event)
**Old**: `processMonthEnd()` in `Fund.js`, per-pod calculation

**New**:
```json
{
  "id": "ledger-bonus-payout",
  "channel": "ledger",
  "creation_trigger": "game_event",
  "creation_trigger_config": {
    "event_type": "month_end",
    "conditions": {
      "monthly_profit": { "gt": 0 }
    }
  },
  "features": { "read_only": true },
  "impact": { "type": "none" },
  "content": {
    "description": "Bonus Payout: {pod_name}",
    "amount": {
      "formula": "-monthly_profit * pnl_cut / 100"
    },
    "affect_cash": false
  },
  "active": true
}
```

## Implementation Strategy

### Phase 1: Backend Setup (Complete)
- ✅ Create unified message API
- ✅ Create example messages JSON
- ✅ Document schema

### Phase 2: Frontend Integration (Next Steps)
1. **Gradual Migration**: Keep existing systems working, add `MessageManager` alongside
2. **Event Triggering**: Update `GameState.step()` to trigger game events:
   ```javascript
   // Instead of: this.email_manager.sendLeverageWarning(level)
   // Do: this.message_manager.triggerGameEvent('leverage_threshold', { leverage: this.fund.effective_leverage })
   ```
3. **Response Handling**: Update email response handlers to use `MessageManager.handleEmailResponse()`
4. **Content Loading**: Load messages from API on game start

### Phase 3: Full Migration
1. Remove hardcoded email/news/ledger creation
2. Use `MessageManager` exclusively
3. Remove legacy `EmailManager`, `NewsWire`, `Ledger` creation methods

## Benefits

1. **Easy Content Creation**: Add new messages via API without code changes
2. **Consistent Structure**: All content follows same pattern
3. **Flexible Triggers**: Complex conditions for when messages appear
4. **Dynamic Content**: Variable interpolation for personalized messages
5. **Impact System**: Clear separation of informational vs. actionable content

