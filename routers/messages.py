from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any, List, Optional, Literal
import json
from pathlib import Path
import os

router = APIRouter()

# Path to data files
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Simple token authentication
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me-in-production")

def verify_token(authorization: Optional[str] = Header(None)):
    """Verify admin token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
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

# ===== UNIFIED MESSAGE ENDPOINTS =====

@router.get("/messages")
async def get_messages(
    channel: Optional[Literal["newswire", "email", "ledger"]] = None,
    active_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Get all messages, optionally filtered by channel.
    Unified endpoint for all message types.
    """
    messages = _load_json_file("messages.json", [])
    
    # Filter by channel if specified
    if channel:
        messages = [m for m in messages if m.get("channel") == channel]
    
    # Filter active if requested
    if active_only:
        messages = [m for m in messages if m.get("active", True)]
    
    return messages

@router.get("/messages/{message_id}")
async def get_message(message_id: str) -> Dict[str, Any]:
    """Get a specific message by ID"""
    messages = _load_json_file("messages.json", [])
    message = next((m for m in messages if m.get("id") == message_id), None)
    if not message:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    return message

# ===== ADMIN ENDPOINTS =====

@router.post("/messages", dependencies=[Depends(verify_token)])
async def create_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new message.
    
    Required fields:
    - channel: "newswire" | "email" | "ledger"
    - creation_trigger: "random" | "game_event"
    - features: { read_only: bool, requires_response: bool }
    - impact: { type: "none" | "simulation" | "user_action", ... }
    - content: { ... }
    """
    messages = _load_json_file("messages.json", [])
    
    # Validate required fields
    required_fields = ["channel", "creation_trigger", "features", "impact", "content"]
    for field in required_fields:
        if field not in message:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Validate channel
    if message["channel"] not in ["newswire", "email", "ledger"]:
        raise HTTPException(status_code=400, detail="channel must be 'newswire', 'email', or 'ledger'")
    
    # Validate creation_trigger
    if message["creation_trigger"] not in ["random", "game_event"]:
        raise HTTPException(status_code=400, detail="creation_trigger must be 'random' or 'game_event'")
    
    # Generate ID if not provided
    if "id" not in message:
        message["id"] = f"{message['channel']}-{len(messages) + 1}"
    
    # Set defaults
    if "active" not in message:
        message["active"] = True
    
    messages.append(message)
    _save_json_file("messages.json", messages)
    
    return {"status": "created", "message": message}

@router.put("/messages/{message_id}", dependencies=[Depends(verify_token)])
async def update_message(message_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing message"""
    messages = _load_json_file("messages.json", [])
    
    found = False
    for message in messages:
        if message.get("id") == message_id:
            message.update(updates)
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    
    _save_json_file("messages.json", messages)
    return {"status": "updated", "message_id": message_id}

@router.delete("/messages/{message_id}", dependencies=[Depends(verify_token)])
async def delete_message(message_id: str) -> Dict[str, Any]:
    """Delete a message (soft delete by setting active=false)"""
    messages = _load_json_file("messages.json", [])
    
    found = False
    for message in messages:
        if message.get("id") == message_id:
            message["active"] = False
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail=f"Message {message_id} not found")
    
    _save_json_file("messages.json", messages)
    return {"status": "deleted", "message_id": message_id}

# ===== LEGACY ENDPOINTS (for backward compatibility with frontend) =====
# These map to the new unified message system and are served under /api/content/*

@router.get("/content/flavor")
async def get_flavor_text() -> List[Dict[str, Any]]:
    """Legacy endpoint - maps to newswire messages with flavor type"""
    messages = _load_json_file("messages.json", [])
    flavor_messages = [
        m for m in messages 
        if m.get("channel") == "newswire" 
        and m.get("content", {}).get("type") == "flavor"
        and m.get("active", True)
    ]
    
    # If no messages found, return defaults
    if not flavor_messages:
        return [
            {"id": "1", "text": "Analyst spotted crying in the bathroom.", "active": True},
            {"id": "2", "text": "Compliance officer is asking about your WhatsApps.", "active": True},
            {"id": "3", "text": "Your star trader wants a bigger bonus.", "active": True},
            {"id": "4", "text": "ZeroHedge tweeted about your positions.", "active": True},
            {"id": "5", "text": "The coffee machine is broken. Morale -10.", "active": True},
            {"id": "6", "text": "A junior analyst sent an Excel sheet with hardcoded values.", "active": True},
            {"id": "7", "text": "The printer is out of toner. The deal is stalled.", "active": True},
        ]
    
    # Convert to legacy format
    return [
        {"id": m["id"], "text": m["content"].get("text", ""), "active": m.get("active", True)}
        for m in flavor_messages
    ]

