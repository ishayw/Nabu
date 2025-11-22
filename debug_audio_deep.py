import sounddevice as sd

def debug_devices_deep():
    print("Deep Device Inspection:")
    print("=" * 80)
    
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            api_name = hostapis[dev['hostapi']]['name']
            name = dev['name']
            print(f"Index: {i}")
            print(f"  Name (Raw): {repr(name)}")
            print(f"  API: {api_name}")
            print(f"  Channels: {dev['max_input_channels']}")
            print(f"  Sample Rate: {dev['default_samplerate']}")
            print("-" * 40)

if __name__ == "__main__":
    debug_devices_deep()
