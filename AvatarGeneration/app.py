from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationMixin
from PIL import Image
import io
import json
import os

app = Flask(__name__)
CORS(app)  # Autorise les requêtes provenant de votre interface HTML

# --- INITIALISATION DU MODÈLE ---

model_id = "vikhyatk/moondream2"
local_model_path = "./moondream2_local"

# Télécharge le modèle si inexistant en local, sinon charge depuis le dossier local
if os.path.exists(local_model_path):
    print(f"Chargement du modèle depuis {local_model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        local_model_path, 
        trust_remote_code=True,
        torch_dtype=torch.float32,
        local_files_only=True
    )
    tokenizer = AutoTokenizer.from_pretrained(local_model_path, local_files_only=True)
else:
    print(f"Téléchargement du modèle {model_id} et sauvegarde dans {local_model_path}")
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        trust_remote_code=True,
        torch_dtype=torch.float32
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Sauvegarde en local pour les prochaines fois
    model.save_pretrained(local_model_path)
    tokenizer.save_pretrained(local_model_path)
    print(f"Modèle sauvegardé dans {local_model_path}")

# Patch pour la compatibilité
if not isinstance(model, GenerationMixin):
    model.__class__ = type("MoondreamPatcher", (model.__class__, GenerationMixin), {})

model.eval()


@app.route('/process', methods=['POST'])
def process_image():
    print("Request well received")
    if 'image' not in request.files:
        return jsonify({"error": "Aucune image envoyée"}), 400
    
    file = request.files['image']
    
    try:
        # Conversion du fichier envoyé en objet Image PIL
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))
        
        # Redimensionner l'image pour accélérer le traitement
        max_size = 768
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Encodage de l'image
        import time
        start = time.time()
        with torch.no_grad():
            enc_image = model.encode_image(image)
        print(f"Encodage: {time.time() - start:.2f}s")

        schema = {
            "glasses": "Does the person wear glasses? Answer only 'yes' or 'no'.",
            "beard": "Does the person have a beard? Answer with 'none', 'short', or 'long'.",
            "beard_color": "What is the beard color? Answer with 'black', 'brown' or 'blond'.",
            "hair": "What is the hair style? Answer with 'none', 'short', or 'long'.",
            "hair_color": "What is the hair color? Answer with 'black', 'brown', or 'blond'.",
            "eyes": "What is the eye color? Answer with 'blue', 'brown', or 'green'.",
            "skin_tone": "What is the skin tone? Answer with 'light', 'medium', or 'dark'."
        }
        
        # Analyse selon le schéma
        detected_features = {}
        print("Analyse en cours...")
        for key, question in schema.items():
            # On utilise directement model.answer_question
            answer = model.answer_question(enc_image, question, tokenizer)
            # Nettoyage minimal pour ne garder que la valeur pertinente
            clean_answer = answer.strip().lower().replace(".", "")
            detected_features[key] = clean_answer
        
        '''detected_features = {
            "glasses": "yes",
            "beard": "long",
            "beard_color": "black",
            "hair": "short",
            "hair_color": "black",
            "eyes": "green",
            "skin_tone": "dark"
        }'''
        
        print(f"Analyse réussie : {detected_features}")
        print(f"Start mapping...")

        mapping = [] 
        if detected_features["glasses"] == "yes":
            mapping.append("GLASSES_YES")
        mapping.append("beard_"+detected_features["beard"]+"_"+detected_features["beard_color"])
        mapping.append("hair_"+detected_features["hair"]+"_"+detected_features["hair_color"])
        mapping.append("eyes_"+detected_features["eyes"]+"_left")
        mapping.append("eyes_"+detected_features["eyes"]+"_right")
        mapping.append("head_"+detected_features["skin_tone"])

        
        # Retourne les résultats à l'IHM
        return jsonify({
            "status": "success",
            "mapping": mapping,
            "message": "Analyse complétée"
        })

    except Exception as e:
        print(f"Erreur : {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Lancement du serveur sur le port 5000
    app.run(host='0.0.0.0', port=5010, debug=False)