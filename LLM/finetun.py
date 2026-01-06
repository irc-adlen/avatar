from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset

# 1. Configuration (24Go par GPU est énorme pour un 8B, tu peux augmenter max_seq_length)
max_seq_length = 4096 
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-instruct-bnb-4bit",
    max_seq_length = max_seq_length,
    load_in_4bit = True,
)

# 2. Correction des MLP layers (On ajoute gate, up, down_proj)
model = FastLanguageModel.get_peft_model(
    model,
    r = 32,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"], # Ajoute ceux-là !
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
)

# 3. Chargement et Préparation du Dataset
dataset = load_dataset("json", data_files="dataset_final.jsonl", split="train")

# FONCTION DE FORMATAGE (C'est ce qui manquait !)
def formatting_prompts_func(examples):
    instructions = examples["messages"]
    texts = [tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False) for messages in instructions]
    return { "text" : texts, }

dataset = dataset.map(formatting_prompts_func, batched = True)

# 4. Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text", # On pointe vers le champ "text" généré par formatting_prompts_func
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 150,
        learning_rate = 2e-4,
        fp16 = False,
        bf16 = True,
        logging_steps = 1,
        output_dir = "outputs",
    ),
)

trainer.train()

model.save_pretrained_gguf("model_cpe_lyon", tokenizer, quantization_method = "q4_k_m")