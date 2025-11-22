import os
from abc import ABC, abstractmethod
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(ABC):
    @abstractmethod
    def process_audio(self, audio_path: str) -> str:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found.")
        else:
            genai.configure(api_key=self.api_key)
            
        self.model_name = "gemini-flash-latest"
        
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
        1.  The output MUST be valid JSON. Do not wrap it in markdown code blocks (like ```json). Just return the raw JSON string.
        2.  Identify speakers by voice if names aren't mentioned (e.g., "Speaker 1").
        3.  Extract specific technologies, project names, or key categories for the "tags" list (suggest 1-3 tags).
        """
        
    def process_audio(self, audio_path: str) -> str:
        if not self.api_key:
            return "Error: API Key missing."
            
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."

        print(f"Uploading {audio_path} to Gemini...")
        try:
            # Upload the audio file
            audio_file = genai.upload_file(path=audio_path)
            
            model = genai.GenerativeModel(self.model_name)
            
            print("Generating summary...")
            response = model.generate_content(
                [self.system_prompt, audio_file],
                request_options={"timeout": 600}
            )
            
            return response.text
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return f"Error processing meeting: {e}"
