<img align="left" width="80" height="80" src="frontend/public/icon.png">

# ZokuZoku Web App
ZokuZoku Web App is a standalone, web-based port of the ZokuZoku VSCode extension. It allows translators to view and edit UM:PD story timelines directly in a browser, independent of any IDE.

> [!WARNING]
> **PROTOTYPE ("SHELL") RELEASE**
> This project is currently a **functional prototype**.
> *   **Core Capability**: It can scan your game directory, list stories, and load them into the editor.
> *   **Missing Features**: IPC (Communication with the running game), Audio playback, and advanced editing features are currently **under development**.
> *   **Objective**: This release serves as a foundation for porting the full ZokuZoku experience to the web.
>
> For a detailed breakdown of missing features and the porting plan, see [ROADMAP.md](ROADMAP.md).
>
> *Always backup your data before using this tool.*

# Features
- **Standalone Web Experience:** Runs entirely in your browser using a local backend. no VSCode required.
- **No preprocessing or postprocessing:** All data used by ZokuZoku is dynamically generated the moment you access it. It keeps itself up-to-date with the game's assets without manual actions. Translated data is saved in the exact format Hachimi uses.
- **User friendly interface:** Provides tree views that list translatable assets in a logical manner. The custom editor resembles the original VSCode interface, ensuring a familiar experience for existing users.
- **Streamlined editing:** Accurate story previews with Hachimi's auto wrapping system.
- **Powered by Modern Web Tech:** Built with [Svelte](https://svelte.dev/) and [FastAPI](https://fastapi.tiangolo.com/), replacing the VSCode extension host with a lightweight, dedicated web stack.

# Installation & Getting Started

### Prerequisites
- **OS**: Linux (Primary support), Windows/macOS (Experimental)
- **Python**: 3.10 or later
- **Node.js**: 18 or later (with `pnpm`)
- **Game Data**: UM:PD (DMM/Steam JP) installed locally.

### 1. Start the Backend
The backend acts as the bridge to your local game files and Unity assets.

```bash
cd backend
python3 -m venv venv
source venv/bin/activate.fish # or .bash / .ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*Port: 8000*

### 2. Start the Frontend
The frontend provides the visual editor interface.

```bash
cd frontend
pnpm install
pnpm dev
```
*Port: 5173*

### 3. Usage
Open `http://localhost:5173` in your browser.
- The app will attempt to automatically detect your game installation.
- Use the **Story Browser** to find and select a story.
- The story will load in the editor, ready for translation.

# Development
*Please use the pnpm package manager while working on this project.*

For detailed setup instructions, architecture overview, and contribution guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).

# License
[GNU GPLv3](LICENSE)
