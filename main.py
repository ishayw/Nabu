import uvicorn
import threading
import os
import sys
from app.audio_recorder import AudioRecorder
from app.llm_provider import GeminiProvider
from app.service import MeetingService
from app.server import app, set_service

def main():
    print("Initializing Nabu (formerly Local Meeting Assistant)...")
    
    # Ensure directories exist
    os.makedirs("recordings", exist_ok=True)
    
    # Initialize Components
    recorder = AudioRecorder(output_dir="recordings")
    llm_provider = GeminiProvider() # Will read API key from env
    service = MeetingService(recorder=recorder, llm_provider=llm_provider)
    
    # Inject service into FastAPI app
    set_service(service)
    
    # Start Service (Background Monitoring)
    service.start_service()
    
    print("Starting Web Server at http://localhost:8000")
    try:
        # Run Server
        # We use run() directly which blocks.
        # Service threads run in background.
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        service.stop_service()
        print("Exited.")

if __name__ == "__main__":
    main()
