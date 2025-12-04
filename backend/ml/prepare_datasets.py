import argparse
import os
import json
from datasets import load_dataset
from tqdm import tqdm

def prepare_codesearchnet(output_dir, languages=['python', 'java'], split='train', limit=None):
    print(f"Processing CodeSearchNet for {languages}...")
    
    data = []
    
    for lang in languages:
        print(f"Loading {lang}...")
        try:
            # Using 'sentence-transformers/codesearchnet' which is a Parquet mirror
            # Note: This dataset might not be split by language in the config, checking...
            # If it's monolithic, we might need to filter.
            # Let's try loading the specific language subset if possible, or the whole thing and filter.
            # 'sentence-transformers/codesearchnet' usually has 'lang' column.
            ds = load_dataset("sentence-transformers/codesearchnet", split=split, streaming=True)
        except Exception as e:
            print(f"Error loading {lang}: {e}")
            continue

        count = 0
        for item in tqdm(ds):
            # Check language filter
            if item.get('lang') != lang and item.get('language') != lang:
                continue

            # Check for various common field names
            code = item.get('func_code_string') or item.get('code') or ''
            doc = item.get('func_documentation_string') or item.get('docstring') or ''
            
            if code and doc:
                entry = {
                    "code": code,
                    "docstring": doc,
                    "language": lang,
                    "source": "codesearchnet"
                }
                data.append(entry)
                count += 1
                
            if limit and count >= limit:
                break
                
    output_file = os.path.join(output_dir, f"codesearchnet_{split}.jsonl")
    print(f"Saving {len(data)} records to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')

def prepare_codexglue(output_dir, split='train', limit=None):
    # CodeXGLUE is a collection. We focus on Code-to-Text (doc generation)
    # dataset: code_x_glue_ct_code_to_text
    print(f"Processing CodeXGLUE (Code-to-Text)...")
    
    languages = ['python', 'java']
    data = []
    
    for lang in languages:
        print(f"Loading {lang}...")
        try:
            ds = load_dataset("code_x_glue_ct_code_to_text", lang, split=split, streaming=True, trust_remote_code=True)
        except Exception as e:
            print(f"Error loading {lang}: {e}")
            continue
            
        count = 0
        for item in tqdm(ds):
            # CodeXGLUE structure: 'code', 'docstring'
            code = item.get('code', '')
            doc = item.get('docstring', '')
            
            if code and doc:
                entry = {
                    "code": code,
                    "docstring": doc,
                    "language": lang,
                    "source": "codexglue"
                }
                data.append(entry)
                count += 1
                
            if limit and count >= limit:
                break
    
    output_file = os.path.join(output_dir, f"codexglue_{split}.jsonl")
    print(f"Saving {len(data)} records to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="backend/processed_data", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit samples per language (for testing)")
    parser.add_argument("--dataset", choices=['codesearchnet', 'codexglue', 'all'], default='all')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.dataset in ['codesearchnet', 'all']:
        prepare_codesearchnet(args.output_dir, limit=args.limit)
        
    if args.dataset in ['codexglue', 'all']:
        prepare_codexglue(args.output_dir, limit=args.limit)
