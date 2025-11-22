import soundfile as sf
import os

filename = "meeting_20251121_172549.m4a"
path = os.path.join("recordings", filename)

print(f"Testing file: {path}")
if not os.path.exists(path):
    print("File not found!")
    exit(1)

try:
    f = sf.SoundFile(path)
    print(f"Opened successfully. Duration: {len(f) / f.samplerate}")
    f.close()
except Exception as e:
    print(f"Error opening file: {e}")
