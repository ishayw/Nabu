"""
Check why tags aren't being saved for the M4A files.
This script will examine the debug_log.txt to see what tags were extracted from the LLM.
"""

import os

log_file = "debug_log.txt"

if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Debug Log Contents:")
    print("=" * 60)
    print(content)
    print("=" * 60)
    
    # Try to extract tags from the response
    import json
    import re
    
    # Find the raw response
    if "Raw Response:" in content:
        raw_start = content.find("Raw Response:") + len("Raw Response:")
        raw_end = content.find("\n\n", raw_start)
        if raw_end == -1:
            raw_end = len(content)
        raw_response = content[raw_start:raw_end].strip()
        
        print("\nParsing tags from response...")
        
        # Try to extract JSON
        cleaned = raw_response.strip()
        
        # Remove markdown code blocks
        if "```" in cleaned:
            parts = cleaned.split("```")
            if len(parts) >= 3:
                candidate = parts[1]
                if candidate.startswith("json"):
                    candidate = candidate[4:]
                cleaned = candidate.strip()
        
        # Try to parse
        try:
            data = json.loads(cleaned)
            tags = data.get("tags", [])
            title = data.get("title", "")
            
            print(f"\nExtracted data:")
            print(f"  Title: {title}")
            print(f"  Tags: {tags}")
            print(f"  Tags type: {type(tags)}")
            print(f"  Tags length: {len(tags) if isinstance(tags, list) else 'N/A'}")
            
        except Exception as e:
            print(f"\nFailed to parse JSON: {e}")
else:
    print(f"Debug log file not found: {log_file}")
