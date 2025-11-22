from app.audio_recorder import AudioRecorder
import time
import os

def test_recording():
    print("Testing Audio Recording (Mic + System)...")
    print("Please play some audio (e.g., YouTube) and speak into the microphone.")
    print("Recording for 5 seconds...")
    
    recorder = AudioRecorder()
    
    # Start streams
    recorder.start_listening()
    
    # Start recording to file
    recorder.start_recording()
    
    time.sleep(5)
    
    # Stop
    filename = recorder.stop_recording()
    recorder.stop_listening()
    
    print("-" * 50)
    print(f"Recording saved to: {filename}")
    print("Please play this file to verify you can hear BOTH your voice and the system audio.")
    print("-" * 50)

if __name__ == "__main__":
    test_recording()
