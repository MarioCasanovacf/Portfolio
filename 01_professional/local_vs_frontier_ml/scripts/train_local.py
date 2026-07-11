#!/usr/bin/env python3
"""Fine-tune a multilingual model locally and measure performance.

Saves training and evaluation metrics to JSON for notebook integration.
"""

import argparse
import json
import os
import time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
FULL_DIR = DATA_DIR / "full"
MODELS_DIR = PROJECT_DIR / "models"
METRICS_PATH = PROJECT_DIR / "research" / "local_model_metrics.json"

LANGUAGES = ["en", "de", "es", "fr", "ja", "zh"]
SEED = 42

# Set random seeds for determinism
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


def map_stars_to_sentiment(stars):
    # 1-2 stars -> 0 (Negative)
    # 3 stars -> 1 (Neutral)
    # 4-5 stars -> 2 (Positive)
    if stars <= 2:
        return 0
    elif stars == 3:
        return 1
    else:
        return 2


def load_local_dataset(split="train", limit_per_lang=5000):
    """Load train/test splits from local CSV files and convert to HuggingFace Dataset."""
    dfs = []
    for lang in LANGUAGES:
        suffix = "_test" if split == "test" else ""
        file_path = FULL_DIR / f"reviews_{lang}{suffix}.csv"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Missing dataset file: {file_path}. Run download_data.py first.")
            
        df = pd.read_csv(file_path)
        # We only need stars and review_body
        df = df[["stars", "review_body"]].rename(columns={"review_body": "text"})
        df["label"] = df["stars"].apply(map_stars_to_sentiment)
        df["language"] = lang
        
        # Sample for speed if requested
        if limit_per_lang and len(df) > limit_per_lang:
            df = df.sample(n=limit_per_lang, random_state=SEED)
            
        dfs.append(df)
        
    combined_df = pd.concat(dfs, ignore_index=True)
    return Dataset.from_pandas(combined_df)


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    preds = np.argmax(predictions, axis=1)
    acc = accuracy_score(labels, preds)
    macro_f1 = f1_score(labels, preds, average="macro")
    return {"accuracy": acc, "macro_f1": macro_f1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-name", default="distilbert-base-multilingual-cased", help="HF model hub identifier")
    parser.add_argument("--train-limit", type=int, default=5000, help="Train samples per language")
    parser.add_argument("--test-limit", type=int, default=1000, help="Test samples per language")
    parser.add_argument("--epochs", type=int, default=2, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    args = parser.parse_args()

    print(f"Loading data (limit train={args.train_limit}, test={args.test_limit} per language)...")
    train_dataset = load_local_dataset("train", args.train_limit)
    test_dataset = load_local_dataset("test", args.test_limit)
    print(f"Loaded {len(train_dataset):,} train and {len(test_dataset):,} test rows.")

    print(f"Loading tokenizer & model: {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    def preprocess_function(examples):
        return tokenizer(examples["text"], truncation=True, max_length=128)

    print("Tokenizing datasets...")
    train_tokenized = train_dataset.map(preprocess_function, batched=True)
    test_tokenized = test_dataset.map(preprocess_function, batched=True)

    # Determine device
    device = "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
    elif torch.cuda.is_available():
        device = "cuda"
    print(f"Using device: {device}")

    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=3).to(device)

    # Output directory
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    output_dir = MODELS_DIR / "checkpoint"

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        learning_rate=3e-5,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        seed=SEED,
        data_seed=SEED,
        logging_steps=100,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tokenized,
        eval_dataset=test_tokenized,
        compute_metrics=compute_metrics,
        processing_class=tokenizer,
    )

    print("Starting fine-tuning...")
    start_train_time = time.time()
    trainer.train()
    end_train_time = time.time()
    train_duration = end_train_time - start_train_time
    print(f"Training completed in {train_duration:.2f} seconds.")

    # Save tokenizer and best model
    best_model_path = MODELS_DIR / "best_model"
    model.save_pretrained(best_model_path)
    tokenizer.save_pretrained(best_model_path)
    print(f"Best model saved to {best_model_path}")

    # Evaluate Overall
    print("Evaluating overall performance...")
    eval_results = trainer.evaluate()
    
    # Measure Latency / Throughput on CPU and MPS/GPU
    print("Measuring throughput...")
    
    # Let's select 1000 samples for throughput test
    test_subset = test_tokenized.select(range(min(1000, len(test_tokenized))))
    
    # MPS Throughput
    model.to(device)
    start_time = time.time()
    with torch.no_grad():
        for i in range(0, len(test_subset), args.batch_size):
            batch = test_subset[i:i+args.batch_size]
            inputs = tokenizer(batch["text"], return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
            _ = model(**inputs)
    mps_duration = time.time() - start_time
    mps_throughput = len(test_subset) / mps_duration
    
    # CPU Throughput
    model.to("cpu")
    start_time = time.time()
    with torch.no_grad():
        for i in range(0, len(test_subset), args.batch_size):
            batch = test_subset[i:i+args.batch_size]
            inputs = tokenizer(batch["text"], return_tensors="pt", padding=True, truncation=True, max_length=128).to("cpu")
            _ = model(**inputs)
    cpu_duration = time.time() - start_time
    cpu_throughput = len(test_subset) / cpu_duration

    print(f"MPS Throughput: {mps_throughput:.2f} reviews/sec")
    print(f"CPU Throughput: {cpu_throughput:.2f} reviews/sec")

    # Evaluate per language
    print("Evaluating per-language metrics...")
    lang_metrics = {}
    model.to(device)
    for lang in LANGUAGES:
        lang_subset = test_tokenized.filter(lambda x: x["language"] == lang)
        
        preds = []
        labels = []
        with torch.no_grad():
            for i in range(0, len(lang_subset), args.batch_size):
                batch = lang_subset[i:i+args.batch_size]
                inputs = tokenizer(batch["text"], return_tensors="pt", padding=True, truncation=True, max_length=128).to(device)
                outputs = model(**inputs)
                batch_preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
                preds.extend(batch_preds)
                labels.extend(batch["label"])
                
        acc = accuracy_score(labels, preds)
        macro_f1 = f1_score(labels, preds, average="macro")
        lang_metrics[lang] = {
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "count": len(labels)
        }
        print(f"  {lang}: accuracy={acc:.4f}, macro_f1={macro_f1:.4f}")

    # Determinism Check
    print("Checking determinism...")
    sample_text = ["This product is amazing!", "Das ist schrecklich.", "No me gusta para nada."]
    inputs = tokenizer(sample_text, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        out1 = model(**inputs).logits.cpu().numpy()
        out2 = model(**inputs).logits.cpu().numpy()
    
    deterministic = np.allclose(out1, out2)
    print(f"Determinism Check: {'PASS' if deterministic else 'FAIL'}")

    # Save all metrics
    metrics = {
        "model_name": args.model_name,
        "train_limit_per_lang": args.train_limit,
        "test_limit_per_lang": args.test_limit,
        "training_time_sec": train_duration,
        "overall_accuracy": float(eval_results["eval_accuracy"]),
        "overall_macro_f1": float(eval_results["eval_macro_f1"]),
        "mps_throughput_reviews_per_sec": mps_throughput,
        "cpu_throughput_reviews_per_sec": cpu_throughput,
        "deterministic": bool(deterministic),
        "per_language": lang_metrics
    }
    
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"All metrics saved to {METRICS_PATH}")


if __name__ == "__main__":
    main()
