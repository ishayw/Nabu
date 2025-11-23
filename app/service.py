import threading
import time
import os
from enum import Enum
from app.audio_recorder import AudioRecorder
# from app.llm_provider import GeminiProvider # Circular import risk? No, but not implemented yet.

class MeetingStatus(Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"

class MeetingService:
    def __init__(self, recorder: AudioRecorder, llm_provider=None):
        self.recorder = recorder
        self.llm_provider = llm_provider
        self.status = MeetingStatus.IDLE
        self.running = False
        self.monitor_thread = None
        
        # VAD Settings
        self.vad_threshold = 0.03  # RMS Threshold
        self.silence_duration = 10 # Seconds of silence to stop
        self.min_recording_duration = 10 # Minimum seconds to keep
        
        self.last_voice_time = 0
        self.start_time = 0
        self.manual_override = False # If True, auto-stop is disabled
        self.notification = None # Store temporary user messages

    def start_service(self):
        self.running = True
        self.recorder.start_listening() # Start monitoring streams
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        print("Meeting Service Started")

    def stop_service(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.recorder.stop_listening() # Stop streams
        print("Meeting Service Stopped")

    def start_recording(self, manual=False):
        if self.status == MeetingStatus.RECORDING:
            return
            
        print("Starting Recording...")
        self.status = MeetingStatus.RECORDING
        self.manual_override = manual
        self.start_time = time.time()
        self.last_voice_time = time.time()
        self.recorder.start_recording()

    def stop_recording(self):
        if self.status != MeetingStatus.RECORDING:
            return

        print("Stopping Recording...")
        filename = self.recorder.stop_recording()
        self.status = MeetingStatus.PROCESSING
        self.manual_override = False
        
        # Trigger processing in a separate thread
        if filename:
            threading.Thread(target=self._process_meeting, args=(filename,)).start()

    def _process_meeting(self, filename):
        print(f"Processing meeting: {filename}")
        # Import here to avoid circular dependency if needed, or use self.llm_provider
        try:
            # We need to parse the JSON response here as per the new requirement
            import json
            from app.database import add_meeting, add_tag
            from datetime import datetime
            
            # Get duration
            try:
                import soundfile as sf
                # soundfile supports WAV, FLAC, OGG, but often not M4A/MP3 depending on libs
                f = sf.SoundFile(filename)
                duration = len(f) / f.samplerate
                f.close()
            except Exception as e:
                # print(f"Could not determine duration with soundfile: {e}")
                # This is expected for M4A/MP3 if libs aren't present. 
                # We can try to use os.path.getsize as a proxy or just ignore.
                duration = 0
            
            # Only check duration if we successfully got it
            if duration > 0 and duration < self.min_recording_duration:
                msg = f"Recording too short ({duration:.1f}s). Discarded."
                print(msg)
                self.notification = {"type": "warning", "message": msg}
                os.remove(filename)
                self.status = MeetingStatus.IDLE
                return

            response_text = self.llm_provider.process_audio(filename)
            
            # Parse JSON
            title = None
            tags = []
            summary = response_text
            
            try:
                import re
                
                # Debug logging
                try:
                    with open("debug_log.txt", "w", encoding="utf-8") as log:
                        log.write(f"Raw Response:\n{response_text}\n\n")
                except Exception as e:
                    print(f"Failed to write log: {e}")

                cleaned_text = response_text.strip()
                
                # Strategy 1: Remove Markdown Code Blocks
                if "```" in cleaned_text:
                    # Simple split to get content between first and last ```
                    parts = cleaned_text.split("```")
                    if len(parts) >= 3:
                        # parts[0] is before, parts[1] is content (maybe with 'json' prefix), parts[2] is after
                        candidate = parts[1]
                        if candidate.startswith("json"):
                            candidate = candidate[4:]
                        cleaned_text = candidate.strip()
                
                # Strategy 2: Regex for JSON object (fallback or refinement)
                # We look for the outermost {}
                json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
                if json_match:
                    cleaned_text = json_match.group(0)
                
                try:
                    with open("debug_log.txt", "a", encoding="utf-8") as log:
                        log.write(f"Extracted Text:\n{cleaned_text}\n\n")
                except: pass

                # Strategy 3: Fix common JSON errors
                # We used to replace \n with \\n here, but that breaks pretty-printed JSON.
                # Only do it if strictly necessary or use a better regex.
                # For now, let's trust the LLM or use the fallbacks.
                
                try:
                    data = json.loads(cleaned_text)
                except json.JSONDecodeError:
                    # Try one more time with strict=False if available
                    # Sometimes trailing commas are the issue
                    cleaned_text_fixed = re.sub(r',\s*\}', '}', cleaned_text)
                    cleaned_text_fixed = re.sub(r',\s*\]', ']', cleaned_text_fixed)
                    try:
                        data = json.loads(cleaned_text_fixed)
                    except:
                        # Fallback: Try ast.literal_eval for Python-style dicts (single quotes)
                        try:
                            import ast
                            # We need to be careful with ast.literal_eval on arbitrary strings, but for this it's okay
                            # It expects python syntax, so true/false must be True/False, null is None
                            # We can try to replace them
                            py_text = cleaned_text.replace("true", "True").replace("false", "False").replace("null", "None")
                            data = ast.literal_eval(py_text)
                            if not isinstance(data, dict):
                                raise ValueError("Not a dict")
                        except:
                            raise # Re-raise original error if this fails too

                title = data.get("title")
                tags = data.get("tags", [])
                summary = data.get("summary", response_text)
                
            except Exception as e:
                try:
                    with open("debug_log.txt", "a", encoding="utf-8") as log:
                        log.write(f"JSON Error: {e}\n")
                except: pass
                print(f"Failed to parse JSON: {e}")
                summary = response_text
                title = "Meeting " + datetime.now().strftime("%Y-%m-%d %H:%M") # Fallback title
            
            # Save to DB
            # Save to DB
            # Robust timestamp parsing
            base_name = os.path.basename(filename)
            name_without_ext = os.path.splitext(base_name)[0]
            # Expected format: meeting_YYYYMMDD_HHMMSS
            if name_without_ext.startswith("meeting_"):
                timestamp_str = name_without_ext.replace("meeting_", "")
            else:
                timestamp_str = name_without_ext

            try:
                dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                created_at_fmt = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Fallback to file modification time or current time
                try:
                    mtime = os.path.getmtime(filename)
                    created_at_fmt = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    created_at_fmt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            result = add_meeting(
                filename=os.path.basename(filename),
                created_at=created_at_fmt,
                duration=duration,
                summary_text=summary,
                title=title
            )
            
            if result is None:
                # Meeting already exists (e.g. from upload), so update it
                print(f"Meeting exists, updating: {title}")
                from app.database import update_meeting
                update_meeting(
                    filename=os.path.basename(filename),
                    title=title,
                    summary_text=summary,
                    duration=duration
                )
            
            for tag in tags:
                add_tag(os.path.basename(filename), tag)
                
            print(f"Meeting processed and saved: {title}")
            
        except Exception as e:
            print(f"Error processing meeting: {e}")
            import traceback
            traceback.print_exc()
            
        self.status = MeetingStatus.IDLE

    def _monitor_loop(self):
        counter = 0
        trigger_count = 0
        REQUIRED_TRIGGER_FRAMES = 5 
        
        while self.running:
            rms = self.recorder.get_rms()
            now = time.time()
            
            counter += 1
            if counter % 10 == 0: 
                pass
            
            if rms > self.vad_threshold:
                self.last_voice_time = now
                
                if self.status == MeetingStatus.IDLE and not self.manual_override:
                    trigger_count += 1
                    if trigger_count >= REQUIRED_TRIGGER_FRAMES:
                        print(f"Voice detected. Starting recording. RMS: {rms:.4f}")
                        self.start_recording()
                        trigger_count = 0
                else:
                    trigger_count = 0 
            else:
                trigger_count = 0 
            
            if self.status == MeetingStatus.RECORDING:
                if not self.manual_override:
                    if now - self.last_voice_time > self.silence_duration:
                        if now - self.start_time > self.min_recording_duration:
                            print("Silence detected. Stopping.")
                            self.stop_recording()
            
            time.sleep(0.1)
