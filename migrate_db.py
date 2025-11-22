import os
import json
import glob
from app.database import init_db, add_meeting, add_tag

RECORDINGS_DIR = "recordings"

def migrate():
    print("Initializing database...")
    init_db()
    
    print("Migrating recordings...")
    wav_files = glob.glob(os.path.join(RECORDINGS_DIR, "*.wav"))
    
    for wav_path in wav_files:
        filename = os.path.basename(wav_path)
        created_at = filename.replace("meeting_", "").replace(".wav", "")
        # Format timestamp nicely if possible, or keep raw
        try:
            dt = datetime.strptime(created_at, "%Y%m%d_%H%M%S")
            created_at_fmt = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            created_at_fmt = created_at
            
        # Check for summary
        summary_path = wav_path.replace(".wav", ".txt")
        summary_text = ""
        if os.path.exists(summary_path):
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read()
                
        # Add to DB
        print(f"Importing {filename}...")
        add_meeting(filename, created_at_fmt, summary_text=summary_text)
        
        # Check for tags
        tags_path = wav_path.replace(".wav", ".tags.json")
        if os.path.exists(tags_path):
            try:
                with open(tags_path, "r") as f:
                    tags = json.load(f)
                    for tag in tags:
                        add_tag(filename, tag)
                print(f"  Added {len(tags)} tags.")
            except Exception as e:
                print(f"  Error reading tags: {e}")

if __name__ == "__main__":
    from datetime import datetime
    migrate()
    print("Migration complete.")
