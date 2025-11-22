from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import List
from datetime import datetime
from app.service import MeetingService
from app.database import (
    get_all_meetings, get_meeting, delete_meeting, clear_all_meetings,
    add_tag, get_tags, search_meetings, add_meeting
)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/recordings", StaticFiles(directory="recordings"), name="recordings")

# Global Service Instance (injected from main.py)
service: MeetingService = None

def set_service(s: MeetingService):
    global service
    service = s

class DeviceConfig(BaseModel):
    device_index: int

class TagsData(BaseModel):
    tag: str

@app.get("/")
async def read_root():
    return FileResponse("templates/index.html")

@app.get("/status")
async def get_status():
    """Get current service status."""
    if not service:
        return {"status": "offline"}
    
    # Map Enum to string
    status_str = service.status.value if hasattr(service.status, 'value') else str(service.status)
    is_recording = (status_str == "recording")
    
    return {
        "status": status_str,
        "is_recording": is_recording,
        "rms": float(service.recorder.get_rms())
    }

@app.get("/devices")
async def get_devices():
    """List available input devices."""
    if not service:
        return {"devices": []}
    return {"devices": service.recorder.list_input_devices()}

@app.post("/config/device")
async def set_device(config: DeviceConfig):
    """Set the active microphone device."""
    if service:
        service.recorder.set_device(config.device_index)
    return {"status": "updated", "device_index": config.device_index}

@app.post("/control/{action}")
async def control_service(action: str):
    """Manual control for recording."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if action == "start":
        # Use service method to ensure state is updated correctly
        service.start_recording(manual=True)
        return {"status": "started"}
    
    elif action == "stop":
        # Use service method to ensure processing is triggered
        service.stop_recording()
        return {"status": "stopped"}
    
    return {"error": "Invalid action"}

@app.get("/history")
async def get_history():
    """List all recordings from DB."""
    meetings = get_all_meetings()
    
    # Enrich with tags
    result = []
    for m in meetings:
        m['tags'] = get_tags(m['filename'])
        result.append(m)
        
    return {"recordings": result}

@app.delete("/history")
async def clear_history():
    """Delete all recordings and summaries."""
    clear_all_meetings()
    
    # Also clear files
    folder = "recordings"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            
    return {"status": "cleared"}

@app.get("/meeting/{filename}")
async def get_meeting_details(filename: str):
    """Get details for a specific meeting."""
    meeting = get_meeting(filename)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    meeting['tags'] = get_tags(filename)
    return meeting

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio file for playback."""
    file_path = os.path.join("recordings", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")

@app.get("/tags/{filename}")
async def get_meeting_tags(filename: str):
    """Get tags for a recording."""
    return {"tags": get_tags(filename)}

@app.post("/tags/{filename}")
async def add_meeting_tag(filename: str, data: TagsData):
    """Add a tag to a recording."""
    success = add_tag(filename, data.tag)
    if not success:
         raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "added", "tag": data.tag}

@app.get("/search")
async def search(q: str):
    """Search meetings by title, summary, or tags."""
    results = search_meetings(q)
    # Enrich with tags
    for m in results:
        m['tags'] = get_tags(m['filename'])
    return {"results": results}

@app.post("/upload")
async def upload_recording(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a recording file manually."""
    try:
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Keep original extension or convert? Let's assume wav/mp3/m4a
        ext = os.path.splitext(file.filename)[1]
        if not ext:
            ext = ".wav"
            
        filename = f"meeting_{timestamp}{ext}"
        file_path = os.path.join("recordings", filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get duration (approximate or 0 for now, updated after processing)
        duration = 0 
        
        # Add to DB immediately so it shows up
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_meeting(filename, created_at, duration, summary_text="Processing...", title=file.filename)
        
        # Trigger processing in background
        if service:
             background_tasks.add_task(service._process_meeting, file_path)
             
        return {"status": "uploaded", "filename": filename}
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
