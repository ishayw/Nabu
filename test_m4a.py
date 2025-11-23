import os
import shutil
import time
from app.service import MeetingService
from app.audio_recorder import AudioRecorder
from app.llm_provider import GeminiProvider

# Mock recorder
class MockRecorder:
    def start_listening(self): pass
    def stop_listening(self): pass
    def stop_recording(self): return None

def test_m4a():
    source = r"C:\Users\Ishay Wayner\Documents\projects\meeting-summarizer\test.m4a"
    dest = r"C:\Users\Ishay Wayner\Documents\projects\meeting-summarizer\recordings\test_meeting.m4a"
    
    if not os.path.exists(source):
        print(f"Source file not found: {source}")
        return

    # Copy file
    shutil.copy(source, dest)
    print(f"Copied test file to {dest}")

    # Initialize service
    recorder = MockRecorder()
    provider = GeminiProvider()
    service = MeetingService(recorder, provider)
    
    # Process
    print("Starting processing...")
    service._process_meeting(dest)
    print("Processing complete.")

if __name__ == "__main__":
    test_m4a()
