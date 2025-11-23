import uvicorn
import logging
import os
from app.server import app, set_service
from app.audio_recorder import AudioRecorder
from app.service import MeetingService
# from app.llm_provider import GeminiProvider # Not implemented yet
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
    
    # provider = GeminiProvider() 
    # provider = DummyProvider() # Use dummy for now
    # For now, pass None or a dummy if Service expects it. 
    # Service code handles None provider gracefully or we can add a simple one.
    # Let's use a simple mock for now if needed, or just None.
    # The Service class imports: from app.llm_provider import GeminiProvider
    # But let's check service.py again. It has `llm_provider=None` default.
    
    # We need a provider that has `process_audio`.
    class SimpleProvider:
        def process_audio(self, filename):
            return "Summary generation not yet implemented. This is a placeholder."
            
    provider = SimpleProvider()
    
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
