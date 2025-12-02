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
