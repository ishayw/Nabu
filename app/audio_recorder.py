import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import queue
import time
import os
import platform
import re
from datetime import datetime

class AudioRecorder:
    def __init__(self, output_dir="recordings", samplerate=16000, channels=1):
        self.output_dir = output_dir
        self.samplerate = samplerate
        self.channels = channels
        self.recording = False
        self.mic_queue = queue.Queue()
        self.sys_queue = queue.Queue()
        self.mic_stream = None
        self.sys_stream = None
        self.writer_thread = None
        self.filename = None
        self.current_mic_rms = 0.0
        self.current_sys_rms = 0.0
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _get_wasapi_loopback_device(self):
        """Finds the default output device specifically on WASAPI for loopback."""
        if platform.system() != 'Windows':
            return None
            
        try:
            wasapi_host_id = None
            for i, api in enumerate(sd.query_hostapis()):
                if 'WASAPI' in api['name']:
                    wasapi_host_id = i
                    break
            
            if wasapi_host_id is None:
                return None

            # Find default output device index
            # sd.default.device is [input_idx, output_idx]
            default_out_idx = sd.default.device[1]
            
            # Verify it's on WASAPI or find the WASAPI equivalent
            dev_info = sd.query_devices(default_out_idx)
            if dev_info['hostapi'] == wasapi_host_id:
                return default_out_idx
                
            # If default is not WASAPI, search for the WASAPI device with the same name
            # or just the first WASAPI output device.
            for i, dev in enumerate(sd.query_devices()):
                if dev['hostapi'] == wasapi_host_id and dev['max_output_channels'] > 0:
                    # This is a candidate. In a perfect world we match the name.
                    # For now, let's try to find the one that looks like the default.
                    if dev['name'] == dev_info['name']:
                        return i
            
            # Fallback: just return the default and hope sounddevice handles it or find first WASAPI output
            for i, dev in enumerate(sd.query_devices()):
                 if dev['hostapi'] == wasapi_host_id and dev['max_output_channels'] > 0:
                     return i
                     
            return None
            
        except Exception as e:
            print(f"Error finding loopback device: {e}")
            return None

    def _mic_callback(self, indata, frames, time, status):
        if status:
            print(f"Mic Status: {status}")
        self.mic_queue.put(indata.copy())
        # Calculate RMS for VAD
        if len(indata) > 0:
            self.current_mic_rms = np.sqrt(np.mean(indata**2))

    def _sys_callback(self, indata, frames, time, status):
        if status:
            print(f"Sys Status: {status}")
        self.sys_queue.put(indata.copy())
        # Calculate RMS for VAD (System audio)
        if len(indata) > 0:
            self.current_sys_rms = np.sqrt(np.mean(indata**2))

    def _writer(self):
        """Combines streams and writes to file."""
        file = None
        print("Writer thread started.")
        try:
            while (self.mic_stream and self.mic_stream.active) or (self.sys_stream and self.sys_stream.active):
                try:
                    mic_data = self.mic_queue.get(timeout=0.5)
                except queue.Empty:
                    if not self.recording: # If not recording and no data, just continue/break
                         if not ((self.mic_stream and self.mic_stream.active) or (self.sys_stream and self.sys_stream.active)):
                             break
                         continue
                    mic_data = None # Handle later

                try:
                    sys_data = self.sys_queue.get(timeout=0.1)
                except queue.Empty:
                    sys_data = None

                # If we have neither, continue
                if mic_data is None and sys_data is None:
                    continue
                    
                # Handle missing data by creating silence
                if mic_data is not None and sys_data is None:
                    sys_data = np.zeros_like(mic_data)
                elif sys_data is not None and mic_data is None:
                    mic_data = np.zeros_like(sys_data)
                
                # Resize if mismatch
                if len(mic_data) != len(sys_data):
                    min_len = min(len(mic_data), len(sys_data))
                    mic_data = mic_data[:min_len]
                    sys_data = sys_data[:min_len]

                if self.recording:
                    if file is None and self.filename:
                        print(f"Opening file: {self.filename}")
                        file = sf.SoundFile(self.filename, mode='w', samplerate=self.samplerate, channels=self.channels)
                    
                    if file:
                        # Mix audio: simple addition and clip
                        mixed = mic_data + sys_data
                        mixed = np.clip(mixed, -1.0, 1.0)
                        file.write(mixed)
                else:
                    # Not recording, close file if open
                    if file:
                        print("Closing file (recording stopped).")
                        file.close()
                        file = None
                        
        except Exception as e:
            print(f"Error in writer: {e}")
        finally:
            if file:
                file.close()
            print("Writer thread finished.")

    def _normalize_device_name(self, name):
        """Cleans up device names to help with de-duplication."""
        # 1. Fix specific quirks like " )" -> ")"
        name = name.replace(" )", ")")
        
        # 2. Remove generic driver suffixes
        # Regex explanation:
        # \s+ : match leading whitespace
        # \( : match opening paren
        # ... : match content
        # \) : match closing paren
        name = re.sub(r'\s+\(Realtek\(R\) Audio\)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+\(Realtek HD Audio.*\)', '', name, flags=re.IGNORECASE)
        # Aggressive Intel regex: remove everything starting with (Intel
        name = re.sub(r'\s+\(Intel.*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+\(High Definition Audio.*\)', '', name, flags=re.IGNORECASE)
        
        # 3. Remove empty parens "()" which often indicate ghost devices
        name = name.replace("()", "")
        
        # 4. Remove trailing/leading whitespace
        return name.strip()

    def list_input_devices(self):
        """Lists available input devices, filtering duplicates."""
        devices = []
        try:
            # Query all devices
            all_devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            
            unique_devices = {} # normalized_name -> {priority, device_info}
            
            # Priority map (lower is better)
            api_priority = {
                'Windows WASAPI': 0,
                'MME': 1,             # MME is often more compatible/stable than DirectSound for names
                'Windows DirectSound': 2,
                # 'Windows WDM-KS': 3 # Exclude WDM-KS entirely as it lists ghost/internal pins
            }

            for i, dev in enumerate(all_devices):
                # Filter for input devices (max_input_channels > 0)
                if dev['max_input_channels'] > 0:
                    api_name = host_apis[dev['hostapi']]['name']
                    
                    # Skip WDM-KS entirely
                    if 'WDM-KS' in api_name:
                        continue

                    # Skip virtual system mappers to reduce clutter
                    if "Sound Mapper" in dev['name'] or "Primary Sound Capture" in dev['name']:
                        continue
                        
                    raw_name = dev['name']
                    norm_name = self._normalize_device_name(raw_name)
                    
                    # Skip if normalization resulted in empty name
                    if not norm_name:
                        continue

                    # Determine priority
                    priority = api_priority.get(api_name, 99)
                    
                    # Logic:
                    # 1. If we haven't seen this normalized name, add it.
                    # 2. If we have, but this one has a better priority (lower), replace it.
                    
                    if norm_name not in unique_devices or priority < unique_devices[norm_name]['priority']:
                        unique_devices[norm_name] = {
                            'priority': priority,
                            'data': {
                                "index": i,
                                "name": norm_name, # Use normalized name for cleaner UI
                                "channels": dev['max_input_channels']
                            }
                        }
            
            # Convert to list and sort by name
            devices = [v['data'] for v in unique_devices.values()]
            devices.sort(key=lambda x: x['name'])
            
        except Exception as e:
            print(f"Error listing devices: {e}")
        return devices

    def set_device(self, device_index):
        """Sets the microphone device index."""
        self.device_index = device_index
        # If currently listening, restart to apply change
        if self.mic_stream and self.mic_stream.active:
            self.stop_listening()
            self.start_listening()

    def start_listening(self):
        """Starts the audio streams for monitoring (VAD) without recording to file."""
        if (self.mic_stream and self.mic_stream.active) or (self.sys_stream and self.sys_stream.active):
            return

        self.mic_queue = queue.Queue()
        self.sys_queue = queue.Queue()
        self.current_mic_rms = 0.0
        self.current_sys_rms = 0.0

        try:
            # Mic Stream
            print(f"Starting Mic Stream on device index: {getattr(self, 'device_index', None)}")
            self.mic_stream = sd.InputStream(
                device=getattr(self, 'device_index', None), # Use selected device or default
                callback=self._mic_callback,
                channels=self.channels,
                samplerate=self.samplerate
            )
            self.mic_stream.start()

            # System Stream (Loopback)
            wasapi_dev = self._get_wasapi_loopback_device()
            if wasapi_dev is not None:
                print(f"Attempting to open Loopback on device {wasapi_dev}...")
                try:
                    # Method 1: WasapiSettings(loopback=True)
                    self.sys_stream = sd.InputStream(
                        device=wasapi_dev,
                        callback=self._sys_callback,
                        channels=self.channels,
                        samplerate=self.samplerate,
                        extra_settings=sd.WasapiSettings(loopback=True)
                    )
                    self.sys_stream.start()
                    print("Loopback started (Method 1).")
                except TypeError:
                    print("WasapiSettings(loopback=True) failed. Trying Method 2...")
                    try:
                        # Method 2: InputStream(loopback=True)
                        self.sys_stream = sd.InputStream(
                            device=wasapi_dev,
                            callback=self._sys_callback,
                            channels=self.channels,
                            samplerate=self.samplerate,
                            loopback=True
                        )
                        self.sys_stream.start()
                        print("Loopback started (Method 2).")
                    except Exception as e2:
                        print(f"Loopback Method 2 failed: {e2}")
                        print("Continuing with Microphone only.")
                except Exception as e:
                    print(f"Loopback failed: {e}")
                    print("Continuing with Microphone only.")
            else:
                print("No WASAPI device found. Monitoring Mic only.")

            # Start writer thread
            self.writer_thread = threading.Thread(target=self._writer)
            self.writer_thread.start()
            print("Started listening (monitoring)...")

        except Exception as e:
            print(f"Failed to start listening: {e}")
            # Clean up if partially started
            self.stop_listening()

    def start_recording(self):
        """Enables writing to file."""
        if self.recording:
            return

        if not (self.mic_stream and self.mic_stream.active):
            self.start_listening()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = os.path.join(self.output_dir, f"meeting_{timestamp}.wav")
        self.recording = True
        print(f"Started recording to {self.filename}")

    def stop_recording(self):
        """Stops writing to file but keeps listening."""
        if not self.recording:
            return

        self.recording = False
        print(f"Stopped recording. Saved to {self.filename}")
        return self.filename

    def stop_listening(self):
        """Stops streams and writer thread."""
        self.recording = False
        
        if self.mic_stream:
            try:
                self.mic_stream.stop()
                self.mic_stream.close()
            except Exception as e:
                print(f"Error closing mic stream: {e}")
            self.mic_stream = None
        
        if self.sys_stream:
            try:
                self.sys_stream.stop()
                self.sys_stream.close()
            except Exception as e:
                print(f"Error closing sys stream: {e}")
            self.sys_stream = None
            
    def get_rms(self):
        # Return the maximum activity from either mic or system
        return max(self.current_mic_rms, self.current_sys_rms)
