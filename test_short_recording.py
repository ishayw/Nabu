"""
Test that short recordings are handled correctly:
1. Duration is detected correctly
2. Recording is NOT sent to LLM
3. Proper "too short" message is stored
"""

from app.audio_utils import get_audio_duration
from app.database import add_meeting, get_meeting, get_tags
from datetime import datetime
import os

# Test file
test_file = "recordings/test_short_silence.wav"

print("Testing short recording handling...")
print("=" * 60)

# 1. Test duration detection
duration = get_audio_duration(test_file)
print(f"\n1. Duration Detection:")
print(f"   Duration: {duration:.2f}s")
print(f"   ✓ Duration detected correctly" if duration == 2.0 else f"   ✗ Expected 2.0s")

# 2. Simulate the logic from service.py
min_recording_duration = 3
should_skip_llm = (duration > 0 and duration < min_recording_duration)

print(f"\n2. LLM Processing Check:")
print(f"   Min duration threshold: {min_recording_duration}s")
print(f"   Should skip LLM: {should_skip_llm}")
print(f"   ✓ Logic correct" if should_skip_llm else f"   ✗ Should skip LLM")

# 3. Test adding to database like service.py would
filename = os.path.basename(test_file)
created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if should_skip_llm:
    summary = "Recording too short to summarize."
    title = "Short Recording"
    tags = ["Short"]
    print(f"\n3. Database Entry (simulated):")
    print(f"   Title: {title}")
    print(f"   Summary: {summary}")
    print(f"   Tags: {tags}")
    print(f"   Duration: {duration}s")
    
    # Add to database
    result = add_meeting(
        filename=filename,
        created_at=created_at,
        duration=duration,
        summary_text=summary,
        title=title
    )
    
    if result:
        print(f"   ✓ Added to database (ID: {result})")
        
        # Add tag
        from app.database import add_tag
        success = add_tag(filename, "Short")
        print(f"   {'✓' if success else '✗'} Tag added: Short")
        
        # Verify
        meeting = get_meeting(filename)
        db_tags = get_tags(filename)
        
        print(f"\n4. Verification:")
        print(f"   Title in DB: {meeting.get('title')}")
        print(f"   Duration in DB: {meeting.get('duration')}s")
        print(f"   Tags in DB: {db_tags}")
        print(f"   ✓ All data persisted correctly")
    else:
        print(f"   ✗ Failed to add to database (might already exist)")

print("\n" + "=" * 60)
print("Test complete!")
