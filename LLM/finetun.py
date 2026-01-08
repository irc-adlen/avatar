import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
from peft import LoraConfig, get_peft_model

model_id = "unsloth/gemma-2-27b-it-bnb-4bit"

# 1. Chargement du modèle (Pipeline Parallelism automatique)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto", # Répartit le modèle sur GPU 0 et GPU 1
    dtype=torch.bfloat16,
)

# Activation des optimisations mémoire
model.gradient_checkpointing_enable() 

tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.padding_side = 'right' 

# 2. Configuration LoRA (Rank 16 pour économiser la VRAM)
peft_config = LoraConfig(
    r=64, 
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, peft_config)

# 3. Préparation du Dataset
dataset = load_dataset("json", data_files="dataset_final.jsonl", split="train")

def formatting_prompts_func(example):
    messages = example["messages"]
    new_messages = []
    system_content = ""
    for msg in messages:
        if msg["role"] == "system":
            system_content = msg["content"] + "\n\n"
        elif msg["role"] == "user":
            if system_content:
                new_messages.append({"role": "user", "content": system_content + msg["content"]})
                system_content = ""
            else:
                new_messages.append(msg)
        else:
            new_messages.append(msg)
    return {"text": tokenizer.apply_chat_template(new_messages, tokenize=False)}

dataset = dataset.map(formatting_prompts_func, remove_columns=dataset.column_names)

# 4. Configuration SFT ultra-optimisée pour 2x24GB
training_args = SFTConfig(
    output_dir="./outputs_cpe_lyon",
    dataset_text_field="text",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16, 
    learning_rate=2e-4,
    bf16=True,
    max_steps=500,
    logging_steps=1,
    save_strategy="no",
    optim="paged_adamw_8bit", # Indispensable pour ne pas saturer la VRAM
    report_to="none",
    gradient_checkpointing=True,
)

# 5. Initialisation du Trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    args=training_args,
)

# Fix manuel de la longueur
trainer.max_seq_length = 2048

print("--- Entraînement de l'assistant CPE Lyon (Gemma-2-27B) ---")
trainer.train()

# Sauvegarde
model.save_pretrained("./model_cpe_27b_final")
tokenizer.save_pretrained("./model_cpe_27b_final")