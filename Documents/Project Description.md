**CodeWhisper \- Code Documentation Auto-Generator with Quality Metrics**

**Project Overview**

This project aims to build a **state-of-the-art tool that automatically generates documentation for software code using advanced transformer models, coupled with analytical quality metrics to assess code health and maintainability**. Designed for software engineers, data scientists, and teams, the tool provides automatic function/class documentation, quantifies the quality of generated docs, and visualizes repository health and technical debt through an interactive dashboard.

Unlike existing tools like GitHub Copilot or Tabnine, this solution uniquely blends deep analytics with AI-based summarization. Key differentiators include multi-language support (Python, Java, Javascript), custom complexity metric extraction (Cyclomatic, Halstead, Maintainability Index), code health anomaly detection, and actionable suggestions for refactoring candidates.

**Technical Architecture**

The system consists of:

* **GitHub repository scraper** (using PyGithub or git) to extract and process code files, supporting multiple programming languages.

* **Data pipeline and AST parsing** modules that prepare code-function and docstring pairs, leveraging ast (Python) and javalang (Java).

* **Transformer-based docstring generator** utilizing models like CodeT5, fine-tuned via LoRA/QLoRA for efficiency.

* **Metrics engine** calculating code complexity, maintainability index, and documentation coverage.

* **Analytics dashboard** (Streamlit/Dash) showing repository health, complexity distribution, documentation stats, and flagged refactoring suggestions.

All outputs, scores, and documentation are stored in a database (e.g., SQLite), enabling both real-time analysis and historical tracking.

**Transformer Model & Implementation**

* **Model Selection:** CodeT5 is recommended for its superior performance in code documentation generation and multi-language support. CodeBERT and CodeLlama are alternatives for specific sub-tasks.

* **Training Data:** Combines public datasets (CodeSearchNet, CodeXGLUE) with personal GitHub code, paired via AST parsing.

* **Fine-tuning:** Uses efficient LoRA/QLoRA methods on limited GPUs; input formatting includes language tags and function signatures.

* **Evaluation:** BLEU, ROUGE, BERTScore, CodeBLEU, plus human rubric ratings.

**Data Science & Analytics Module**

* **Calculates**: Cyclomatic complexity (McCabe), Halstead metrics, lines of code (LOC), maintainability index, cognitive complexity.

* **Analysis:** Uses statistical tests and ML models (RandomForest/XGBoost) to correlate documentation quality with code complexity and predict maintainability.

* **Anomaly Detection:** Isolation Forest or threshold models flag poorly documented/high-complexity code units for action.

**Dashboard Design**

* **Visualizations:** Repository health scores, complexity heatmaps, documentation coverage bars, commit trend analyses.

* **Tech Stack:** Streamlit recommended for fast prototypes; Dash or React+D3 for advanced setups.

* **Modes:** Batch analyses by default, with options for real-time refresh.

**Extensions & Future Work**

Planned future features include: multi-language expansion, direct integration with code review tools (GitHub Actions), automated refactoring suggestions, and feedback-driven improvement cycles.

**Portfolio Impact**

This project demonstrates full-stack data science, NLP for code understanding, and interpretable analytics—making it an ideal centerpiece for professional data science or software engineering applications.