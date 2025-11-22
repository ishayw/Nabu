import sqlite3
import os
from datetime import datetime

DB_PATH = "meetings.db"

def init_db():
    """Initialize the database with tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Meetings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            duration REAL,
            summary_text TEXT
        )
    ''')
    
    # Tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Meeting Tags relation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meeting_tags (
            meeting_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY(meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (meeting_id, tag_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def add_meeting(filename, created_at, duration=0, summary_text="", title=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if not title:
            title = f"Meeting {created_at}"
            
        cursor.execute(
            "INSERT INTO meetings (filename, title, created_at, duration, summary_text) VALUES (?, ?, ?, ?, ?)",
            (filename, title, created_at, duration, summary_text)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # Already exists
    finally:
        conn.close()

def update_meeting(filename, title=None, summary_text=None, duration=None):
    """Updates an existing meeting."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        if summary_text:
            updates.append("summary_text = ?")
            params.append(summary_text)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)
            
        if not updates:
            return False
            
        params.append(filename)
        sql = f"UPDATE meetings SET {', '.join(updates)} WHERE filename = ?"
        
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating meeting: {e}")
        return False
    finally:
        conn.close()

def get_all_meetings():
    conn = get_db_connection()
    meetings = conn.execute("SELECT * FROM meetings ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(m) for m in meetings]

def get_meeting(filename):
    conn = get_db_connection()
    meeting = conn.execute("SELECT * FROM meetings WHERE filename = ?", (filename,)).fetchone()
    conn.close()
    return dict(meeting) if meeting else None

def delete_meeting(filename):
    conn = get_db_connection()
    conn.execute("DELETE FROM meetings WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()

def clear_all_meetings():
    conn = get_db_connection()
    conn.execute("DELETE FROM meetings")
    conn.execute("DELETE FROM tags")
    conn.execute("DELETE FROM meeting_tags")
    conn.commit()
    conn.close()

def add_tag(meeting_filename, tag_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get meeting ID
    meeting = cursor.execute("SELECT id FROM meetings WHERE filename = ?", (meeting_filename,)).fetchone()
    if not meeting:
        conn.close()
        return False
    meeting_id = meeting['id']
    
    # Get or create tag ID
    cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
    tag = cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,)).fetchone()
    tag_id = tag['id']
    
    # Link
    cursor.execute("INSERT OR IGNORE INTO meeting_tags (meeting_id, tag_id) VALUES (?, ?)", (meeting_id, tag_id))
    
    conn.commit()
    conn.close()
    return True

def get_tags(meeting_filename):
    conn = get_db_connection()
    query = '''
        SELECT t.name 
        FROM tags t
        JOIN meeting_tags mt ON t.id = mt.tag_id
        JOIN meetings m ON m.id = mt.meeting_id
        WHERE m.filename = ?
    '''
    tags = conn.execute(query, (meeting_filename,)).fetchall()
    conn.close()
    return [t['name'] for t in tags]

def search_meetings(query):
    conn = get_db_connection()
    # Search in title, summary, or tags
    sql = '''
        SELECT DISTINCT m.* 
        FROM meetings m
        LEFT JOIN meeting_tags mt ON m.id = mt.meeting_id
        LEFT JOIN tags t ON mt.tag_id = t.id
        WHERE m.title LIKE ? 
           OR m.summary_text LIKE ? 
           OR t.name LIKE ?
        ORDER BY m.created_at DESC
    '''
    param = f"%{query}%"
    meetings = conn.execute(sql, (param, param, param)).fetchall()
    conn.close()
    return [dict(m) for m in meetings]
