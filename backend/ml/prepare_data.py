import json
import argparse
from datasets import load_dataset
from tqdm import tqdm

def prepare_data(output_file: str, samples_per_lang: int = 1000):
    print(f"Loading CodeXGLUE Code-to-Text dataset...")
    
    data = []
    
    # Load Python
    print("Fetching Python samples...")
    try:
        # google/code_x_glue_ct_code_to_text
        ds_py = load_dataset("google/code_x_glue_ct_code_to_text", "python", split="train", streaming=True)
        count = 0
        for item in tqdm(ds_py):
            if count >= samples_per_lang:
                break
            
            # CodeXGLUE usually has 'code' and 'docstring'
            code = item.get("code")
            doc = item.get("docstring")
            
            if code and doc:
                data.append({
                    "language": "python",
                    "code": code,
                    "docstring": doc
                })
                count += 1
    except Exception as e:
        print(f"Error loading Python data: {e}")
        
    # Load Java
    print("Fetching Java samples...")
    try:
        ds_java = load_dataset("google/code_x_glue_ct_code_to_text", "java", split="train", streaming=True)
        count = 0
        for item in tqdm(ds_java):
            if count >= samples_per_lang:
                break
            
            code = item.get("code")
            doc = item.get("docstring")
            
            if code and doc:
                data.append({
                    "language": "java",
                    "code": code,
                    "docstring": doc
                })
                count += 1
    except Exception as e:
        print(f"Error loading Java data: {e}")
    
    print(f"Saving {len(data)} samples to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Training Data from CodeXGLUE")
    parser.add_argument("--output", type=str, default="training_data.json", help="Output JSON file")
    parser.add_argument("--samples", type=int, default=1000, help="Samples per language")
    
    args = parser.parse_args()
    
    prepare_data(args.output, args.samples)
