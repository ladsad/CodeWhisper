import json
import os
import radon.complexity as radon_cc
import radon.metrics as radon_metrics
import radon.raw as radon_raw
from radon.visitors import Function, Class
import lizard
from typing import List, Dict, Any

class MetricsAnalyzer:
    def analyze_code(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Analyze code string directly without file I/O"""
        if language.lower() in ['python', 'py']:
            return self._analyze_python_code(code)
        elif language.lower() in ['java']:
            # Java analysis in this class currently relies on file path for Lizard
            # We'll need a workaround or just skip full metrics for string-only Java for now
            # or write to temp file if needed. For now, let's support Python fully.
            return {}
        else:
            return {}

    def _analyze_python_code(self, code: str) -> Dict[str, Any]:
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
            # AST parse for docstrings
            import ast
            tree = ast.parse(code)
            docstrings = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstrings[node.name] = bool(ast.get_docstring(node))

            blocks = radon_cc.cc_visit(code)
            for block in blocks:
                if isinstance(block, Function):
                    func_metrics = {
                        "name": block.name,
                        "lineno": block.lineno,
                        "cyclomatic_complexity": block.complexity,
                        "type": "method" if block.is_method else "function",
                        "has_docstring": docstrings.get(block.name, False)
                    }
                    functions.append(func_metrics)
        except Exception as e:
            print(f"Error in Radon/AST analysis: {e}")

        return {
            "language": "python",
            "loc": loc,
            "sloc": sloc,
            "maintainability_index": mi,
            "functions": functions
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        _, ext = os.path.splitext(file_path)
        if ext == '.py':
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            result = self._analyze_python_code(code)
            result['file_path'] = file_path
            
            # Augment with Lizard (requires file path usually, but we can try string if supported or skip)
            # Lizard analyze_file needs path. 
            try:
                liz_analysis = lizard.analyze_file(file_path)
                for func in liz_analysis.function_list:
                    match = next((f for f in result['functions'] if f['name'] == func.name and abs(f['lineno'] - func.start_line) < 5), None)
                    if match:
                        match['nloc'] = func.nloc
                        match['token_count'] = func.token_count
                        match['cyclomatic_complexity_lizard'] = func.cyclomatic_complexity
            except Exception:
                pass
                
            return result
        elif ext == '.java':
            return self._analyze_java(file_path)
        else:
            return {}

    def _analyze_java(self, file_path: str) -> Dict[str, Any]:
        # Java analysis relies primarily on Lizard
        functions = []
        loc = 0
        nloc = 0
        
        try:
            # Javalang for docstrings
            import javalang
            try:
                tree = javalang.parse.parse(open(file_path, encoding='utf-8').read())
                docstrings = {}
                for _, node in tree.filter(javalang.tree.MethodDeclaration):
                    docstrings[node.name] = bool(node.documentation)
            except:
                docstrings = {}

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
                    "params": len(func.parameters),
                    "has_docstring": docstrings.get(func.name, False)
                })
        except Exception as e:
            print(f"Error in Lizard/Javalang analysis for {file_path}: {e}")

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
