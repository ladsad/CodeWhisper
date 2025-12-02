**CodeWhisper \- Code Documentation Auto-Generator with Quality Metrics**

**Project Overview**

This project aims to build a **state-of-the-art tool that automatically generates documentation for software code using advanced transformer models, coupled with analytical quality metrics to assess code health and maintainability**. Designed for software engineers, data scientists, and teams, the tool provides automatic function/class documentation, quantifies the quality of generated docs, and visualizes repository health and technical debt through an interactive dashboard.

Unlike existing tools like GitHub Copilot or Tabnine, this solution uniquely blends deep analytics with AI-based summarization. Key differentiators include multi-language support (Python, Java, Javascript), custom complexity metric extraction (Cyclomatic, Halstead, Maintainability Index), code health anomaly detection, and actionable suggestions for refactoring candidates.

## 2. Technical Architecture

### System Design

```ascii
                ┌───────────────────────────────┐
                │      GitHub Repo Scraper      │
                └─────────────┬─────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Data Pipeline    │
                    └─────────┬─────────┘
        ┌─────────────┬─────┬──────────┴─────────────┐
        │             │     │                        │
 ┌──────▼──────┐ ┌────▼────┐ │       ┌─────────────┐  │
 │ Preprocess  │ │ AST     │ │       │ Complexity  │  │
 │ Code/Docs   │ │ Parsing │ │       │ Metrics     │  │
 └──────▲──────┘ └──▲──────┘ │       └────▲────────┘  │
        │             │      │            │           │
        │   ┌─────────┴──────┴────────────┴──────┐   │
        │   │ Transformer Model (CodeT5, etc)    │   │
        │   └────────────────┬───────────────────┘   │
        │                    │                       │
        │        ┌───────────▼────────────┐          │
        └───────►│ Documentation & Metrics│◄─────────┘
                 └───────────┬────────────┘
                             │
                   ┌─────────▼──────────┐
                   │ Analytics Storage  │
                   └─────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │   Dashboard (UI)  │
                    └───────────────────┘
```

### Component Breakdown

-   **Ingestion & Scraping:** Clone or pull from target repositories (via GitHub API or local files)
-   **Preprocessing:** Clean, deduplicate, and batch code
-   **AST Parsing:** Use language-specific parsers (Python: ast, Java: JavaParser)
-   **Transformer Inference:** Model to autogenerate and score documentation
-   **Complexity Analyzer:** Compute code metrics (see Section 4)
-   **Data Store:** Database (e.g., SQLite/Postgres) to persist results
-   **Analytics Dashboard:** Streamlit/Dash/React frontend for interactive insights

### Technology Stack & Justification

| Component         | Technology                                                                    | Justification                                     |
| ----------------- | ----------------------------------------------------------------------------- | ------------------------------------------------- |
| Scraper           | PyGithub, Git CLI                                                             | Robust API, supports private/public repos         |
| AST Parser        | ast/javalang                                                                  | Strong static analysis, language-specific parsing |
| Transformer Model | HuggingFace (PyTorch/TensorFlow)                                              | Pretrained models, easy finetuning                |
| Metrics           | Radon (Python), lizard (multi), Cognitive Complexity (pylint), custom scripts | Comprehensive metrics                             |
| Data Store        | SQLite/MySQL/Postgres                                                         | Easy local development/scalability                |
| Dashboard         | Streamlit/Dash/React+D3                                                       | Fast interactive prototyping, real-time capable   |
| Backend           | FastAPI/Flask                                                                 | Async inference, REST API for dashboard/VSCode    |

### Database Schema (Sample)
**Table: code_files**

| Column | Type | Description |
| :--- | :--- | :--- |
| file_id | INTEGER PK | File identifier |
| repo_name | TEXT | Repository name |
| file_path | TEXT | Path within repo |
| language | TEXT | Language (Python/Java, etc) |
| code_text | TEXT | Raw code |
| docstring_text | TEXT | Existing docstring (if any) |
| generated_doc | TEXT | Model-generated docstring |
| complexity_json | JSON | Dict for metrics (McCabe, Halstead, MI, etc) |
| timestamp | TIMESTAMP | Extraction time |

## 3. Transformer Component - Detailed Implementation

### Model Comparison: Code Documentation Generation

| Model | Architecture | Pros | Cons | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **CodeBERT** | Encoder-only (BERT-based) | Lightweight, fast embeddings, good for search | **Not designed for generation** (seq2seq), requires ad-hoc decoders | Code search, classification, clone detection |
| **CodeT5 / CodeT5+** | Encoder-Decoder (T5-based) | **SOTA for summarization**, native multi-lang support, efficient fine-tuning | Moderate resource usage compared to LLMs | **Doc generation**, code translation, refinement |
| **CodeLlama** | Decoder-only (LLM) | Powerful generation, large context window, zero-shot capabilities | **Heavy compute**, slower inference, requires quantization for consumer GPUs | Complex generation, chat, reasoning |

### Recommendation: CodeT5+

**Why:**
-   **Strong documentation generation results:** specifically pre-trained for code-to-text tasks.
-   **Multi-language support:** Native support for Python, Java, JS, etc.
-   **HuggingFace support:** Excellent integration with `transformers` library.
-   **Lightweight:** 220M/770M parameter versions are feasible for local dev/small-scale fine-tuning.

**CodeLlama (Meta)** is strong for large-scale tasks but requires significantly heavier compute resources.
**CodeBERT** is better suited for embedding and classification tasks, not text generation.

### Implementation Details
*   **Training Data:** Combines public datasets (CodeSearchNet, CodeXGLUE) with personal GitHub code, paired via AST parsing.
*   **Fine-tuning:** Uses efficient LoRA/QLoRA methods on limited GPUs; input formatting includes language tags and function signatures.
*   **Evaluation:** BLEU, ROUGE, BERTScore, CodeBLEU, plus human rubric ratings.

**Data Science & Analytics Module**

*   **Calculates**: Cyclomatic complexity (McCabe), Halstead metrics, lines of code (LOC), maintainability index, cognitive complexity.

*   **Analysis:** Uses statistical tests and ML models (RandomForest/XGBoost) to correlate documentation quality with code complexity and predict maintainability.

*   **Anomaly Detection:** Isolation Forest or threshold models flag poorly documented/high-complexity code units for action.

**Dashboard Design**

*   **Visualizations:** Repository health scores, complexity heatmaps, documentation coverage bars, commit trend analyses.

*   **Tech Stack:** Streamlit recommended for fast prototypes; Dash or React+D3 for advanced setups.

*   **Modes:** Batch analyses by default, with options for real-time refresh.

**Extensions & Future Work**

Planned future features include: multi-language expansion, direct integration with code review tools (GitHub Actions), automated refactoring suggestions, and feedback-driven improvement cycles.

**Portfolio Impact**

This project demonstrates full-stack data science, NLP for code understanding, and interpretable analytics—making it an ideal centerpiece for professional data science or software engineering applications.