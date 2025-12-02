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
    learning_rate: float = 2e-4
):
    print(f"Loading model: {model_name}")
    
    # QLoRA Configuration
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )

    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Load Model with Quantization
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    # LoRA Configuration
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
    # Assuming JSON format: [{"language": "python", "code": "def foo...", "docstring": "..."}]
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
        gradient_accumulation_steps=4, # Simulate larger batch size
        learning_rate=learning_rate,
        num_train_epochs=epochs,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="no", # Set to 'steps' or 'epoch' if validation set provided
        fp16=True, # Use FP16 if GPU supports it
        optim="paged_adamw_8bit", # Use 8-bit optimizer to save memory
        ddp_find_unused_parameters=False if torch.cuda.device_count() > 1 else None,
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
    parser = argparse.ArgumentParser(description="Fine-tune CodeT5 with QLoRA")
    parser.add_argument("--train_file", type=str, required=True, help="Path to training data (JSON)")
    parser.add_argument("--output_dir", type=str, default="./results", help="Output directory")
    parser.add_argument("--model_name", type=str, default="Salesforce/codet5-small", help="Base model name")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size per device")
    
    args = parser.parse_args()
    
    train(
        train_file=args.train_file,
        output_dir=args.output_dir,
        model_name=args.model_name,
        batch_size=args.batch_size
    )
