"""
Test uploading a file to verify the entire pipeline works with the fixes.
This simulates what happens when a file is uploaded via the web interface.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Copy test.m4a to a new filename to test fresh processing
import shutil
from datetime import datetime

source = "test.m4a"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
test_filename = f"meeting_{timestamp}_test.m4a"
test_filepath = os.path.join("recordings", test_filename)

print(f"Copying {source} to {test_filepath}...")
shutil.copy(source, test_filepath)

# Now simulate the processing
from app.service import MeetingService
from app.audio_recorder import AudioRecorder
from app.llm_provider import GeminiProvider
from app.database import get_meeting, get_tags

print("\nInitializing service...")
recorder = AudioRecorder(output_dir="recordings")
provider = GeminiProvider()
service = MeetingService(recorder, provider)

print(f"\nProcessing {test_filepath}...")
print("This will call the Gemini API and may take a minute...")

# Process the meeting
service._process_meeting(test_filepath)

print("\nVerifying results...")
meeting = get_meeting(test_filename)
tags = get_tags(test_filename)

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60)
print(f"Filename: {meeting.get('filename')}")
print(f"Title: {meeting.get('title')}")
print(f"Duration: {meeting.get('duration')}s ({meeting.get('duration')/60:.1f} min)")
print(f"Tags: {tags}")
print(f"Summary preview: {meeting.get('summary_text', '')[:200]}...")

if tags:
    print(f"\n✓ Tags were saved successfully!")
else:
    print(f"\n✗ WARNING: No tags were saved")

print("\n" + "=" * 60)
