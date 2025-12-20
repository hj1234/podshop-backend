# Pod Shop Content API

FastAPI backend for managing game content (flavor text, recruitment data, news templates).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set admin token (optional, defaults to "change-me-in-production"):
```bash
export ADMIN_TOKEN="your-secret-token-here"
```

3. Run the server:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### Content Endpoints (Public)
- `GET /api/content/flavor` - Get all active flavor text
- `GET /api/content/recruitment` - Get recruitment configuration
- `GET /api/content/news` - Get all active news templates

### Admin Endpoints (Requires Authorization)
All admin endpoints require an `Authorization` header with the admin token:
```
Authorization: Bearer your-secret-token-here
```

#### Flavor Text
- `GET /api/admin/flavor` - List all flavor text items
- `POST /api/admin/flavor` - Add new flavor text
- `PUT /api/admin/flavor/{item_id}` - Update flavor text
- `DELETE /api/admin/flavor/{item_id}` - Delete flavor text (soft delete)

#### Recruitment
- `GET /api/admin/recruitment` - Get recruitment config
- `PUT /api/admin/recruitment` - Update entire recruitment config
- `POST /api/admin/recruitment/specialisms` - Add specialism
- `POST /api/admin/recruitment/names` - Add name (first or last)
- `POST /api/admin/recruitment/bios` - Add bio

#### News Templates
- `GET /api/admin/news` - List all news templates
- `POST /api/admin/news` - Add new news template
- `PUT /api/admin/news/{template_id}` - Update news template
- `DELETE /api/admin/news/{template_id}` - Delete news template (soft delete)

## Example Usage

### Add Flavor Text
```bash
curl -X POST "http://localhost:8000/api/admin/flavor" \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "New flavor text here",
    "active": true
  }'
```

### Add News Template
```bash
curl -X POST "http://localhost:8000/api/admin/news" \
  -H "Authorization: Bearer your-secret-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Market Surge",
    "body": "Markets rally on positive news.",
    "impact": {"volatility_spike": 0.005},
    "type": "info",
    "probability": 0.03,
    "active": true
  }'
```

## Data Storage

Content is stored in JSON files in the `data/` directory:
- `data/flavor_text.json`
- `data/recruitment.json`
- `data/news_templates.json`

These files are created automatically when you use the admin API.