@router.get("/content/recruitment")
async def get_recruitment_data() -> Dict[str, Any]:
    """
    Legacy endpoint - returns recruitment configuration.
    Now supports both new format (candidates array) and old format (separate arrays).
    """
    # Try new format first (recruitment_candidates.json)
    candidates = _load_json_file("recruitment_candidates.json", [])
    
    if candidates and isinstance(candidates, list) and len(candidates) > 0:
        # New format: convert to legacy format for backward compatibility
        active_candidates = [c for c in candidates if c.get("active", True)]
        
        # Build legacy format from candidates
        specialisms = {}
        names_first = []
        names_last = []
        bios = []
        
        for candidate in active_candidates:
            spec_name = candidate.get("specialism")
            if spec_name and spec_name not in specialisms:
                specialisms[spec_name] = {
                    "beta_mu": candidate.get("beta_mu", 0.0),
                    "beta_sigma": candidate.get("beta_sigma", 0.1),
                    "vol_range": candidate.get("vol_range", [0.01, 0.02])
                }
            
            if candidate.get("first_name"):
                names_first.append(candidate["first_name"])
            if candidate.get("last_name"):
                names_last.append(candidate["last_name"])
            if candidate.get("bio"):
                bios.append(candidate["bio"])
        
        return {
            "specialisms": specialisms,
            "names_first": list(set(names_first)),  # Remove duplicates
            "names_last": list(set(names_last)),
            "bios": bios,
            "_candidates": active_candidates  # Include full candidate data for new frontend code
        }
    
    # Fallback to old format (recruitment.json)
    default_recruitment = {
        "specialisms": {
            "Global Macro": {"beta_mu": 0.4, "beta_sigma": 0.5, "vol_range": [0.01, 0.03]},
            "Equity TMT": {"beta_mu": 1.1, "beta_sigma": 0.2, "vol_range": [0.015, 0.04]},
            "Fixed Income RV": {"beta_mu": 0.05, "beta_sigma": 0.1, "vol_range": [0.005, 0.01]},
            "Deep Value": {"beta_mu": 0.8, "beta_sigma": 0.3, "vol_range": [0.01, 0.02]},
            "Stat Arb": {"beta_mu": 0.0, "beta_sigma": 0.05, "vol_range": [0.005, 0.015]}
        },
        "names_first": ["Brad", "Chad", "Winston", "Preston", "Chip", "Trey", "Gorman", "Liz", "Sloane", "Caroline"],
        "names_last": ["Sterling", "Hancock", "Vanderbilt", "Roth", "Dubois", "Kowalski", "Chen", "Gupta", "Schmidt"],
        "bios": [
            "Claims he predicted the 2008 crash (he was 12).",
            "Spent 3 years at Citadel. Has a non-compete he thinks is 'unenforceable'.",
            "Writes a substack about interest rates. 500k followers.",
            "Only trades when Mercury is in retrograde.",
            "Previously managed money for a cartel (allegedly).",
            "Wears a vest in the shower. Pure efficiency.",
            "Thinks 'Risk Management' is for cowards.",
            "Brings his own Bloomberg keyboard to interviews.",
            "Left last firm because the coffee wasn't single-origin."
        ]
    }
    return _load_json_file("recruitment.json", default_recruitment)

@router.get("/content/news")
async def get_news_templates() -> List[Dict[str, Any]]:
    """Legacy endpoint - maps to newswire messages with news type"""
    messages = _load_json_file("messages.json", [])
    news_messages = [
        m for m in messages
        if m.get("channel") == "newswire"
        and m.get("content", {}).get("type") in ["info", "alert", "breaking"]
        and m.get("active", True)
    ]
    
    # If no messages found, return minimal defaults
    if not news_messages:
        return [
            {
                "id": "1",
                "headline": "Fed Signals Rate Cut",
                "body": "Federal Reserve hints at potential rate cuts in upcoming meetings, sparking optimism in equity markets.",
                "impact": {"volatility_spike": 0.008},
                "type": "info",
                "probability": 0.03,
                "active": True
            }
        ]
    
    # Convert to legacy format
    return [
        {
            "id": m["id"],
            "headline": m["content"].get("headline", ""),
            "body": m["content"].get("body", ""),
            "impact": m.get("impact", {}).get("simulation", {}),
            "type": m["content"].get("type", "info"),
            "probability": m.get("creation_trigger_config", {}).get("probability", 0.03),
            "active": m.get("active", True)
        }
        for m in news_messages
    ]

