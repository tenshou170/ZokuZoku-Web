# Porting Roadmap: ZokuZoku Web App

**Goal**: Achieve 100% feature parity with the original ZokuZoku VSCode extension to allow for its retirement. The web application is designed to be a standalone, fully functional replacement.

## Current State vs. Target
| Feature | Original Extension | Web App (Current Prototype) | Target Goal |
| :--- | :--- | :--- | :--- |
| **Story Browsing** | File-system based | Basic scanning | Full navigation + specific path opening |
| **Story Editing** | Full Tree Editor | Basic Tree Editor | Complete parity (incl. all slot types) |
| **Preview** | Live Preview | **Mock / Partial** | Live Preview (Text + Audio) |
| **IPC (Hachimi)** | Direct Pipe/Socket | **Missing** | Backend Proxy to Game IPC |
| **Audio** | Native Decoder (criCodecs) | **Missing** | Backend Decoder (ffmpeg/vgmstream) → Web Audio |
| **State** | VSCode Memento | LocalStorage | Robust Persistence |

## Remaining Work
The following key features must be ported to complete the transition:

### 1. IPC Implementation (In-Game Control)
The original extension communicated with **Hachimi** (the game hook) to control the game directly (e.g., "Goto Block").
*   **Need**: A mechanism for the Web App backend to send commands to the running game process via sockets or named pipes.

### 2. Audio & Asset Support
The extension decoded game audio files (`.hca`, `.adx`) natively using a C++ module (`criCodecs`).
*   **Need**: Server-side decoding (likely via `vgmstream` or `ffmpeg`) to stream standard audio (WAV/MP3) to the browser for playback.

### 3. Advanced Editor Features
The prototype supports basic viewing and editing.
*   **Need**: Support for all specific text slot types (`GenericSlot`, `ChoiceSlot`, etc.) and a robust "Save" functionality that writes changes back to the game's data files.

### 4. Application Packaging
*   **Need**: Eventually wrapping the web application in **Electron** or **Tauri** to provide a seamless "Desktop App" experience similar to VSCode.
