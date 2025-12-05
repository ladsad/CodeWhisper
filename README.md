# CodeWhisper

CodeWhisper is an intelligent tool for auto-generating documentation and analyzing code quality.

## Project Structure

- `backend/`: Python FastAPI backend.
- `frontend/`: Next.js frontend dashboard.
- `vscode-extension/`: VS Code extension for IDE integration.
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

### Streamlit Dashboard

1. Navigate to `backend/`.
2. Run: `streamlit run dashboard/app.py`.

### VS Code Extension

1. Navigate to `vscode-extension/`.
2. Install dependencies: `npm install`.
3. Compile: `npm run compile`.
4. Press `F5` to launch Extension Development Host.
5. Right-click on code and select "CodeWhisper: Generate Documentation".

## Features

- **Code Analysis**: Calculates cyclomatic complexity, maintainability index, and detects anomalies.
- **Auto-Documentation**: Generates docstrings using **CodeT5+** fine-tuned with **QLoRA**.
- **Dashboard**: Visualizes project health and metrics (Streamlit MVP).
- **VS Code Extension**: Right-click context menu for real-time documentation generation.

## Model Training

The documentation generation model uses **CodeT5-small** fine-tuned on **CodeXGLUE** (Python/Java) with QLoRA.

### Training on Kaggle

Use `backend/ml/kaggle_train.ipynb` for training on Kaggle's free T4 GPU.

### Hyperparameters

| Parameter | Value |
| :--- | :--- |
| Batch Size | 4 |
| Gradient Accumulation | 4 |
| Learning Rate | 2e-5 |
| Epochs | 2-3 |
| Max Seq Length | 512 |

## Model Performance

The documentation generation model achieved the following results on the training subset:

| Metric | Score |
| :--- | :--- |
| **BLEU** | 36.65 |
| **ROUGE-L** | 62.17 |
| **BERTScore** | 0.93 |

*Note: These scores represent a sanity check on the training data.*
