from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
import os

router = APIRouter()

# Path to data files
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Simple token authentication
# In production, use proper authentication (JWT, OAuth, etc.)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me-in-production")

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify admin token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Support both "Bearer token" and just "token"
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    return True

def _load_json_file(filename: str, default: Any = None):
    """Load JSON file or return default"""
    file_path = DATA_DIR / filename
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading {filename}: {str(e)}")
    return default if default is not None else []

def _save_json_file(filename: str, data: Any):
    """Save data to JSON file"""
    file_path = DATA_DIR / filename
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error writing {filename}: {str(e)}")

# ===== FLAVOR TEXT ENDPOINTS =====

@router.get("/flavor")
async def list_flavor_text(_: bool = Depends(verify_token)) -> List[Dict[str, Any]]:
    """List all flavor text items"""
    return _load_json_file("flavor_text.json", [])

@router.post("/flavor")
async def add_flavor_text(item: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Add new flavor text item"""
    items = _load_json_file("flavor_text.json", [])
    
    # Generate ID if not provided
    if "id" not in item:
        item["id"] = f"flavor-{len(items) + 1}"
    
    # Set defaults
    if "active" not in item:
        item["active"] = True
    
    items.append(item)
    _save_json_file("flavor_text.json", items)
    
    return {"status": "added", "item": item}

@router.put("/flavor/{item_id}")
async def update_flavor_text(item_id: str, updates: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Update existing flavor text item"""
    items = _load_json_file("flavor_text.json", [])
    
    found = False
    for item in items:
        if item.get("id") == item_id:
            item.update(updates)
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Flavor text item {item_id} not found")
    
    _save_json_file("flavor_text.json", items)
    return {"status": "updated", "item_id": item_id}

@router.delete("/flavor/{item_id}")
async def delete_flavor_text(item_id: str, _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Delete flavor text item (soft delete by setting active=false)"""
    items = _load_json_file("flavor_text.json", [])
    
    found = False
    for item in items:
        if item.get("id") == item_id:
            item["active"] = False
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Flavor text item {item_id} not found")
    
    _save_json_file("flavor_text.json", items)
    return {"status": "deleted", "item_id": item_id}

# ===== RECRUITMENT CANDIDATES ENDPOINTS =====

@router.get("/recruitment/candidates")
async def list_candidates(_: bool = Depends(verify_token)) -> List[Dict[str, Any]]:
    """List all recruitment candidates"""
    return _load_json_file("recruitment_candidates.json", [])

@router.post("/recruitment/candidates")
async def add_candidate(candidate: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Add a new recruitment candidate"""
    candidates = _load_json_file("recruitment_candidates.json", [])
    
    # Validate required fields
    required_fields = ["specialism", "beta_mu", "beta_sigma", "vol_range", "first_name", "last_name", "bio"]
    for field in required_fields:
        if field not in candidate:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Generate ID if not provided
    if "id" not in candidate:
        candidate["id"] = f"candidate-{len(candidates) + 1}"
    
    # Set defaults
    if "active" not in candidate:
        candidate["active"] = True
    
    candidates.append(candidate)
    _save_json_file("recruitment_candidates.json", candidates)
    
    return {"status": "added", "candidate": candidate}

@router.put("/recruitment/candidates/{candidate_id}")
async def update_candidate(candidate_id: str, updates: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Update an existing recruitment candidate"""
    candidates = _load_json_file("recruitment_candidates.json", [])
    
    found = False
    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            candidate.update(updates)
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    
    _save_json_file("recruitment_candidates.json", candidates)
    return {"status": "updated", "candidate_id": candidate_id}

@router.delete("/recruitment/candidates/{candidate_id}")
async def delete_candidate(candidate_id: str, _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Delete a candidate (soft delete by setting active=false)"""
    candidates = _load_json_file("recruitment_candidates.json", [])
    
    found = False
    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            candidate["active"] = False
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found")
    
    _save_json_file("recruitment_candidates.json", candidates)
    return {"status": "deleted", "candidate_id": candidate_id}

# ===== LEGACY RECRUITMENT ENDPOINTS (for backward compatibility) =====

@router.get("/recruitment")
async def get_recruitment_data(_: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Legacy endpoint - returns recruitment configuration in old format"""
    return _load_json_file("recruitment.json", {})

@router.put("/recruitment")
async def update_recruitment_data(data: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Legacy endpoint - update recruitment configuration in old format"""
    _save_json_file("recruitment.json", data)
    return {"status": "updated", "data": data}

# ===== NEWS TEMPLATES ENDPOINTS =====

@router.get("/news")
async def list_news_templates(_: bool = Depends(verify_token)) -> List[Dict[str, Any]]:
    """List all news templates"""
    return _load_json_file("news_templates.json", [])

@router.post("/news")
async def add_news_template(template: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Add new news template"""
    templates = _load_json_file("news_templates.json", [])
    
    # Generate ID if not provided
    if "id" not in template:
        template["id"] = f"news-{len(templates) + 1}"
    
    # Set defaults
    if "active" not in template:
        template["active"] = True
    if "impact" not in template:
        template["impact"] = {}
    if "type" not in template:
        template["type"] = "info"
    if "probability" not in template:
        template["probability"] = 0.03
    
    templates.append(template)
    _save_json_file("news_templates.json", templates)
    
    return {"status": "added", "template": template}

@router.put("/news/{template_id}")
async def update_news_template(template_id: str, updates: Dict[str, Any], _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Update existing news template"""
    templates = _load_json_file("news_templates.json", [])
    
    found = False
    for template in templates:
        if template.get("id") == template_id:
            template.update(updates)
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"News template {template_id} not found")
    
    _save_json_file("news_templates.json", templates)
    return {"status": "updated", "template_id": template_id}

@router.delete("/news/{template_id}")
async def delete_news_template(template_id: str, _: bool = Depends(verify_token)) -> Dict[str, Any]:
    """Delete news template (soft delete by setting active=false)"""
    templates = _load_json_file("news_templates.json", [])
    
    found = False
    for template in templates:
        if template.get("id") == template_id:
            template["active"] = False
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"News template {template_id} not found")
    
    _save_json_file("news_templates.json", templates)
    return {"status": "deleted", "template_id": template_id}

