import requests
import json

url = "http://localhost:8000/history"

try:
    response = requests.get(url)
    data = response.json()
    recordings = data.get("recordings", [])
    
    if not recordings:
        print("No recordings found.")
    else:
        # Get the most recent one (upload)
        latest = recordings[0]
        print(f"Filename: {latest.get('filename')}")
        print(f"Title: {latest.get('title')}")
        print(f"Summary: {latest.get('summary_text')}")
        print(f"Tags: {latest.get('tags')}")
        
except Exception as e:
    print(f"Error: {e}")
