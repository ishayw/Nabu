# Nabu Product Roadmap

This document outlines the development roadmap for Nabu (formerly Meeting Summarizer). It is a living document and will evolve as the project progresses.

## Phase 1: Stabilization & Core Foundation (Current Focus)
**Goal:** Ensure the core recording and summarization loop is rock-solid and the UI is polished.

- [ ] **Core Reliability**
    - [ ] Fix "Audio file not found" race conditions in `AudioRecorder`.
    - [ ] Verify SQLite concurrency safety for parallel recording/writing.
    - [ ] Add robust error handling for audio device disconnection.
- [ ] **UI/UX Polish**
    - [ ] Improve meeting list layout (spacing, padding).
    - [ ] Fix long title truncation/wrapping issues.
    - [ ] Finalize "Royal Blue & Gold" theme implementation.
    - [ ] Create and integrate final logo and creative assets.
- [ ] **Project Structure & Roles**
    - [ ] Define clear roles (Frontend, Backend, UX, QA) in `roles/`.
    - [ ] Establish collaboration workflows (`collaboration.md`).

## Phase 2: Feature Expansion (Next Up)
**Goal:** Add value through new input methods and better data management.

- [ ] **External Sources**
    - [ ] Integrate YouTube Audio Downloader as a first-class feature (Import from URL).
    - [ ] Allow manual upload of existing audio files for summarization.
- [ ] **Data Management**
    - [ ] Search functionality for meeting history (by title, tag, content).
    - [ ] Filter meetings by date range or tags.
    - [ ] Delete meetings (and associated audio files) from the UI.
- [ ] **Export & Sharing**
    - [ ] Export summaries to Markdown and PDF.
    - [ ] "Copy to Clipboard" button for summaries.

## Phase 3: Advanced Intelligence & Integration (Future)
**Goal:** Make Nabu a proactive and seamless assistant.

- [ ] **Real-Time Capabilities**
    - [ ] Live transcription display during recording.
    - [ ] Real-time keyword spotting/highlighting.
- [ ] **Deeper Integration**
    - [ ] Calendar integration (Google Calendar, Outlook) to auto-tag meetings.
    - [ ] Desktop Application wrapper (Electron/Tauri) for system tray access and global shortcuts.
- [ ] **Advanced AI**
    - [ ] Multi-language support (transcription and translation).
    - [ ] "Ask Nabu" - Chat interface to query your meeting database (RAG).
    - [ ] Speaker diarization (identifying who said what).

## Infrastructure & Quality
- [ ] Set up automated tests (Unit tests for backend, E2E for flow).
- [ ] CI/CD pipeline for automated testing and linting.
