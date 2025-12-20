# Unified Message System

The unified message system provides a consistent framework for all game content across three channels: **newswire**, **email**, and **ledger**.

## Quick Start

### 1. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
./run.sh  # Or: uvicorn main:app --reload
```

### 2. View Example Messages

The backend includes example messages in `backend/data/messages_example.json`. To use them:

```bash
# Copy example to active messages file
cp backend/data/messages_example.json backend/data/messages.json
```

### 3. Access the API

- **Get all messages**: `GET http://localhost:8000/api/messages`
- **Get by channel**: `GET http://localhost:8000/api/messages?channel=email`
- **Get specific message**: `GET http://localhost:8000/api/messages/{message_id}`

### 4. Admin API (Create/Update Messages)

All admin endpoints require authentication via `Authorization` header:

```bash
# Set admin token (or use default "change-me-in-production")
export ADMIN_TOKEN=your-secret-token

# Create a new message
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "email",
    "creation_trigger": "random",
    "creation_trigger_config": { "probability": 0.05 },
    "features": { "read_only": true, "requires_response": false },
    "impact": { "type": "none" },
    "content": {
      "sender": "System",
      "subject": "Test Email",
      "body": "This is a test email.",
      "type": "standard"
    },
    "active": true
  }'

# Update a message
curl -X PUT http://localhost:8000/api/messages/email-1 \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "active": false
  }'

# Delete (soft delete) a message
curl -X DELETE http://localhost:8000/api/messages/email-1 \
  -H "Authorization: Bearer your-secret-token"
```

## Message Structure

See `SCHEMA.md` for detailed schema documentation.

## Legacy Endpoints

The system maintains backward compatibility with existing endpoints:

- `GET /api/content/flavor` - Maps to newswire messages with `type: "flavor"`
- `GET /api/content/recruitment` - Returns recruitment configuration
- `GET /api/content/news` - Maps to newswire messages with news types

## Frontend Integration

The frontend `MessageManager` class (in `frontend/src/lib/game/MessageManager.js`) provides:

- `loadMessages()` - Fetch messages from API
- `checkRandomMessages()` - Check for random-triggered messages
- `triggerGameEvent(eventType, eventData)` - Trigger game event messages
- `applyImpact()` - Apply simulation impacts from newswire
- `handleEmailResponse()` - Handle user responses to emails

See `MIGRATION.md` for how to integrate this into the existing game.

## Example: Adding a New Email

1. **Create via API**:
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer your-secret-token" \
  -H "Content-Type: application/json" \
  -d @new_email.json
```

2. **Or edit `backend/data/messages.json` directly** (requires server restart)

3. **Frontend automatically picks it up** on next game start (if using `MessageManager.loadMessages()`)

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Get all active messages
curl http://localhost:8000/api/messages?active_only=true

# Get only email messages
curl http://localhost:8000/api/messages?channel=email

# Test admin endpoint (requires token)
curl -H "Authorization: Bearer change-me-in-production" \
  http://localhost:8000/api/messages
```

