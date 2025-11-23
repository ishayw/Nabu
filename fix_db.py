import sqlite3
import json
import re
import ast

DB_PATH = "meetings.db"

def fix_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    meetings = cursor.execute("SELECT * FROM meetings").fetchall()
    
    for m in meetings:
        summary_text = m['summary_text']
        if not summary_text: continue
        
        # Check if it looks like raw JSON (starts with ``` or {)
        if summary_text.strip().startswith("```") or summary_text.strip().startswith("{"):
            print(f"Fixing meeting: {m['filename']}")
            
            cleaned_text = summary_text.strip()
            if "```" in cleaned_text:
                parts = cleaned_text.split("```")
                if len(parts) >= 3:
                    candidate = parts[1]
                    if candidate.startswith("json"):
                        candidate = candidate[4:]
                    cleaned_text = candidate.strip()
            
            try:
                # Try parsing
                try:
                    data = json.loads(cleaned_text)
                except:
                    # Try ast fallback
                     # Try one more time with strict=False if available
                    cleaned_text_fixed = re.sub(r',\s*\}', '}', cleaned_text)
                    cleaned_text_fixed = re.sub(r',\s*\]', ']', cleaned_text_fixed)
                    try:
                        data = json.loads(cleaned_text_fixed)
                    except:
                        py_text = cleaned_text.replace("true", "True").replace("false", "False").replace("null", "None")
                        data = ast.literal_eval(py_text)
                
                if isinstance(data, dict):
                    new_summary = data.get("summary", summary_text)
                    new_title = data.get("title", m['title'])
                    
                    cursor.execute(
                        "UPDATE meetings SET summary_text = ?, title = ? WHERE id = ?",
                        (new_summary, new_title, m['id'])
                    )
                    print(f"  -> Updated summary and title.")
                else:
                    print("  -> Parsed data is not a dict.")
                    
            except Exception as e:
                print(f"  -> Failed to parse: {e}")

    conn.commit()
    conn.close()
    print("Database fix complete.")

if __name__ == "__main__":
    fix_db()
