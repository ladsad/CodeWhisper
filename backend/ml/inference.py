"""
Inference module for the fine-tuned CodeT5 model.
Loads the LoRA adapter and generates documentation.
"""
import os
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel

# Global model and tokenizer (loaded once)
_model = None
_tokenizer = None
_device = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "codet5-finetuned")
BASE_MODEL = "Salesforce/codet5-small"

def load_model():
    """Load the fine-tuned model and tokenizer."""
    global _model, _tokenizer, _device
    
    if _model is not None:
        return _model, _tokenizer
    
    print(f"Loading model from {MODEL_PATH}...")
    
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {_device}")
    
    # Load base model
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        BASE_MODEL,
        trust_remote_code=True,
        local_files_only=False  # Allow downloading base model if needed
    )
    
    # Load LoRA adapter
    _model = PeftModel.from_pretrained(base_model, MODEL_PATH)
    _model = _model.to(_device)
    _model.eval()
    
    # Load tokenizer from local model directory (it has tokenizer files)
    # Fall back to base model if local tokenizer not found
    try:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
        print("Loaded tokenizer from local model directory")
    except:
        _tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        print("Loaded tokenizer from base model")
    
    print("Model loaded successfully!")
    return _model, _tokenizer

def generate_docstring(code: str, language: str = "python", max_length: int = 128) -> str:
    """
    Generate a docstring for the given code.
    
    Args:
        code: The source code to document
        language: Programming language (python, java)
        max_length: Maximum length of generated docstring
        
    Returns:
        Generated docstring
    """
    model, tokenizer = load_model()
    
    # Format input like training data
    input_text = f"Generate a documentation string for this function:\n{language}: {code}"
    
    # Tokenize
    inputs = tokenizer(
        input_text,
        max_length=512,
        truncation=True,
        padding="max_length",
        return_tensors="pt"
    ).to(_device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=2
        )
    
    # Decode
    docstring = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return docstring

def is_model_available() -> bool:
    """Check if the trained model is available."""
    return os.path.exists(MODEL_PATH) and os.path.isdir(MODEL_PATH)
