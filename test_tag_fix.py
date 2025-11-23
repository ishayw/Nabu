"""
Test the fixed tag extraction by processing a new copy of test.m4a.
This will verify that tags are now extracted even if JSON parsing partially fails.
"""

import sys
import os
import shutil
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Create a new test file
source = "test.m4a"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
test_filename = f"meeting_{timestamp}_tagtest.m4a"
test_filepath = os.path.join("recordings", test_filename)

print(f"Copying {source} to {test_filepath}...")
shutil.copy(source, test_filepath)

# Process the meeting
from app.service import MeetingService
from app.audio_recorder import AudioRecorder
from app.llm_provider import GeminiProvider
from app.database import get_meeting, get_tags

print("\nInitializing service...")
recorder = AudioRecorder(output_dir="recordings")
provider = GeminiProvider()
service = MeetingService(recorder, provider)

print(f"\nProcessing {test_filepath}...")
print("This will call the Gemini API - watch for tag extraction messages...")
print("=" * 60)

# Process
service._process_meeting(test_filepath)

print("=" * 60)
print("\nVerifying results...")
meeting = get_meeting(test_filename)
tags = get_tags(test_filename)

print(f"\nFilename: {meeting.get('filename')}")
print(f"Title: {meeting.get('title')}")
print(f"Duration: {meeting.get('duration')}s")
print(f"Tags in DB: {tags}")

if tags and len(tags) > 0:
    print(f"\n✓✓✓ SUCCESS! {len(tags)} tags were saved successfully!")
else:
    print(f"\n✗✗✗ FAILED: No tags were saved")
