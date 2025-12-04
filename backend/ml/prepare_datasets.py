import argparse
import os
import json
from datasets import load_dataset
from tqdm import tqdm

def prepare_dataset(output_dir, languages=['python', 'java'], split='train', limit=None):
    print(f"Processing google/code_x_glue_ct_code_to_text for {languages}...")
    
    data = []
    
    for lang in languages:
        print(f"Loading {lang}...")
        try:
            # Using 'google/code_x_glue_ct_code_to_text' as requested
            # Disable streaming to avoid 429 Too Many Requests (downloads full dataset)
            ds = load_dataset("google/code_x_glue_ct_code_to_text", lang, split=split, trust_remote_code=True)
        except Exception as e:
            print(f"Error loading {lang}: {e}")
            continue

        count = 0
        for item in tqdm(ds):
            code = item.get('code') or item.get('func_code_string') or ''
            doc = item.get('docstring') or item.get('func_documentation_string') or ''
            
            if code and doc:
                entry = {
                    "code": code,
                    "docstring": doc,
                    "language": lang,
                    "source": "google/code_x_glue_ct_code_to_text"
                }
                data.append(entry)
                count += 1
                
            if limit and count >= limit:
                break
                
    output_file = os.path.join(output_dir, f"training_data_{split}.jsonl")
    print(f"Saving {len(data)} records to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="backend/processed_data", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit samples per language (for testing)")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    prepare_dataset(args.output_dir, limit=args.limit)
