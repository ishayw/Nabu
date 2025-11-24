# Nabu 🖋️

**Nabu** (formerly Meeting Summarizer) is an intelligent local meeting assistant that records, transcribes, and summarizes your meetings automatically.

Named after the Mesopotamian god of literacy, scribes, and wisdom, Nabu acts as your personal digital scribe, ensuring you never miss a detail.

![Nabu Logo](static/logo.png)

## Features

-   **Automatic Meeting Detection**: Monitors microphone and system audio to detect when a meeting starts.
-   **Dual-Channel Recording**: Captures both your voice (Microphone) and remote participants (System Audio/Loopback).
-   **AI Summarization**: Uses Google Gemini to generate concise summaries, titles, and tags with automatic retry logic.
-   **Local Database**: Stores all meeting history locally with SQLite.
-   **Modern UI**: A premium, dark-mode interface with a "Royal Blue & Gold" theme.
-   **Privacy First**: Recordings and database are stored locally on your machine.
-   **File Upload Validation**: Automatic validation of file types and sizes for security.
-   **Pagination**: Efficient browsing of large meeting histories.
-   **Background Service**: Run permanently in the background on Windows or macOS.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ishayw/Nabu.git
    cd Nabu
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You may need to install [FFmpeg](https://ffmpeg.org/download.html) and add it to your PATH for audio processing (required for M4A/MP3 support).*

3.  **Set up Environment Variables**:
    Copy the example environment file and configure it:
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env` and add your Google Gemini API key:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```
    
    You can also customize other settings:
    - `APP_PORT`: Server port (default: 8000)
    - `MAX_FILE_SIZE_MB`: Maximum upload size (default: 500MB)
    - `CORS_ORIGINS`: Allowed CORS origins for production
    - `LLM_MAX_RETRIES`: Number of retries for API failures (default: 3)
    - See `.env.example` for all available options

## Usage

### Manual Start (Development)

1.  **Run the application**:
    ```bash
    python main.py
    ```

2.  **Open the interface**:
    Navigate to `http://localhost:8000` in your browser.

### Background Service (Production)

Run Nabu permanently in the background so it starts automatically with your system.

#### Windows

1. Open PowerShell **as Administrator**
2. Navigate to the project directory:
   ```powershell
   cd path\to\Nabu
   ```
3. Run the installation script:
   ```powershell
   .\service\windows\install.ps1
   ```
4. The service will start automatically at login

**Management Commands:**
```powershell
# Start service
Start-ScheduledTask -TaskName "NabuMeetingSummarizer"

# Stop service
Stop-ScheduledTask -TaskName "NabuMeetingSummarizer"

# Check status
Get-ScheduledTask -TaskName "NabuMeetingSummarizer"

# Uninstall
.\service\windows\uninstall.ps1
```

#### macOS

1. Open Terminal
2. Navigate to the project directory:
   ```bash
   cd path/to/Nabu
   ```
3. Make the script executable and run it:
   ```bash
   chmod +x service/macos/install.sh
   ./service/macos/install.sh
   ```
4. The service will start automatically at login

**Management Commands:**
```bash
# Check status
launchctl list | grep nabu

# Stop service
launchctl unload ~/Library/LaunchAgents/com.nabu.meeting-summarizer.plist

# Start service
launchctl load ~/Library/LaunchAgents/com.nabu.meeting-summarizer.plist

# View logs
tail -f app.log

# Uninstall
./service/macos/uninstall.sh
```

### Recording Meetings

> [!NOTE]
> **Automatic Meeting Detection** is currently in development and is **disabled by default**. The voice activity detection (VAD) mechanism is experimental and may not work reliably in all environments. For best results, use manual recording via the web interface or file uploads.
>
> To enable auto-detection (not recommended), set `AUTO_DETECTION=true` in your `.env` file.

3.  **Start a Meeting**:
    -   **Manual Recording**: Click the "Record" button in the UI to start/stop recording.
    -   **Upload**: Drag and drop audio files (WAV, M4A, MP3, FLAC, OGG) for processing.
    -   **Automatic** (experimental, disabled by default): If enabled, Nabu will detect audio and start recording automatically.

4.  **View Summaries**:
    Once the meeting ends (or you click Stop), Nabu will process the audio and display the summary, title, and tags in the history list.

## Configuration

All configuration is managed through environment variables in `.env`:

- **General**: Host, port, environment (development/production)
- **Recording**: VAD threshold, silence duration, minimum recording length
- **LLM**: API key, model, timeout, retry settings
- **Upload**: Max file size, allowed extensions
- **CORS**: Allowed origins for API requests
- **Pagination**: Page sizes for history listing

See `.env.example` for a complete list with defaults.

## Tech Stack

-   **Backend**: Python, FastAPI
-   **Frontend**: HTML, Vanilla JS
-   **Audio**: SoundDevice, SoundFile, NumPy, FFmpeg
-   **AI**: Google Gemini Flash with retry logic
-   **Database**: SQLite
-   **Logging**: Python logging with file rotation

## Recent Improvements

-   ✅ Robust M4A/MP3 duration detection using FFmpeg
-   ✅ Tag persistence with regex fallback for partial JSON failures
-   ✅ Short recording detection (< 3 seconds skips expensive API calls)
-   ✅ Centralized configuration management
-   ✅ Structured logging with file rotation  
-   ✅ File upload validation (size, type, MIME)
-   ✅ LLM retry logic with exponential backoff
-   ✅ Pagination for meeting history
-   ✅ CORS restrictions for production security
-   ✅ Background service support for Windows and macOS

## Troubleshooting

### Service won't start
- **Windows**: Check Task Scheduler for error messages
- **macOS**: Check logs with `tail -f app.log` or `launchctl list | grep nabu`

### FFmpeg not found
- Install FFmpeg and add to PATH
- **Windows**: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org)
- **macOS**: `brew install ffmpeg`

### Permission errors
- **Windows**: Run PowerShell as Administrator
- **macOS**: Check file permissions with `ls -la service/macos/`

## License

[MIT](LICENSE)
