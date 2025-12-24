"""
API endpoints for game tracking
"""
from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import database
import uuid
import json

router = APIRouter()

class GameInProgressCreate(BaseModel):
    fund_name: str
    geolocation: Optional[str] = None

class GameInProgressUpdate(BaseModel):
    fund_name: Optional[str] = None
    geolocation: Optional[str] = None

class HistoricalGameCreate(BaseModel):
    fund_name: str
    time_started: datetime
    time_ended: Optional[datetime] = None
    completed: bool = False
    geolocation: Optional[str] = None

@router.get("/games/in-progress")
async def list_games_in_progress(limit: int = 50, offset: int = 0):
    """List games in progress with pagination"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM games_in_progress
    """)
    total_result = cursor.fetchone()
    total_count = total_result["total"] if total_result else 0
    
    # Get paginated games
    cursor.execute("""
        SELECT id, fund_name, time_started, geolocation, created_at
        FROM games_in_progress
        ORDER BY time_started DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    games = cursor.fetchall()
    conn.close()
    
    return {
        "games": [
            {
                "id": game["id"],
                "fund_name": game["fund_name"],
                "time_started": game["time_started"],
                "geolocation": game["geolocation"],
                "created_at": game["created_at"]
            }
            for game in games
        ],
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total_count
    }

@router.post("/games/in-progress")
async def create_game_in_progress(game: GameInProgressCreate):
    """Create a new game in progress"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Generate UUID for the game
    game_id = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO games_in_progress (id, fund_name, time_started, geolocation)
        VALUES (?, ?, datetime('now'), ?)
    """, (game_id, game.fund_name, game.geolocation))
    
    conn.commit()
    conn.close()
    
    return {"id": game_id, "message": "Game created successfully"}

@router.get("/games/in-progress/{game_id}")
async def get_game_in_progress(game_id: str):
    """Get a specific game in progress"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fund_name, time_started, geolocation, created_at
        FROM games_in_progress
        WHERE id = ?
    """, (game_id,))
    
    game = cursor.fetchone()
    conn.close()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        "id": game["id"],
        "fund_name": game["fund_name"],
        "time_started": game["time_started"],
        "geolocation": game["geolocation"],
        "created_at": game["created_at"]
    }

@router.put("/games/in-progress/{game_id}")
async def update_game_in_progress(game_id: str, game: GameInProgressUpdate):
    """Update a game in progress"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Build update query dynamically
    updates = []
    values = []
    
    if game.fund_name is not None:
        updates.append("fund_name = ?")
        values.append(game.fund_name)
    
    if game.geolocation is not None:
        updates.append("geolocation = ?")
        values.append(game.geolocation)
    
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
    
    values.append(game_id)
    query = f"UPDATE games_in_progress SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(query, values)
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Game not found")
    
    conn.close()
    return {"message": "Game updated successfully"}

@router.delete("/games/in-progress/{game_id}")
async def delete_game_in_progress(game_id: str):
    """Delete a game in progress"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM games_in_progress WHERE id = ?", (game_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Game not found")
    
    conn.close()
    return {"message": "Game deleted successfully"}

class EndGameRequest(BaseModel):
    results_data: Optional[str] = None

@router.post("/games/in-progress/{game_id}/end")
async def end_game(
    game_id: str, 
    completed: bool = False, 
    total_pnl: Optional[float] = None,
    request_body: Optional[EndGameRequest] = Body(None)
):
    """Move a game from in-progress to historical"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get the game
    cursor.execute("""
        SELECT id, fund_name, time_started, geolocation
        FROM games_in_progress
        WHERE id = ?
    """, (game_id,))
    
    game = cursor.fetchone()
    if not game:
        conn.close()
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get results_data from request body if provided
    results_data_str = None
    results_data_dict = None
    if request_body and request_body.results_data:
        results_data_str = request_body.results_data
        try:
            results_data_dict = json.loads(results_data_str)
        except json.JSONDecodeError:
            results_data_dict = None
    
    # Extract metrics from results_data
    firm_cash = None
    game_days_played = None
    annualized_performance = None
    finishing_nav = None
    
    if results_data_dict:
        firm_cash = results_data_dict.get('firmCash')
        game_start_date = results_data_dict.get('gameStartDate')
        game_end_date = results_data_dict.get('gameEndDate')
        finishing_nav = results_data_dict.get('investorEquity')
        
        # Calculate game days played
        if game_start_date and game_end_date:
            game_days_played = database.calculate_game_days(game_start_date, game_end_date)
        
        # Calculate annualized performance
        if finishing_nav and game_days_played:
            annualized_performance = database.calculate_annualized_performance(finishing_nav, game_days_played)
    
    # Generate shareable_id if results_data is provided (retirement)
    shareable_id = None
    if results_data_str:
        shareable_id = str(uuid.uuid4())[:8]  # Short 8-character ID
    
    # Get time_ended from database after insertion to ensure consistent format
    # First insert, then calculate time_played
    cursor.execute("""
        INSERT INTO historical_games (id, fund_name, time_started, time_ended, completed, geolocation, total_pnl, shareable_id, results_data, firm_cash, game_days_played, annualized_performance)
        VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
    """, (game["id"], game["fund_name"], game["time_started"], completed, game["geolocation"], total_pnl, shareable_id, results_data_str, firm_cash, game_days_played, annualized_performance))
    
    # Get the inserted time_ended to calculate time_played
    cursor.execute("""
        SELECT time_ended FROM historical_games WHERE id = ?
    """, (game_id,))
    result = cursor.fetchone()
    time_ended = result["time_ended"] if result else None
    
    # Calculate and update time_played
    time_played = database.calculate_time_played(game["time_started"], time_ended)
    if time_played:
        cursor.execute("""
            UPDATE historical_games SET time_played = ? WHERE id = ?
        """, (time_played, game_id))
    
    # Delete from in_progress
    cursor.execute("DELETE FROM games_in_progress WHERE id = ?", (game_id,))
    
    conn.commit()
    conn.close()
    
    return {
        "message": "Game moved to historical",
        "shareable_id": shareable_id
    }

@router.get("/games/historical")
async def list_historical_games(limit: int = 50, offset: int = 0):
    """List historical games with pagination"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM historical_games
    """)
    total_result = cursor.fetchone()
    total_count = total_result["total"] if total_result else 0
    
    # Get paginated games
    cursor.execute("""
        SELECT id, fund_name, time_started, time_ended, completed, geolocation, time_played, total_pnl, created_at
        FROM historical_games
        ORDER BY time_started DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    games = cursor.fetchall()
    conn.close()
    
    return {
        "games": [
            {
                "id": game["id"],
                "fund_name": game["fund_name"],
                "time_started": game["time_started"],
                "time_ended": game["time_ended"],
                "completed": bool(game["completed"]),
                "geolocation": game["geolocation"],
                "time_played": game["time_played"],
                "total_pnl": game["total_pnl"],
                "created_at": game["created_at"]
            }
            for game in games
        ],
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total_count
    }

@router.get("/games/historical/{game_id}")
async def get_historical_game(game_id: str):
    """Get a specific historical game"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fund_name, time_started, time_ended, completed, geolocation, time_played, total_pnl, created_at
        FROM historical_games
        WHERE id = ?
    """, (game_id,))
    
    game = cursor.fetchone()
    conn.close()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        "id": game["id"],
        "fund_name": game["fund_name"],
        "time_started": game["time_started"],
        "time_ended": game["time_ended"],
        "completed": bool(game["completed"]),
        "geolocation": game["geolocation"],
        "time_played": game["time_played"],
        "total_pnl": game["total_pnl"],
        "created_at": game["created_at"]
    }

@router.post("/games/maintenance/move-old-games")
async def move_old_games():
    """Manually trigger moving old games to historical"""
    moved_count = database.move_old_games_to_historical()
    return {"message": f"Moved {moved_count} games to historical"}

@router.get("/games/results/{shareable_id}")
async def get_game_results(shareable_id: str):
    """Get game results by shareable ID"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, fund_name, time_started, time_ended, completed, total_pnl, results_data, time_played, game_days_played, annualized_performance
        FROM historical_games
        WHERE shareable_id = ?
    """, (shareable_id,))
    
    game = cursor.fetchone()
    conn.close()
    
    if not game:
        raise HTTPException(status_code=404, detail="Results not found")
    
    # Parse results_data JSON
    results_data = None
    if game["results_data"]:
        try:
            results_data = json.loads(game["results_data"])
        except json.JSONDecodeError:
            results_data = None
    
    return {
        "id": game["id"],
        "fund_name": game["fund_name"],
        "time_started": game["time_started"],
        "time_ended": game["time_ended"],
        "completed": bool(game["completed"]),
        "total_pnl": game["total_pnl"],
        "time_played": game["time_played"],
        "game_days_played": game["game_days_played"],
        "annualized_performance": game["annualized_performance"],
        "results_data": results_data
    }

@router.get("/leaderboard")
async def get_leaderboard(limit: int = 20, offset: int = 0):
    """Get leaderboard with pagination - only shows entries with positive PnL"""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # Get total count (only positive PnL)
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM historical_games
        WHERE total_pnl IS NOT NULL AND total_pnl > 0
    """)
    total_result = cursor.fetchone()
    total_count = total_result["total"] if total_result else 0
    
    # Get leaderboard entries (sorted by total_pnl DESC, only positive PnL)
    cursor.execute("""
        SELECT fund_name, total_pnl, time_ended, completed
        FROM historical_games
        WHERE total_pnl IS NOT NULL AND total_pnl > 0
        ORDER BY total_pnl DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    
    entries = cursor.fetchall()
    conn.close()
    
    return {
        "entries": [
            {
                "fund_name": entry["fund_name"],
                "total_pnl": entry["total_pnl"],
                "time_ended": entry["time_ended"],
                "completed": bool(entry["completed"])
            }
            for entry in entries
        ],
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total_count
    }

