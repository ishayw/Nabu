"""
Settings management for the Meeting Summarizer application.
Provides persistent storage and retrieval of user preferences.
"""

import sqlite3
from typing import Any, Dict, Optional
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)


class SettingsManager:
    """Manages application settings with database persistence."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self._create_table()
        self._initialize_defaults()
    
    def _create_table(self):
        """Create settings table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Settings table ready")
    
    def _initialize_defaults(self):
        """Initialize default settings if they don't exist."""
        defaults = {
            "min_recording_duration": str(Config.MIN_RECORDING_DURATION),
            "delete_short_recordings": "false",
            "compress_recordings": "true",
            "auto_detection": str(Config.AUTO_DETECTION).lower(),
            "vad_threshold": str(Config.VAD_THRESHOLD),
            "silence_duration": str(Config.SILENCE_DURATION),
        }
        
        for key, value in defaults.items():
            if self.get(key) is None:
                self.set(key, value)
    
    def get(self, key: str) -> Optional[str]:
        """Get a setting value by key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def set(self, key: str, value: str, description: str = None):
        """Set a setting value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO settings (key, value, description, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                description = excluded.description,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value, description))
        
        conn.commit()
        conn.close()
        logger.info(f"Setting updated: {key} = {value}")
    
    def get_all(self) -> Dict[str, str]:
        """Get all settings as a dictionary."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT key, value FROM settings")
        results = cursor.fetchall()
        
        conn.close()
        return {row[0]: row[1] for row in results}
    
    def delete(self, key: str):
        """Delete a setting."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
        
        conn.commit()
        conn.close()
        logger.info(f"Setting deleted: {key}")


# Global settings manager instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
