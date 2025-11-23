# Nabu Product Roadmap

This document outlines the planned features and improvements for Nabu.

## Phase 1: Core Stability & User Experience (Immediate Focus)
**Goal:** Fix existing bugs and make the application look and feel premium.

- [ ] **Reliability & Performance**
    - [ ] Fix "Audio file not found" errors and race conditions in recording.
    - [ ] Resolve "Invalid sample rate" errors during device switching or startup.
    - [ ] Ensure database stability when recording and viewing history simultaneously.
- [ ] **UI/UX Improvements**
    - [ ] **Visual Polish:** Implement the "Royal Blue & Gold" theme consistently.
    - [ ] **Layout:** Fix spacing and padding in the meeting list.
    - [ ] **Typography:** Fix long meeting titles truncating or breaking layout.
    - [ ] **Feedback:** Add visual indicators for "Recording", "Processing", and "Error" states.

## Phase 2: Enhanced Input & Management (Short Term)
**Goal:** Allow users to do more with their data and support more sources.

- [ ] **New Audio Sources**
    - [ ] **YouTube Import:** Input a YouTube URL to download and summarize the audio.
    - [ ] **File Upload:** Manually upload existing .mp3/.wav/.m4a files for summarization.
- [ ] **Meeting Management**
    - [ ] **Search:** Full-text search for meeting titles, summaries, and transcripts.
    - [ ] **Filtering:** Filter history by date range, tags, or duration.
    - [ ] **Delete:** Ability to delete meetings and their audio files from the UI.
- [ ] **Export Options**
    - [ ] Export summary to Markdown (.md) and Text (.txt).
    - [ ] Copy summary to clipboard with one click.

## Phase 3: Advanced AI & Workflow (Medium Term)
**Goal:** Transform Nabu from a recorder into an intelligent assistant.

- [ ] **Real-Time Features**
    - [ ] Live transcription view while recording.
    - [ ] Real-time keyword highlighting during meetings.
- [ ] **Advanced Summarization**
    - [ ] **Speaker Identification:** Distinguish between different speakers in the transcript.
    - [ ] **Action Items:** Automatically extract and list action items/todos.
    - [ ] **Multi-language:** Support for transcribing and summarizing non-English meetings.
    - [ ] **Chat with Meeting:** "Ask Nabu" interface to query specific details from a meeting.

## Phase 4: System Integration (Long Term)
**Goal:** Deep integration with the user's desktop environment.

- [ ] **Calendar Sync:** Connect to Google/Outlook Calendar to auto-label recordings.
- [ ] **System Tray App:** Run in the background with a quick-access menu.
- [ ] **Global Hotkeys:** Start/Stop recording from anywhere in the OS.
