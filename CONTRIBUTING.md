# Contributing to ZokuZoku Web App

Thank you for your interest in contributing to the ZokuZoku Web App!
This document provides guidelines and instructions for setting up your development environment and submitting contributions.

## Project Structure

The project is a monorepo-style setup split into two distinct parts:

*   **`backend/`**: A Python application using **FastAPI**.
    *   Handles file system access (Game Data).
    *   Wraps `UnityPy` for asset extraction.
    *   Exposes a REST API for the frontend.
*   **`frontend/`**: A **Svelte** single-page application (SPA).
    *   Provides the user interface (Story Browser, Editor).
    *   Communicates with the backend via HTTP.
    *   Replaces the original VSCode extension webviews.

## Development Setup

### Prerequisites
*   **Python 3.10+** (Recommend managing with `pyenv` or system package manager)
*   **Node.js 18+** & **pnpm** (Strictly enforced)
*   **Git**
*   **UM:PD game** (DMM/Steam JP version) installed locally for testing.

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate (Choose one depending on your shell)
source venv/bin/activate.fish  # Fish
# source venv/bin/activate     # Bash/Zsh
# .\venv\Scripts\Activate.ps1  # PowerShell

# Install dependencies
pip install -r requirements.txt

# Run server (Auto-reloads on change)
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies using pnpm
pnpm install

# Run development server
pnpm dev
```
Open `http://localhost:5173` to view the app.

## Workflow & Coding Standards

### Python (Backend)
*   **Code Style**: Follow PEP 8.
*   **Type Hints**: Use python type hints where possible.
*   **Dependencies**: If you add a new library, update `requirements.txt` (`pip freeze > requirements.txt`).

### TypeScript / Svelte (Frontend)
*   **Package Manager**: Use **pnpm** only. Do not use `npm` or `yarn`.
*   **Linting**: Run `pnpm check` to catch TypeScript errors before committing.
*   **Component Style**: styling should generally be scoped within the `.svelte` file or use shared CSS variables.

### Commit Messages
*   Use clear, descriptive titles.
*   Examples:
    *   `feat: Add file picker for story loading`
    *   `fix: Game path detection on Windows`
    *   `docs: Update contribution guide`

## Submission Guidelines

1.  **Fork** the repository.
2.  Create a **Feature Branch** (`git checkout -b feat/my-cool-feature`).
3.  Commit your changes.
4.  Push to your fork (`git push origin feat/my-cool-feature`).
5.  Open a **Pull Request** targeting the `main` branch.

### Review Process
*   Ensure your code builds locally (`pnpm check` passed).
*   Verify functionality with a real game installation if possible.
*   Provide a description of your changes in the PR.
