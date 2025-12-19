import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import os

repo_id = "parler-tts/parler-tts-mini-multilingual-v1.1"
base_dir = "./parler_offline"

# Create sub-directories to avoid file conflicts
os.makedirs(f"{base_dir}/model", exist_ok=True)
os.makedirs(f"{base_dir}/prompt_tokenizer", exist_ok=True)
os.makedirs(f"{base_dir}/description_tokenizer", exist_ok=True)

print(f"Downloading model from {repo_id}...")

# 1. Load Model
model = ParlerTTSForConditionalGeneration.from_pretrained(repo_id)
# 2. Load Prompt Tokenizer (for the text you want spoken)
prompt_tokenizer = AutoTokenizer.from_pretrained(repo_id)
# 3. Load Description Tokenizer (for the style description)
description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)

print("Saving to separate folders...")

# Save Model
model.save_pretrained(f"{base_dir}/model")

# Save Prompt Tokenizer
prompt_tokenizer.save_pretrained(f"{base_dir}/prompt_tokenizer")

# Save Description Tokenizer
description_tokenizer.save_pretrained(f"{base_dir}/description_tokenizer")

print("Download complete. Structure fixed.")