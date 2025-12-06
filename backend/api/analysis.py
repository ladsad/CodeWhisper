from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import os
from core.scanner import scan_directory
from core.metrics import calculate_cyclomatic_complexity

router = APIRouter()

class AnalysisRequest(BaseModel):
    project_path: str

class FileMetric(BaseModel):
    file_path: str
    complexity: int

class AnalysisResponse(BaseModel):
    files: List[FileMetric]
    average_complexity: float

@router.post("/analyze", response_model=AnalysisResponse)
def analyze_project(request: AnalysisRequest):
    if not os.path.exists(request.project_path):
        raise HTTPException(status_code=404, detail="Project path not found")

    metrics = []
    total_complexity = 0
    file_count = 0

    for file_path in scan_directory(request.project_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Only analyze Python files for complexity for now
            if file_path.endswith('.py'):
                complexity = calculate_cyclomatic_complexity(content)
                metrics.append(FileMetric(file_path=file_path, complexity=complexity))
                total_complexity += complexity
                file_count += 1
        except Exception as e:
            # Log error or skip
            continue

    avg_complexity = total_complexity / file_count if file_count > 0 else 0
    
    return AnalysisResponse(files=metrics, average_complexity=avg_complexity)
class GenerateRequest(BaseModel):
    code: str
    language: str

@router.post("/generate")
async def generate_doc(request: GenerateRequest):
    """
    Generate docstring for the provided code using the fine-tuned CodeT5 model.
    """
    from ml.inference import generate_docstring, is_model_available
    from core.analyzer import MetricsAnalyzer
    
    # Generate docstring using trained model
    if is_model_available():
        try:
            generated_doc = generate_docstring(request.code, request.language)
        except Exception as e:
            print(f"Model inference error: {e}")
            generated_doc = f"[Model error: {str(e)}]"
    else:
        generated_doc = "[Model not available - place trained model in backend/models/codet5-finetuned/]"
    
    # Also calculate complexity metrics
    analyzer = MetricsAnalyzer()
    metrics = analyzer.analyze_code(request.code, request.language)
    
    complexity_info = ""
    if metrics:
        avg_cc = 0
        max_cc = 0
        funcs = metrics.get('functions', [])
        if funcs:
            avg_cc = sum(f['cyclomatic_complexity'] for f in funcs) / len(funcs)
            max_cc = max(f['cyclomatic_complexity'] for f in funcs)
        
        complexity_info = f"\n\nComplexity Report:\n- Maintainability Index: {metrics.get('maintainability_index', 0):.2f}\n- Avg Cyclomatic Complexity: {avg_cc:.2f}\n- Max Cyclomatic Complexity: {max_cc}"

    # Combine model output with complexity info
    docstring = f'"""\n{generated_doc}{complexity_info}\n"""'
    return {"docstring": docstring}

