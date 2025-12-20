from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from routers import admin, messages, games
import database
import os

app = FastAPI(title="Pod Shop Content API", version="1.0.0")

# Unified message system (includes legacy /api/content/* endpoints for backward compatibility)
app.include_router(messages.router, prefix="/api", tags=["messages"])

# Also include messages router under /api/messages for clarity
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])

# Admin endpoints for managing content (recruitment config and messages)
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Game tracking endpoints
app.include_router(games.router, prefix="/api", tags=["games"])

@app.get("/")
async def root():
    return {"message": "Pod Shop Content API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    database.init_database()
    
class MoveOldGamesMiddleware(BaseHTTPMiddleware):
    """Middleware to move old games to historical"""
    async def dispatch(self, request: Request, call_next):
        # Only run on API requests, not too frequently
        if request.url.path.startswith("/api/games") and request.method == "GET":
            try:
                database.move_old_games_to_historical()
            except Exception as e:
                # Don't fail the request if maintenance fails
                print(f"Error moving old games: {e}")
        
        response = await call_next(request)
        return response

# Add custom middleware first (runs last)
app.add_middleware(MoveOldGamesMiddleware)

# CORS middleware must be added LAST so it runs FIRST (middleware runs in reverse order)
# This ensures CORS headers are added to all responses
# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
# Add default localhost origins
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
# Combine and filter out empty strings
all_origins = [origin for origin in default_origins + allowed_origins if origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=all_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

