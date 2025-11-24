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
        You are an expert Meeting Secretary. Your task is to listen to the audio recording and create a professional, structured meeting summary.
        
        You MUST return your response in valid JSON format with the following structure:
        {
            "title": "Short, punchy title (max 10 words)",
            "tags": ["tag1", "tag2", "tag3"],
            "summary": "The full markdown summary..."
        }

        For the "summary" field, use the following Markdown format:
        # Meeting Summary
        
        ## Speakers
        *   [Speaker Name/Voice A]: [Brief description of role/context]
        
        ## Executive Summary
        [Concise, high-level overview of the meeting's purpose and key outcomes. Keep it professional and direct.]
        
        ## Key Discussion Points
        *   **[Topic 1]**: [Detail] (Ref: "Direct quote or timestamp if available")
        *   **[Topic 2]**: [Detail]
        
        ## Action Items
        (Only include this section if there are clear, assignable tasks. If none, omit this section entirely.)
        *   [ ] [Action] - Assigned to [Name]
        
        IMPORTANT GUARDRAILS:
        1.  **JSON Format**: The output MUST be valid, parseable JSON. Do NOT wrap it in markdown code blocks (like ```json). Just return the raw JSON string. Escape all double quotes inside strings.
        2.  **Title**: Keep the title SHORT, descriptive, and professional. Avoid generic titles like "Meeting Summary".
        3.  **Action Items**: Do NOT hallucinate action items. Only list them if explicitly mentioned or clearly implied as a next step. If none, do not include the section.
        4.  **Tags**: Extract 3-5 relevant tags (technologies, project names, key topics).
        5.  **Speakers**: Identify speakers by name if mentioned, otherwise use "Speaker 1", "Speaker 2", etc.
        6.  **Quality**: Focus on substance over fluff. Capture the core decisions and insights.
        7.  **Tone and Style**: Use a professional, informational tone. Do NOT use emojis or casual language. The summary should be suitable for business documentation.
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
