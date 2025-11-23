import os
import time
from abc import ABC, abstractmethod
import google.generativeai as genai
from dotenv import load_dotenv
from app.config import Config
from app.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

class LLMProvider(ABC):
    @abstractmethod
    def process_audio(self, audio_path: str) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key=None, max_retries=None, retry_delay=None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.max_retries = max_retries or Config.LLM_MAX_RETRIES
        self.retry_delay = retry_delay or Config.LLM_RETRY_DELAY
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found. LLM features will not work.")
        else:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini API configured")
            
        self.model_name = Config.GEMINI_MODEL
        
        self.system_prompt = """
        You are an expert Meeting Secretary. Your task is to listen to the audio recording and create a structured meeting summary.
        
        You MUST return your response in valid JSON format with the following structure:
        {
            "title": "A concise and descriptive title for the meeting based on the content",
            "tags": ["tag1", "tag2", "tag3"],
            "summary": "The full markdown summary..."
        }

        For the "summary" field, use the following Markdown format:
        # Meeting Summary
        
        ## 🗣️ Speakers
        *   [Speaker Name/Voice A]: [Brief description of role/tone]
        
        ## 📝 Executive Summary
        [Concise overview of the main purpose and outcomes]
        
        ## 🔑 Key Discussion Points
        *   **[Topic 1]**: [Detail] (Ref: "Direct quote...")
        *   **[Topic 2]**: [Detail] (Ref: "Direct quote...")
        
        ## ✅ Action Items
        *   [ ] [Action] - Assigned to [Name]
        
        IMPORTANT:
        1.  The output MUST be valid, parseable JSON. 
        2.  Do NOT wrap it in markdown code blocks (like ```json). Just return the raw JSON string.
        3.  Do NOT include trailing commas.
        4.  Escape any double quotes inside strings.
        5.  Identify speakers by voice if names aren't mentioned (e.g., "Speaker 1").
        6.  Extract specific technologies, project names, or key categories for the "tags" list (suggest 1-3 tags).
        """
        
    def process_audio(self, audio_path: str) -> str:
        """Process audio with retry logic."""
        if not self.api_key:
            return "Error: API Key missing."
            
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Uploading {audio_path} to Gemini (attempt {attempt + 1}/{self.max_retries})...")
                
                # Upload the audio file
                audio_file = genai.upload_file(path=audio_path)
                
                model = genai.GenerativeModel(self.model_name)
                
                logger.info("Generating summary...")
                response = model.generate_content(
                    [self.system_prompt, audio_file],
                    request_options={"timeout": Config.LLM_TIMEOUT}
                )
                
                logger.info("Summary generated successfully")
                return response.text
                
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    logger.error(f"All {self.max_retries} attempts failed")
                    return f"Error processing meeting after {self.max_retries} attempts: {e}"
