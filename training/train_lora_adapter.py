"""
LoRA Adapter Training Pipeline
Coder: Claude Sonnet 4.5
Awaiting Peer Review

Trains LoRA adapters using QLoRA (quantized LoRA) for archetype-specific behaviors.

Uses:
- Hugging Face PEFT library
- BitsAndBytes for 4-bit quantization
- Training data from curate_archetype_data.py

Trains 7 adapters per archetype:
- personality, dialogue_style, action_policy, emotional_response
- world_knowledge, social_dynamics, goal_prioritization
"""

import os
import json
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
        Trainer
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from datasets import Dataset
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Required packages not installed: {e}")
    logger.error("Install with: pip install transformers peft bitsandbytes datasets accelerate")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for LoRA training."""
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    archetype: str = "vampire"
    adapter_task: str = "personality"
    training_data_path: str = "training/data/vampire_personality_training.json"
    output_dir: str = "training/adapters/vampire/personality"
    
    # LoRA config
    lora_rank: int = 32
    lora_alpha: float = 16.0
    lora_dropout: float = 0.05
    
    # Training config
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 2048
    gradient_accumulation_steps: int = 4
    
    # Quantization
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"


class LoRATrainer:
    """
    Trains LoRA adapters for archetype-specific tasks.
    
    Uses QLoRA (quantized LoRA) for memory-efficient training.
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.dataset = None
        
        logger.info(f"LoRATrainer initialized: {config.archetype}_{config.adapter_task}")
    
    def load_base_model(self) -> None:
        """
        Load base model with 4-bit quantization.
        
        Uses BitsAndBytes for quantization (reduces memory from 14GB to ~3.5GB).
        """
        logger.info(f"Loading base model: {self.config.base_model}")
        
        # Quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=self.config.use_4bit,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=True  # Nested quantization for extra efficiency
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        logger.info("✅ Base model loaded with 4-bit quantization")
    
    def apply_lora_config(self) -> None:
        """
        Apply LoRA configuration to base model.
        
        LoRA adds trainable low-rank matrices to attention layers.
        """
        logger.info("Applying LoRA configuration...")
        
        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Attention layers
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        logger.info(f"✅ LoRA applied: {trainable_params:,} trainable params ({trainable_params/total_params*100:.2f}% of total)")
    
    def load_training_data(self) -> None:
        """Load and prepare training data."""
        logger.info(f"Loading training data from {self.config.training_data_path}")
        
        with open(self.config.training_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        examples = data['examples']
        logger.info(f"Loaded {len(examples)} training examples")
        
        # Prepare dataset
        formatted_examples = []
        for ex in examples:
            # Format as instruction-following examples
            formatted = {
                'text': f"### Input:\n{ex['input']}\n\n### Output:\n{ex['output']}"
            }
            formatted_examples.append(formatted)
        
        self.dataset = Dataset.from_list(formatted_examples)
        logger.info("✅ Training data prepared")
    
    def tokenize_dataset(self) -> None:
        """Tokenize dataset for training."""
        logger.info("Tokenizing dataset...")
        
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                truncation=True,
                max_length=self.config.max_seq_length,
                padding="max_length"
            )
        
        self.dataset = self.dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=['text']
        )
        
        logger.info("✅ Dataset tokenized")
    
    def train(self) -> None:
        """Train LoRA adapter."""
        logger.info(f"Starting training: {self.config.num_epochs} epochs")
        
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            fp16=True,
            logging_steps=10,
            save_strategy="epoch",
            optim="paged_adamw_8bit",  # Memory-efficient optimizer
            warmup_steps=100,
            lr_scheduler_type="cosine",
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.dataset,
        )
        
        trainer.train()
        
        logger.info("✅ Training complete")
    
    def save_adapter(self) -> None:
        """Save trained LoRA adapter."""
        logger.info(f"Saving adapter to {self.config.output_dir}")
        
        self.model.save_pretrained(self.config.output_dir)
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        # Save config
        config_path = Path(self.config.output_dir) / "training_config.json"
        with open(config_path, 'w') as f:
            json.dump({
                'base_model': self.config.base_model,
                'archetype': self.config.archetype,
                'adapter_task': self.config.adapter_task,
                'lora_rank': self.config.lora_rank,
                'lora_alpha': self.config.lora_alpha,
                'num_epochs': self.config.num_epochs,
                'training_data_path': self.config.training_data_path,
            }, f, indent=2)
        
        logger.info(f"✅ Adapter saved to {self.config.output_dir}")
    
    def train_adapter(self) -> None:
        """Complete training pipeline."""
        self.load_base_model()
        self.apply_lora_config()
        self.load_training_data()
        self.tokenize_dataset()
        self.train()
        self.save_adapter()


def train_all_vampire_adapters():
    """Train all 7 vampire adapters."""
    adapter_tasks = [
        "personality", "dialogue_style", "action_policy",
        "emotional_response", "world_knowledge", "social_dynamics",
        "goal_prioritization"
    ]
    
    for task in adapter_tasks:
        logger.info(f"\n{'='*60}\nTraining Vampire {task} Adapter\n{'='*60}")
        
        config = TrainingConfig(
            archetype="vampire",
            adapter_task=task,
            training_data_path=f"training/data/vampire_{task}_training.json",
            output_dir=f"training/adapters/vampire/{task}"
        )
        
        trainer = LoRATrainer(config)
        trainer.train_adapter()


def train_all_zombie_adapters():
    """Train all 7 zombie adapters."""
    adapter_tasks = [
        "personality", "dialogue_style", "action_policy",
        "emotional_response", "world_knowledge", "social_dynamics",
        "goal_prioritization"
    ]
    
    for task in adapter_tasks:
        logger.info(f"\n{'='*60}\nTraining Zombie {task} Adapter\n{'='*60}")
        
        config = TrainingConfig(
            archetype="zombie",
            adapter_task=task,
            training_data_path=f"training/data/zombie_{task}_training.json",
            output_dir=f"training/adapters/zombie/{task}"
        )
        
        trainer = LoRATrainer(config)
        trainer.train_adapter()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--archetype", choices=["vampire", "zombie", "all"], default="vampire")
    parser.add_argument("--task", help="Specific task to train (or 'all')")
    args = parser.parse_args()
    
    if args.archetype == "all":
        train_all_vampire_adapters()
        train_all_zombie_adapters()
    elif args.archetype == "vampire":
        if args.task and args.task != "all":
            config = TrainingConfig(
                archetype="vampire",
                adapter_task=args.task,
                training_data_path=f"training/data/vampire_{args.task}_training.json",
                output_dir=f"training/adapters/vampire/{args.task}"
            )
            trainer = LoRATrainer(config)
            trainer.train_adapter()
        else:
            train_all_vampire_adapters()
    elif args.archetype == "zombie":
        if args.task and args.task != "all":
            config = TrainingConfig(
                archetype="zombie",
                adapter_task=args.task,
                training_data_path=f"training/data/zombie_{args.task}_training.json",
                output_dir=f"training/adapters/zombie/{args.task}"
            )
            trainer = LoRATrainer(config)
            trainer.train_adapter()
        else:
            train_all_zombie_adapters()

