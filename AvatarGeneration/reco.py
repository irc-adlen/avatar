import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationMixin
from PIL import Image
import json

# 1. Gestion du Device (Force le CPU pour éviter le conflit MPS/CPU sur Mac)
device = "cpu" 
print(f"Utilisation du device : {device}")

# 2. Chargement du modèle
model_id = "vikhyatk/moondream2"
model = AutoModelForCausalLM.from_pretrained(
    model_id, 
    trust_remote_code=True,
    torch_dtype=torch.float32 # Plus stable sur CPU
).to(device)

# PATCH UNIVERSEL
if not isinstance(model, GenerationMixin):
    model.__class__ = type("MoondreamPatcher", (model.__class__, GenerationMixin), {})

tokenizer = AutoTokenizer.from_pretrained(model_id)
model.eval()

# 3. Préparation de l'image
image_path = "cheveux_court_yeux_marron_peau_marron_lunette_barbe_moyenne.jpg" 
image = Image.open(image_path)

# On s'assure que l'encodage se fait sur le bon device
with torch.no_grad():
    enc_image = model.encode_image(image)

# 4. Stratégie de questions ciblées
schema = {
    "glasses": "Does the person wear glasses? Answer only 'yes' or 'no'.",
    "beard": "Does the person have a beard? Answer with 'none', 'short', or 'long'.",
    "hair": "What is the hair style? Answer with 'bald', 'short', or 'long'."
}

detected_features = {}

print("Analyse en cours...")
for key, question in schema.items():
    # model.answer_question gère normalement le tokenizer en interne pour moondream
    answer = model.answer_question(enc_image, question, tokenizer)
    clean_answer = answer.strip().lower().replace(".", "")
    detected_features[key] = clean_answer

# 5. Affichage du JSON final
print("\nRésultat final en JSON :")
print(json.dumps(detected_features, indent=4))