import ast
import os
import glob
from typing import List, Dict, Optional
import javalang

class CodeExtractor:
    def __init__(self):
        pass

    def extract_from_directory(self, root_path: str) -> List[Dict[str, str]]:
        results = []
        # Python files
        for file_path in glob.glob(os.path.join(root_path, '**', '*.py'), recursive=True):
            if 'venv' in file_path or '__pycache__' in file_path:
                continue
            results.extend(self.extract_python(file_path))
        
        # Java files
        for file_path in glob.glob(os.path.join(root_path, '**', '*.java'), recursive=True):
            results.extend(self.extract_java(file_path))
            
        return results

    def extract_python(self, file_path: str) -> List[Dict[str, str]]:
        pairs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        # Get function source code
                        # This is a simplification; getting exact source from AST node requires ast.get_source_segment (Python 3.8+)
                        # or reading lines based on lineno.
                        # For now, we'll store the signature and docstring.
                        pairs.append({
                            'language': 'python',
                            'file_path': file_path,
                            'name': node.name,
                            'docstring': docstring,
                            'lineno': node.lineno
                        })
        except Exception as e:
            print(f"Error parsing Python file {file_path}: {e}")
            
        return pairs

    def extract_java(self, file_path: str) -> List[Dict[str, str]]:
        pairs = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = javalang.parse.parse(source)
            
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                if node.documentation:
                    # javalang documentation includes the comment delimiters usually
                    docstring = node.documentation
                    pairs.append({
                        'language': 'java',
                        'file_path': file_path,
                        'name': node.name,
                        'docstring': docstring,
                        'lineno': node.position.line if node.position else 0
                    })
        except Exception as e:
             print(f"Error parsing Java file {file_path}: {e}")
             
        return pairs

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Extract code-docstring pairs")
    parser.add_argument("path", help="Root directory to scan")
    parser.add_argument("--output", help="Output JSON file", default="extracted_data.json")
    
    args = parser.parse_args()
    
    extractor = CodeExtractor()
    data = extractor.extract_from_directory(args.path)
    
    print(f"Extracted {len(data)} pairs.")
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {args.output}")
