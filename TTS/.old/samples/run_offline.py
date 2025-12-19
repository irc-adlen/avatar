import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# PATHS TO SUBFOLDERS
model_path = "./parler_offline/model"
prompt_tok_path = "./parler_offline/prompt_tokenizer"
desc_tok_path = "./parler_offline/description_tokenizer"

print(f"Loading from local storage on {device}...")

# Load from specific subfolders
model = ParlerTTSForConditionalGeneration.from_pretrained(model_path).to(device)
prompt_tokenizer = AutoTokenizer.from_pretrained(prompt_tok_path)
description_tokenizer = AutoTokenizer.from_pretrained(desc_tok_path)

def generate_speech(text_prompt, description, filename):
    print(f"Generating {filename}...")
    
    # 1. Tokenize Description
    # We explicitly move tensors to device here
    input_ids = description_tokenizer(description, return_tensors="pt").input_ids.to(device)
    attention_mask = description_tokenizer(description, return_tensors="pt").attention_mask.to(device)
    
    # 2. Tokenize Prompt
    prompt_input_ids = prompt_tokenizer(text_prompt, return_tensors="pt").input_ids.to(device)
    prompt_attention_mask = prompt_tokenizer(text_prompt, return_tensors="pt").attention_mask.to(device)

    # 3. Generate
    # We pass the arguments exactly by name
    generation = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        prompt_input_ids=prompt_input_ids,
        prompt_attention_mask=prompt_attention_mask,
        max_length=2580,
        do_sample=True
    )
    
    # 4. Save
    audio_arr = generation.cpu().numpy().squeeze()
    sf.write(filename, audio_arr, model.config.sampling_rate)
    print(f"Success! Saved to {filename}")

prompt_text = "En descendant de la voiture, ils savaient qu'ils ne devaient plus s'appeler par leurs prénoms. Ils redevenaient Athéna, Arès et Hadès. Ces surnoms, au début, ils les avaient adoptés comme un jeu. Un peu comme des gamins, ils fuyaient un monde qu'ils refusaient. Ils redistribuaient les cartes — en premier lieu, celles de leur identité. Ils se choisissaient."

# Option A: Christine (Likely the best)
desc_christine = "Christine's voice is very clear, expressive and animated, with a moderate speed. The recording is of very high quality."
generate_speech(prompt_text, desc_christine, "french_christine.wav")

# Option B: Improved Daniel (Warmer, slower)
desc_daniel_better = "Daniel's voice is deep, warm, and expressive, with a slow speaking rate and very clear audio."
generate_speech(prompt_text, desc_daniel_better, "french_daniel_improved.wav")

# --- ENGLISH TEST ---
# generate_speech(
#     "Hello, this is the corrected test running with separated tokenizers.",
#     "A female speaker delivers a slightly expressive and animated speech with a moderate speed and pitch. The recording is of very high quality.",
#     "test_fix_english.wav"
# )