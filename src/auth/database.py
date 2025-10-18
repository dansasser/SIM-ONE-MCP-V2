"""
Database module for API key storage and management.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

# Database path
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "api_keys.db"


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the API keys database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create api_keys table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT NOT NULL UNIQUE,
            key_prefix TEXT NOT NULL,
            user_email TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            expires_at TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_user_email ON api_keys(user_email)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_is_active ON api_keys(is_active)
    """)
    
    conn.commit()
    conn.close()


def insert_api_key(
    key_hash: str,
    key_prefix: str,
    user_email: str,
    description: Optional[str] = None
) -> int:
    """Insert a new API key into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO api_keys (key_hash, key_prefix, user_email, description)
        VALUES (?, ?, ?, ?)
    """, (key_hash, key_prefix, user_email, description))
    
    key_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return key_id


def get_api_key_by_hash(key_hash: str) -> Optional[dict]:
    """Get API key details by hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM api_keys
        WHERE key_hash = ? AND is_active = 1
    """, (key_hash,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_last_used(key_hash: str) -> None:
    """Update the last_used_at timestamp for an API key."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE api_keys
        SET last_used_at = CURRENT_TIMESTAMP
        WHERE key_hash = ?
    """, (key_hash,))
    
    conn.commit()
    conn.close()


def list_all_keys() -> list[dict]:
    """List all API keys."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, key_prefix, user_email, description, created_at, last_used_at, is_active
        FROM api_keys
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def list_keys_by_email(user_email: str) -> list[dict]:
    """List all API keys for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, key_prefix, user_email, description, created_at, last_used_at, is_active
        FROM api_keys
        WHERE user_email = ?
        ORDER BY created_at DESC
    """, (user_email,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def revoke_key_by_prefix(key_prefix: str) -> bool:
    """Revoke (deactivate) an API key by its prefix."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE api_keys
        SET is_active = 0
        WHERE key_prefix = ?
    """, (key_prefix,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0


def get_key_by_prefix(key_prefix: str) -> Optional[dict]:
    """Get API key details by prefix."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, key_prefix, user_email, description, created_at, last_used_at, is_active
        FROM api_keys
        WHERE key_prefix = ?
    """, (key_prefix,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

