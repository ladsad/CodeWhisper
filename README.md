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

- **Code Analysis**: Calculates cyclomatic complexity, maintainability index, and detects anomalies.
- **Auto-Documentation**: Generates docstrings using **CodeT5+** fine-tuned with **QLoRA**.
- **Dashboard**: Visualizes project health and metrics.

## Model Performance

The documentation generation model (CodeT5+ small) was fine-tuned on the **CodeXGLUE** dataset (Python/Java) and achieved the following results on the training subset:

| Metric | Score |
| :--- | :--- |
| **BLEU** | 36.65 |
| **ROUGE-L** | 62.17 |
| **BERTScore** | 0.93 |

*Note: These scores represent a sanity check on the training data.*
