import os
from typing import List, Generator

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx'}

def scan_directory(root_path: str) -> Generator[str, None, None]:
    """
    Recursively scans the directory and yields paths to supported files.
    """
    for root, dirs, files in os.walk(root_path):
        # Skip hidden directories and venv
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv' and d != 'node_modules']
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in SUPPORTED_EXTENSIONS:
                yield os.path.join(root, file)
