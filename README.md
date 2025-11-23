# Nabu 🖋️

**Nabu** (formerly Meeting Summar izer) is an intelligent local meeting assistant that records, transcribes, and summarizes your meetings automatically.

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

1.  **Run the application**:
    ```bash
    python main.py
    ```

2.  **Open the interface**:
    Navigate to `http://localhost:8000` in your browser.

3.  **Start a Meeting**:
    -   **Automatic**: Join a Google Meet, Zoom, or Teams call. Nabu will detect the audio and start recording.
    -   **Manual**: Click the "Record" button in the UI.
    -   **Upload**: Drag and drop audio files (WAV, M4A, MP3, FLAC, OGG) for processing.

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

## License

[MIT](LICENSE)
