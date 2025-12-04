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
        # Load streaming to avoid massive RAM usage
        try:
            ds = load_dataset("code_search_net", split=split, streaming=True, trust_remote_code=True)
            # The dataset might be subsetted by language in the config, checking structure
            # Actually code_search_net has subsets like 'python', 'java'
            ds = load_dataset("code_search_net", lang, split=split, streaming=True, trust_remote_code=True)
        except Exception as e:
            print(f"Error loading {lang}: {e}")
            continue

        count = 0
        for item in tqdm(ds):
            # CodeSearchNet structure: 'func_code_string', 'func_documentation_string'
            code = item.get('func_code_string', '')
            doc = item.get('func_documentation_string', '')
            
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
