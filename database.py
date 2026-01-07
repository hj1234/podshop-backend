"""
Database models and setup for game tracking
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import os
import uuid

# Database file path
# Use Railway volume if available, otherwise use local directory
import os
volume_path = os.getenv('RAILWAY_VOLUME_MOUNT_PATH', None)
if volume_path:
    DB_DIR = Path(volume_path)
    # Ensure volume directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
else:
    DB_DIR = Path(__file__).parent  # Fallback to local directory for development
DB_PATH = DB_DIR / "games.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Games in progress table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games_in_progress (
            id TEXT PRIMARY KEY,
            fund_name TEXT NOT NULL,
            time_started TIMESTAMP NOT NULL,
            geolocation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Historical games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_games (
            id TEXT PRIMARY KEY,
            fund_name TEXT NOT NULL,
            time_started TIMESTAMP NOT NULL,
            time_ended TIMESTAMP,
            completed BOOLEAN NOT NULL DEFAULT 0,
            geolocation TEXT,
            time_played TEXT,
            total_pnl REAL,
            shareable_id TEXT UNIQUE,
            results_data TEXT,
            firm_cash REAL,
            game_days_played INTEGER,
            annualized_performance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Add time_played column to existing tables (if it doesn't exist)
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN time_played TEXT")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add total_pnl column to existing tables (if it doesn't exist)
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN total_pnl REAL")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add shareable_id column for shareable results
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN shareable_id TEXT UNIQUE")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add results_data column to store JSON data (awards, etc.)
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN results_data TEXT")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add firm_cash column
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN firm_cash REAL")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add game_days_played column
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN game_days_played INTEGER")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Add annualized_performance column
    try:
        cursor.execute("ALTER TABLE historical_games ADD COLUMN annualized_performance REAL")
    except sqlite3.OperationalError:
        # Column already exists, ignore
        pass
    
    # Create indexes for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_games_in_progress_time_started 
        ON games_in_progress(time_started)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_games_time_started 
        ON historical_games(time_started)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_historical_games_total_pnl 
        ON historical_games(total_pnl DESC)
    """)
    
    conn.commit()
    conn.close()

def calculate_game_days(game_start_date: Optional[str], game_end_date: Optional[str]) -> Optional[int]:
    """Calculate number of game days played from game dates"""
    if not game_start_date or not game_end_date:
        return None
    
    try:
        start = datetime.strptime(game_start_date, '%Y-%m-%d')
        end = datetime.strptime(game_end_date, '%Y-%m-%d')
        delta = end - start
        days = delta.days + 1  # Include both start and end day
        return max(1, days)  # At least 1 day
    except (ValueError, AttributeError) as e:
        print(f"Error calculating game_days: {e}, game_start_date={game_start_date}, game_end_date={game_end_date}")
        return None

def calculate_annualized_performance(finishing_nav: float, game_days: int) -> Optional[float]:
    """Calculate annualized performance: ((finishing_nav / 100,000,000) ^ (252/game_days)) - 1"""
    if not game_days or game_days <= 0:
        return None
    
    try:
        starting_nav = 100_000_000.0
        if finishing_nav <= 0:
            return None
        
        # Calculate return ratio
        return_ratio = finishing_nav / starting_nav
        
        # Annualize: (return_ratio ^ (252 / game_days)) - 1
        annualization_factor = 252.0 / game_days
        annualized_return = (return_ratio ** annualization_factor) - 1.0
        
        return annualized_return
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error calculating annualized_performance: {e}")
        return None

def calculate_time_played(time_started: str, time_ended: Optional[str]) -> Optional[str]:
    """Calculate time played in minutes and seconds format (e.g., '5m 30s')
    
    Handles both SQLite datetime format ('YYYY-MM-DD HH:MM:SS') and ISO format.
    """
    if not time_ended:
        return None
    
    try:
        # Handle SQLite datetime format (space-separated) and ISO format (T-separated)
        start_str = time_started.replace('Z', '+00:00').replace(' ', 'T', 1)
        end_str = time_ended.replace('Z', '+00:00').replace(' ', 'T', 1)
        
        # Parse datetime strings
        if '+' in start_str or start_str.endswith('Z'):
            start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        else:
            # SQLite format: 'YYYY-MM-DD HH:MM:SS'
            start = datetime.strptime(time_started, '%Y-%m-%d %H:%M:%S')
        
        if '+' in end_str or end_str.endswith('Z'):
            end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        else:
            # SQLite format: 'YYYY-MM-DD HH:MM:SS'
            end = datetime.strptime(time_ended, '%Y-%m-%d %H:%M:%S')
        
        delta = end - start
        total_seconds = int(delta.total_seconds())
        
        if total_seconds < 0:
            return None
        
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except (ValueError, AttributeError) as e:
        print(f"Error calculating time_played: {e}, time_started={time_started}, time_ended={time_ended}")
        return None

def move_old_games_to_historical():
    """Move games older than 1 hour from in_progress to historical with completed=False"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find games started more than 1 hour ago
    cursor.execute("""
        SELECT id, fund_name, time_started, geolocation
        FROM games_in_progress
        WHERE datetime(time_started) < datetime('now', '-1 hour')
    """)
    
    old_games = cursor.fetchall()
    
    for game in old_games:
        # Insert into historical (preserve the UUID)
        cursor.execute("""
            INSERT INTO historical_games (id, fund_name, time_started, time_ended, completed, geolocation)
            VALUES (?, ?, ?, datetime('now'), 0, ?)
        """, (game['id'], game['fund_name'], game['time_started'], game['geolocation']))
        
        # Get the inserted time_ended to calculate time_played
        cursor.execute("""
            SELECT time_ended FROM historical_games WHERE id = ?
        """, (game['id'],))
        result = cursor.fetchone()
        time_ended = result['time_ended'] if result else None
        
        # Calculate and update time_played
        time_played = calculate_time_played(game['time_started'], time_ended)
        if time_played:
            cursor.execute("""
                UPDATE historical_games SET time_played = ? WHERE id = ?
            """, (time_played, game['id']))
        
        # Delete from in_progress
        cursor.execute("DELETE FROM games_in_progress WHERE id = ?", (game['id'],))
    
    conn.commit()
    conn.close()
    
    return len(old_games)

def delete_historical_game(game_id: str) -> bool:
    """Delete a historical game by ID. Returns True if deleted, False if not found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM historical_games WHERE id = ?", (game_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted

# Initialize database on import
init_database()

