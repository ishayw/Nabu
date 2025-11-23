import uvicorn
import logging
import os
from app.server import app, set_service
from app.audio_recorder import AudioRecorder
from app.service import MeetingService
from app.llm_provider import GeminiProvider
from app.config import Config
from app.logger import setup_logging, get_logger
# from app.llm_dummy import DummyProvider # For testing without API key

# --- Log Filtering ---
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /status") == -1

# Filter out /status logs
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

def main():
    # Setup logging first
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("="*60)
    logger.info("Starting Nabu Meeting Summarizer...")
    logger.info(f"Environment: {Config.APP_ENV}")
    logger.info(f"Host: {Config.APP_HOST}:{Config.APP_PORT}")
    logger.info("="*60)
    
    # Ensure directories exist
    os.makedirs(Config.RECORDINGS_DIR, exist_ok=True)
    
    # Initialize components
    recorder = AudioRecorder(output_dir=Config.RECORDINGS_DIR)
    
    provider = GeminiProvider() 
    # provider = DummyProvider() # Use dummy for now
    
    service = MeetingService(recorder, provider)
    
    # Inject service into FastAPI app
    set_service(service)
    
    # Start the background service
    service.start_service()
    
    try:
        # Run the API server
        logger.info("Starting FastAPI server...")
        uvicorn.run(
            app, 
            host=Config.APP_HOST, 
            port=Config.APP_PORT, 
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    finally:
        service.stop_service()

if __name__ == "__main__":
    main()
