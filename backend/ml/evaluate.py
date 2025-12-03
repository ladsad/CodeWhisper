import argparse
import json
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel, PeftConfig
from datasets import load_metric
import evaluate
from tqdm import tqdm
import os

def evaluate_model(
    test_file: str,
    model_path: str,
    batch_size: int = 4,
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
):
    print(f"Loading model from {model_path} on {device}...")
    
    # Check if it's a PEFT model
    is_peft = os.path.exists(os.path.join(model_path, "adapter_config.json"))
    
    if is_peft:
        print("Detected PEFT adapter. Loading base model + adapter...")
        config = PeftConfig.from_pretrained(model_path)
        base_model_path = config.base_model_name_or_path
        
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_path)
        model = PeftModel.from_pretrained(base_model, model_path).to(device)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)
    
    # Load metrics
    bleu = evaluate.load("bleu")
    rouge = evaluate.load("rouge")
    bertscore = evaluate.load("bertscore")
    
    # Load data
    with open(test_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Evaluating on {len(data)} examples...")
    
    generated_docs = []
    references = []
    
    # Generate
    for i in tqdm(range(0, len(data), batch_size)):
        batch = data[i:i+batch_size]
        inputs = [f"Generate a documentation string for this function:\n{item['language']}: {item['code']}" for item in batch]
        refs = [item['docstring'] for item in batch]
        
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding=True, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                **model_inputs, 
                max_length=128, 
                num_beams=4, 
                early_stopping=True
            )
            
        decoded_preds = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        
        generated_docs.extend(decoded_preds)
        references.extend(refs)

    # Compute Metrics
    print("Computing metrics...")
    
    bleu_score = bleu.compute(predictions=generated_docs, references=references)
    rouge_score = rouge.compute(predictions=generated_docs, references=references)
    bert_score = bertscore.compute(predictions=generated_docs, references=references, lang="en")
    
    print("\nResults:")
    print(f"BLEU: {bleu_score['bleu']:.4f}")
    print(f"ROUGE-1: {rouge_score['rouge1']:.4f}")
    print(f"ROUGE-2: {rouge_score['rouge2']:.4f}")
    print(f"ROUGE-L: {rouge_score['rougeL']:.4f}")
    print(f"BERTScore (F1 Mean): {sum(bert_score['f1']) / len(bert_score['f1']):.4f}")

    # Save detailed results
    results = []
    for i in range(len(generated_docs)):
        results.append({
            "code": data[i]['code'],
            "reference": references[i],
            "generated": generated_docs[i]
        })
        
    with open("evaluation_results.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print("Detailed results saved to evaluation_results.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Docstring Generation")
    parser.add_argument("--test_file", type=str, required=True, help="Path to test data (JSON)")
    parser.add_argument("--model_path", type=str, default="Salesforce/codet5-small", help="Path to model or checkpoint")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    
    args = parser.parse_args()
    
    evaluate_model(args.test_file, args.model_path, args.batch_size)
