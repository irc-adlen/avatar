import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationMixin
from PIL import Image
import json

def reco():

    # 1. Chargement du modèle
    model_id = "vikhyatk/moondream2"
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)

    # PATCH UNIVERSEL : On injecte les capacités de génération si elles manquent
    if not isinstance(model, GenerationMixin):
        print("Injection de GenerationMixin...")
        model.__class__ = type("MoondreamPatcher", (model.__class__, GenerationMixin), {})

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model.eval()

    # 2. Préparation de l'image
    image_path = "tests/black_cheveux_court_noir_yeux_marron_barbe_moyen_black.jpg" 
    image = Image.open(image_path)
    enc_image = model.encode_image(image)

    # 3. Stratégie de questions ciblées
    schema = {
        "glasses": "Does the person wear glasses? Answer only 'yes' or 'no'.",
        "beard": "Does the person have a beard? Answer with 'none', 'short', or 'long'.",
        "beard_color": "What is the beard color? Answer with 'black', 'brown' or 'blond'.",
        "hair": "What is the hair style? Answer with 'none', 'short', or 'long'.",
        "hair_color": "What is the hair color? Answer with 'black', 'brown', or 'blond'.",
        "eyes": "What is the eye color? Answer with 'blue', 'brown', or 'green'.",
        "skin_tone": "What is the skin tone? Answer with 'light', 'medium', or 'dark'."
    }

    detected_features = {}

    print("Analyse en cours...")
    for key, question in schema.items():
        # On utilise directement model.answer_question
        answer = model.answer_question(enc_image, question, tokenizer)
        # Nettoyage minimal pour ne garder que la valeur pertinente
        clean_answer = answer.strip().lower().replace(".", "")
        detected_features[key] = clean_answer

    # 4. Affichage du JSON final
    print("\nRésultat final en JSON :")
    print(json.dumps(detected_features, indent=4))
    return json.dumps(detected_features, indent=4)