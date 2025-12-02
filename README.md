# CodeWhisper

CodeWhisper is an intelligent tool for auto-generating documentation and analyzing code quality.

## Project Structure

- `backend/`: Python FastAPI backend.
- `frontend/`: Next.js frontend dashboard.
- `Documents/`: Project documentation.

## Getting Started

### Backend

1. Navigate to `backend/`.
2. Create virtual environment: `python -m venv venv`.
3. Activate: `.\venv\Scripts\Activate`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run server: `uvicorn main:app --reload`.

### Frontend

1. Navigate to `frontend/`.
2. Install dependencies: `npm install`.
3. Run dev server: `npm run dev`.

## Features

- **Code Analysis**: Calculates cyclomatic complexity.
- **Auto-Documentation**: (Coming soon) Generates docstrings using LLMs.
- **Dashboard**: Visualizes project health.
