import ast
import os
import glob
import random
import json
from typing import List, Dict, Tuple, Optional
import javalang
from sklearn.model_selection import train_test_split

class DataProcessor:
    def __init__(self, root_path: str, output_dir: str):
        self.root_path = root_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def process(self):
        """
        Main processing pipeline:
        1. Extract code-docstring pairs
        2. Clean data
        3. Split into train/val/test
        4. Augment training data
        5. Save datasets
        """
        print("Starting data processing...")
        
        # 1. Extraction
        all_files = self._get_files()
        print(f"Found {len(all_files)} files.")
        
        data_by_file = {}
        for file_path in all_files:
            # Determine language from content or extension (now we rely on _extract methods to check)
            # We try both or check header first. 
            # Optimization: Check header once
            lang, _, _ = self._parse_scraped_file(file_path)
            
            pairs = []
            if lang == 'python':
                pairs = self._extract_python(file_path)
            elif lang == 'java':
                pairs = self._extract_java(file_path)
                
            if pairs:
                data_by_file[file_path] = pairs

        print(f"Extracted data from {len(data_by_file)} files.")

        # 2. Split (by file to avoid leakage)
        files = list(data_by_file.keys())
        
        if len(files) < 3:
            print("Warning: Dataset too small for split. Using all for training.")
            train_files = files
            val_files = []
            test_files = []
        else:
            train_files, test_files = train_test_split(files, test_size=0.2, random_state=42)
            # Ensure we have enough for val split
            if len(test_files) > 1:
                val_files, test_files = train_test_split(test_files, test_size=0.5, random_state=42)
            else:
                val_files = test_files
                test_files = []

        train_data = self._flatten_data(data_by_file, train_files)
        val_data = self._flatten_data(data_by_file, val_files)
        test_data = self._flatten_data(data_by_file, test_files)

        print(f"Split sizes - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")

        # 3. Augmentation (Train only)
        print("Augmenting training data...")
        augmented_train_data = self._augment_data(train_data)
        print(f"Augmented Train size: {len(augmented_train_data)}")

        # 4. Save
        self._save_json(augmented_train_data, "train.json")
        self._save_json(val_data, "val.json")
        self._save_json(test_data, "test.json")
        print("Data processing complete.")

    def _get_files(self) -> List[str]:
        files = []
        # Look for the scraped .txt files
        files.extend(glob.glob(os.path.join(self.root_path, '**', '*.txt'), recursive=True))
        return [f for f in files if 'venv' not in f and '__pycache__' not in f]

    def _parse_scraped_file(self, file_path: str) -> Tuple[str, str, str]:
        """
        Parses a scraped .txt file to extract metadata and raw code.
        Returns: (language, code, repo_info)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split header and code
            # Header format:
            # Repo: ...
            # Path: ...
            # Language: ...
            # <empty line>
            # <code content>
            
            parts = content.split('\n\n', 1)
            if len(parts) < 2:
                return "", "", ""
            
            header = parts[0]
            code = parts[1]
            
            language = ""
            for line in header.splitlines():
                if line.startswith("Language: "):
                    language = line.replace("Language: ", "").strip().lower()
            
            return language, code, header
        except Exception:
            return "", "", ""

    def _extract_python(self, file_path: str) -> List[Dict]:
        pairs = []
        try:
            language, source, header = self._parse_scraped_file(file_path)
            if language != 'python' or not source:
                return []
            
            tree = ast.parse(source)
            lines = source.splitlines()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        start = node.lineno - 1
                        end = node.end_lineno
                        code_lines = lines[start:end]
                        code = "\n".join(code_lines)
                        
                        pairs.append({
                            'language': 'python',
                            'file_path': file_path,
                            'name': node.name,
                            'code': code,
                            'docstring': docstring,
                            'metadata': header
                        })
        except Exception as e:
            pass
        return pairs

    def _extract_java(self, file_path: str) -> List[Dict]:
        pairs = []
        try:
            language, source, header = self._parse_scraped_file(file_path)
            if language != 'java' or not source:
                return []
            
            tree = javalang.parse.parse(source)
            
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                if node.documentation:
                    pairs.append({
                        'language': 'java',
                        'file_path': file_path,
                        'name': node.name,
                        'code': f"// Code for {node.name}", 
                        'docstring': node.documentation,
                        'metadata': header
                    })
        except Exception:
            pass
        return pairs

    def _flatten_data(self, data_map: Dict, file_list: List[str]) -> List[Dict]:
        flat = []
        for f in file_list:
            flat.extend(data_map[f])
        return flat

    def _augment_data(self, data: List[Dict]) -> List[Dict]:
        augmented = []
        augmented.extend(data) # Keep originals
        
        for item in data:
            if item['language'] == 'python':
                # Variable Renaming Augmentation
                try:
                    aug_code = self._augment_python_rename(item['code'])
                    if aug_code != item['code']:
                        new_item = item.copy()
                        new_item['code'] = aug_code
                        new_item['augmented'] = True
                        augmented.append(new_item)
                except:
                    pass
        return augmented

    def _augment_python_rename(self, source_code: str) -> str:
        """
        Renames variables in Python code using AST.
        """
        try:
            tree = ast.parse(source_code)
            transformer = VariableRenamer()
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)
            return ast.unparse(new_tree) # Requires Python 3.9+
        except:
            return source_code

    def _save_json(self, data: List[Dict], filename: str):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

class VariableRenamer(ast.NodeTransformer):
    def __init__(self):
        self.mapping = {}
        self.count = 0

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Param)):
            if node.id not in self.mapping and node.id != 'self':
                self.mapping[node.id] = f"var_{self.count}"
                self.count += 1
        
        if node.id in self.mapping:
            return ast.copy_location(ast.Name(id=self.mapping[node.id], ctx=node.ctx), node)
        return node

    def visit_arg(self, node):
        if node.arg not in self.mapping and node.arg != 'self':
             self.mapping[node.arg] = f"arg_{self.count}"
             self.count += 1
        
        if node.arg in self.mapping:
            new_node = ast.copy_location(ast.arg(arg=self.mapping[node.arg], annotation=node.annotation), node)
            return new_node
        return node

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Root directory to scan")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()
    
    processor = DataProcessor(args.root, args.output)
    processor.process()
