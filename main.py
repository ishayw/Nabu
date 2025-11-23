import uvicorn
import logging
import os
from app.server import app, set_service
from app.audio_recorder import AudioRecorder
from app.service import MeetingService
from app.llm_provider import GeminiProvider
# from app.llm_dummy import DummyProvider # For testing without API key

# --- Log Filtering ---
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /status") == -1

# Filter out /status logs
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

def main():
    print("Starting Nabu Meeting Summarizer...")
    
    # Ensure directories exist
    os.makedirs("recordings", exist_ok=True)
    
    # Initialize components
    recorder = AudioRecorder(output_dir="recordings")
    
    provider = GeminiProvider() 
    # provider = DummyProvider() # Use dummy for now
    
    service = MeetingService(recorder, provider)
    
    # Inject service into FastAPI app
    set_service(service)
    
    # Start the background service
    service.start_service()
    
    try:
        # Run the API server
        # host="0.0.0.0" allows external access, "127.0.0.1" is local only
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        service.stop_service()

if __name__ == "__main__":
    main()
