from app.audio_recorder import AudioRecorder

def test_recorder():
    print("Testing AudioRecorder Device Listing (Cleaned):")
    print("-" * 80)
    
    recorder = AudioRecorder()
    devices = recorder.list_input_devices()
    
    print(f"{'Idx':<4} {'Name':<50} {'Ch':<4}")
    print("-" * 80)
    
    for dev in devices:
        print(f"{dev['index']:<4} {dev['name'][:48]:<50} {dev['channels']:<4}")

if __name__ == "__main__":
    test_recorder()
