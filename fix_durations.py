"""
Migration script to fix incorrect durations in the database.
This script finds all meetings with duration=0 and recalculates their correct duration.
"""

import sqlite3
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.audio_utils import get_audio_duration
from app.database import DB_PATH, get_db_connection


def fix_durations(dry_run=False):
    """
    Find all meetings with duration=0 and update them with correct duration.
    
    Args:
        dry_run: If True, only show what would be fixed without making changes
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find meetings with duration = 0
    meetings = cursor.execute(
        "SELECT id, filename, duration FROM meetings WHERE duration = 0 OR duration IS NULL"
    ).fetchall()
    
    if not meetings:
        print("✓ No meetings with incorrect duration found.")
        conn.close()
        return
    
    print(f"Found {len(meetings)} meeting(s) with duration=0:\n")
    
    fixed_count = 0
    failed_count = 0
    
    for meeting in meetings:
        meeting_id = meeting['id']
        filename = meeting['filename']
        old_duration = meeting['duration'] or 0
        
        # Find the file
        filepath = os.path.join("recordings", filename)
        
        if not os.path.exists(filepath):
            print(f"✗ {filename}")
            print(f"  File not found: {filepath}")
            failed_count += 1
            continue
        
        # Get correct duration
        new_duration = get_audio_duration(filepath)
        
        if new_duration <= 0:
            print(f"✗ {filename}")
            print(f"  Could not determine duration")
            failed_count += 1
            continue
        
        print(f"{'[DRY RUN] ' if dry_run else ''}✓ {filename}")
        print(f"  Old duration: {old_duration:.1f}s")
        print(f"  New duration: {new_duration:.1f}s ({new_duration/60:.1f} min)")
        
        if not dry_run:
            cursor.execute(
                "UPDATE meetings SET duration = ? WHERE id = ?",
                (new_duration, meeting_id)
            )
            fixed_count += 1
        print()
    
    if not dry_run:
        conn.commit()
        print(f"\n✓ Fixed {fixed_count} meeting(s)")
    else:
        print(f"\n[DRY RUN] Would fix {len(meetings) - failed_count} meeting(s)")
    
    if failed_count > 0:
        print(f"✗ Failed to fix {failed_count} meeting(s)")
    
    conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix incorrect durations in meetings database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Meeting Duration Migration Script")
    print("=" * 60)
    print()
    
    if args.dry_run:
        print("Running in DRY RUN mode - no changes will be made\n")
    
    fix_durations(dry_run=args.dry_run)
