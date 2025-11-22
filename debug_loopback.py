import sounddevice as sd
import sys

print(f"SoundDevice Version: {sd.__version__}")

# 1. Try WasapiSettings(loopback=True)
try:
    s = sd.WasapiSettings(loopback=True)
    print("Method 1: WasapiSettings(loopback=True) -> SUCCESS")
except Exception as e:
    print(f"Method 1: WasapiSettings(loopback=True) -> FAILED: {e}")

# 2. Try InputStream(loopback=True)
try:
    # We need a valid device index or default
    with sd.InputStream(loopback=True) as stream:
        print("Method 2: InputStream(loopback=True) -> SUCCESS")
except Exception as e:
    print(f"Method 2: InputStream(loopback=True) -> FAILED: {e}")

# 3. List WASAPI devices and try to find loopback
print("\nSearching for WASAPI devices...")
wasapi_host_id = None
for i, api in enumerate(sd.query_hostapis()):
    if 'WASAPI' in api['name']:
        wasapi_host_id = i
        break

if wasapi_host_id is not None:
    print(f"WASAPI Host API Index: {wasapi_host_id}")
    found_loopback = False
    for i, dev in enumerate(sd.query_devices()):
        if dev['hostapi'] == wasapi_host_id:
            # print(f"Dev {i}: {dev['name']} (In: {dev['max_input_channels']}, Out: {dev['max_output_channels']})")
            if 'loopback' in dev['name'].lower():
                print(f"  -> Found explicit loopback device: {i} - {dev['name']}")
                found_loopback = True
    
    if not found_loopback:
        print("  -> No explicit 'loopback' device found in list.")
else:
    print("WASAPI Host API not found.")

# 4. Try opening default output device as input
try:
    default_out = sd.default.device[1]
    print(f"\nAttempting to open default output device ({default_out}) as input...")
    with sd.InputStream(device=default_out) as stream:
         print("Method 4: Open default output as input -> SUCCESS")
except Exception as e:
    print(f"Method 4: Open default output as input -> FAILED: {e}")
