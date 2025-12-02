import json
import os
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
import radon.raw as radon_raw
from radon.visitors import Function, Class
import lizard
from typing import List, Dict, Any

class MetricsAnalyzer:
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        _, ext = os.path.splitext(file_path)
        if ext == '.py':
            return self._analyze_python(file_path)
        elif ext == '.java':
            return self._analyze_java(file_path)
        else:
            return {}

    def _analyze_python(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        # File-level metrics
        try:
            mi = radon_metrics.mi_visit(code, multi=False)
        except:
            mi = 0
            
        try:
            raw = radon_raw.analyze(code)
            loc = raw.loc
            sloc = raw.sloc
        except:
            loc = 0
            sloc = 0

        # Function-level metrics using Radon
        functions = []
        try:
            blocks = radon_cc.cc_visit(code)
            for block in blocks:
                if isinstance(block, Function):
                    # Calculate Halstead for function body
                    # We need to extract the source code for the function to do precise Halstead
                    # Radon blocks have lineno and endline (if available, or we guess)
                    # For simplicity here, we'll rely on what we have. 
                    # Actually radon block object doesn't have source. 
                    # We will use the complexity provided.
                    
                    func_metrics = {
                        "name": block.name,
                        "lineno": block.lineno,
                        "cyclomatic_complexity": block.complexity,
                        "type": "method" if block.is_method else "function"
                    }
                    functions.append(func_metrics)
        except Exception as e:
            print(f"Error in Radon analysis for {file_path}: {e}")

        # Cross-check/Augment with Lizard (good for Cognitive Complexity proxy and consistency)
        try:
            liz_analysis = lizard.analyze_file(file_path)
            # Lizard might find functions Radon missed or vice versa, but usually they align.
            # We'll add Lizard's NLOC and CCN if we can match them.
            for func in liz_analysis.function_list:
                # Try to match with existing function record
                match = next((f for f in functions if f['name'] == func.name and abs(f['lineno'] - func.start_line) < 5), None)
                if match:
                    match['nloc'] = func.nloc
                    match['token_count'] = func.token_count
                    match['cyclomatic_complexity_lizard'] = func.cyclomatic_complexity
                else:
                    # Add if not found (maybe Radon missed it)
                    functions.append({
                        "name": func.name,
                        "lineno": func.start_line,
                        "cyclomatic_complexity": func.cyclomatic_complexity,
                        "nloc": func.nloc,
                        "token_count": func.token_count,
                        "type": "function"
                    })
        except Exception as e:
            print(f"Error in Lizard analysis for {file_path}: {e}")

        return {
            "file_path": file_path,
            "language": "python",
            "loc": loc,
            "sloc": sloc,
            "maintainability_index": mi,
            "functions": functions
        }

    def _analyze_java(self, file_path: str) -> Dict[str, Any]:
        # Java analysis relies primarily on Lizard
        functions = []
        loc = 0
        nloc = 0
        
        try:
            liz_analysis = lizard.analyze_file(file_path)
            loc = len(open(file_path, encoding='utf-8').readlines())
            nloc = liz_analysis.nloc
            
            for func in liz_analysis.function_list:
                functions.append({
                    "name": func.name,
                    "lineno": func.start_line,
                    "cyclomatic_complexity": func.cyclomatic_complexity,
                    "nloc": func.nloc,
                    "token_count": func.token_count,
                    "params": len(func.parameters)
                })
        except Exception as e:
            print(f"Error in Lizard analysis for {file_path}: {e}")

        return {
            "file_path": file_path,
            "language": "java",
            "loc": loc,
            "nloc": nloc,
            "functions": functions
        }

if __name__ == "__main__":
    import argparse
    import glob
    
    parser = argparse.ArgumentParser(description="Extract Code Metrics")
    parser.add_argument("path", help="File or directory to analyze")
    parser.add_argument("--output", help="Output JSON file", default="metrics.json")
    
    args = parser.parse_args()
    
    analyzer = MetricsAnalyzer()
    results = []
    
    if os.path.isfile(args.path):
        results.append(analyzer.analyze_file(args.path))
    else:
        for root, _, files in os.walk(args.path):
            for file in files:
                if file.endswith(('.py', '.java')):
                    full_path = os.path.join(root, file)
                    if 'venv' in full_path: continue
                    results.append(analyzer.analyze_file(full_path))
    
    print(f"Analyzed {len(results)} files.")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {args.output}")
