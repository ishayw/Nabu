import requests
import os

url = "http://localhost:8000/upload"
file_path = "test.m4a"

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

print(f"Uploading {file_path}...")
with open(file_path, "rb") as f:
    files = {"file": (os.path.basename(file_path), f, "audio/mp4")}
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
