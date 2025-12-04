import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
import argparse

def train(
    train_file: str,
    output_dir: str,
    model_name: str = "Salesforce/codet5-small",
    batch_size: int = 4,
    epochs: int = 3,
    learning_rate: float = 2e-5
):
    print(f"Loading model: {model_name}")
    
    use_cuda = torch.cuda.is_available()
    device = "cuda" if use_cuda else "cpu"
    print(f"Using device: {device}")

    # QLoRA Configuration (Only if CUDA is available)
    if use_cuda:
        print("CUDA detected. Using QLoRA with 4-bit quantization.")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )
        
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        model.gradient_checkpointing_enable()
        model = prepare_model_for_kbit_training(model)
    else:
        print("CUDA NOT detected. Using standard CPU training (No Quantization).")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            trust_remote_code=True
        ).to(device)

    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # LoRA Configuration
    # We can still use LoRA on CPU to reduce trainable parameters, though it won't be as fast.
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        target_modules=["q", "v"] # Target attention layers
    )

    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # Load Dataset
    data_files = {"train": train_file}
    dataset = load_dataset("json", data_files=data_files)

    def preprocess_function(examples):
        inputs = [
            f"Generate a documentation string for this function:\n{lang}: {code}" 
            for lang, code in zip(examples["language"], examples["code"])
        ]
        targets = examples["docstring"]
        
        model_inputs = tokenizer(inputs, max_length=512, truncation=True, padding="max_length")
        labels = tokenizer(targets, max_length=128, truncation=True, padding="max_length")
        
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    tokenized_dataset = dataset.map(preprocess_function, batched=True)

    # Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=4, 
        learning_rate=learning_rate,
        num_train_epochs=epochs,
        logging_steps=10,
        save_strategy="epoch",
        eval_strategy="no", 
        fp16=use_cuda, # Only use FP16 if CUDA is available
        use_cpu=not use_cuda, # Explicitly tell Trainer to use CPU if needed
        optim="paged_adamw_8bit" if use_cuda else "adamw_torch", # 8-bit optim needs CUDA
        ddp_find_unused_parameters=False if (use_cuda and torch.cuda.device_count() > 1) else None,
        report_to="none"
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    print("Starting training...")
    trainer.train()
    
    print(f"Saving model to {output_dir}")
    trainer.save_model(output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune CodeT5")
    parser.add_argument("--train_file", type=str, required=True, help="Path to training data (JSON)")
    parser.add_argument("--output_dir", type=str, default="./results", help="Output directory")
    parser.add_argument("--model_name", type=str, default="Salesforce/codet5-small", help="Base model name")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per device")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()
    
    train(
        train_file=args.train_file,
        output_dir=args.output_dir,
        model_name=args.model_name,
        batch_size=args.batch_size,
        epochs=args.epochs,
        learning_rate=args.learning_rate
    )
