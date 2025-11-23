from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import magic
from typing import List, Optional
from datetime import datetime
from app.service import MeetingService
from app.database import (
    get_all_meetings, get_meeting, delete_meeting, clear_all_meetings,
    add_tag, get_tags, search_meetings, add_meeting
)
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/recordings", StaticFiles(directory=Config.RECORDINGS_DIR), name="recordings")

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
        "rms": float(service.recorder.get_rms()),
        "notification": service.last_notification
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
async def get_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(Config.DEFAULT_PAGE_SIZE, ge=1, le=Config.MAX_PAGE_SIZE, description="Items per page")
):
    """List recordings from DB with pagination."""
    all_meetings = get_all_meetings()
    
    # Calculate pagination
    total = len(all_meetings)
    start = (page - 1) * page_size
    end = start + page_size
    
    # Get page of meetings
    meetings_page = all_meetings[start:end]
    
    # Enrich with tags
    result = []
    for m in meetings_page:
        m['tags'] = get_tags(m['filename'])
        result.append(m)
        
    return {
        "recordings": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

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

@app.delete("/history/{filename}")
async def delete_single_meeting(filename: str):
    """Delete a single meeting."""
    # Delete from DB
    delete_meeting(filename)
    
    # Delete file
    file_path = os.path.join("recordings", filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Failed to delete {file_path}: {e}")
        # We still return success if DB delete worked, or maybe warn?
        
    return {"status": "deleted", "filename": filename}

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
    """Upload a recording file manually with validation."""
    try:
        # Validate file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {ext} not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > Config.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {Config.MAX_FILE_SIZE_MB}MB"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Validate MIME type using python-magic
        try:
            mime = magic.from_buffer(content, mime=True)
            allowed_mimes = ['audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/wav', 
                           'audio/x-wav', 'audio/flac', 'audio/ogg']
            if mime not in allowed_mimes:
                logger.warning(f"File {file.filename} has unexpected MIME type: {mime}")
        except Exception as e:
            logger.warning(f"Could not validate MIME type: {e}")
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meeting_{timestamp}{ext}"
        file_path = os.path.join(Config.RECORDINGS_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        logger.info(f"File uploaded: {filename} ({file_size / 1024 / 1024:.2f}MB)")
        
        # Add to DB immediately so it shows up
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        add_meeting(filename, created_at, 0, summary_text="Processing...", title=file.filename)
        
        # Trigger processing in background
        if service:
             background_tasks.add_task(service._process_meeting, file_path)
              
        return {"status": "uploaded", "filename": filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
