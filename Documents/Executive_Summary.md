# CodeWhisper: Executive Summary

## Project Overview
CodeWhisper is an intelligent development tool that automatically generates code documentation and quantifies code quality. It uses **CodeT5+** fine-tuned with **QLoRA** to generate docstrings, while providing complexity metrics, anomaly detection, and maintainability predictions through a comprehensive analytics pipeline.

## Key Features
- **Auto-Documentation**: Generates docstrings using a fine-tuned CodeT5 model (BLEU: 36.65, ROUGE-L: 62.17)
- **Code Analysis**: Cyclomatic complexity, maintainability index, and anomaly detection (Isolation Forest)
- **VS Code Extension**: Right-click context menu for real-time documentation generation
- **Streamlit Dashboard**: Visualizes project health, complexity heatmaps, and flagged files

## Technical Stack
| Component | Technology |
|-----------|------------|
| Backend | Python, FastAPI |
| ML/AI | CodeT5+, QLoRA, HuggingFace Transformers |
| Analysis | Radon, Lizard, scikit-learn, XGBoost |
| Dashboard | Streamlit, Plotly |
| IDE Integration | VS Code Extension (TypeScript) |

## Target Audience
Software engineers, data scientists, and development teams seeking to improve documentation coverage, track technical debt, and maintain code health standards.

## Unique Value Proposition
Unlike code completion tools (Copilot, Tabnine), CodeWhisper focuses on **long-term codebase health**. It combines deep analytics with automated documentation, offering a transparent dashboard for visualizing quality trends and identifying refactoring candidates.
