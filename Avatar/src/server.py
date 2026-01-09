from flask import Flask, request, Response, render_template, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import requests
import os
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import json
from pygltflib import GLTF2, PbrMetallicRoughness

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
IMG_PATH = '/app/captures/new_user.jpg'
GLB_BASE_PATH = os.path.join(DATA_FOLDER, 'avatar_custom_20260108_173302.glb')

model_id = "openai/clip-vit-large-patch14"
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = CLIPModel.from_pretrained(model_id).to(device)
processor = CLIPProcessor.from_pretrained(model_id)
model.eval()

def load_color_libraries():
    libraries = {}
    color_files = {
        'hair_color': 'hair_color_library.json',
        'beard_color': 'beard_color_library.json',
        'eyes_color': 'eyes_color_library.json',
        'skin_color': 'skin_color_library.json'
    }
    for key, filename in color_files.items():
        filepath = os.path.join(DATA_FOLDER, filename)
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                libraries[key] = {texture["tag"]: texture for texture in data.get("textures", [])}
        except:
            libraries[key] = {}
    return libraries

COLOR_LIBRARIES = load_color_libraries()

def find_best_match(image, options, category_name):
    if category_name in ["beard", "hair"]:
        text_prompts = [f"a person with {opt.replace('_', ' ')}" for opt in options]
    elif category_name in ["beard_color", "hair_color", "eyes_color", "skin_tone"]:
        color_descriptions = {
            "#4D3826": "dark brown", "#000000": "black", "#1C1C1B": "very dark brown",
            "#444445": "dark gray", "#513C2E": "brown", "#5A4234": "medium brown",
            "#704E41": "chestnut brown", "#926144": "light brown", "#6D5B41": "tan brown",
            "#856E4A": "sandy brown", "#93826D": "ash brown", "#AD8B62": "light blonde",
            "#2A1B16": "dark brown eyes", "#63473A": "brown eyes", "#8E5A2D": "hazel eyes",
            "#60646B": "gray eyes", "#4E6066": "blue gray eyes", "#555D3A": "green eyes",
            "#8A7228": "light green eyes", "#5C8A93": "blue eyes",
            "#D4A384": "light skin", "#C9967A": "fair skin", "#C29173": "beige skin",
            "#B78568": "tan skin", "#AE7C5F": "medium tan skin", "#A57356": "olive skin",
            "#8D5F48": "brown skin", "#7D513D": "dark brown skin", "#6B4534": "deep brown skin",
            "#54372A": "very dark brown skin", "#452D21": "dark skin"
        }
        if category_name in ["beard_color", "hair_color"]:
            text_prompts = [f"a person with {color_descriptions.get(opt, 'colored')} {category_name.split('_')[0]}" for opt in options]
        elif category_name == "eyes_color":
            text_prompts = [f"a person with {color_descriptions.get(opt, 'colored')} eyes" for opt in options]
        else:
            text_prompts = [f"a person with {color_descriptions.get(opt, 'skin tone')}" for opt in options]
    else:
        text_prompts = options
    
    inputs = processor(text=text_prompts, images=image, return_tensors="pt", padding=True).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    
    best_idx = probs.argmax().item()
    return options[best_idx], probs[0][best_idx].item()

def analyze_image_and_get_features():
    if not os.path.exists(IMG_PATH):
        raise FileNotFoundError(f"Image non trouvée: {IMG_PATH}")
    
    image = Image.open(IMG_PATH).convert('RGB')
    
    with open(os.path.join(DATA_FOLDER, "beard_labels.json"), "r") as f:
        beard_options = json.load(f)
    with open(os.path.join(DATA_FOLDER, "beard_color_labels.json"), "r") as f:
        beard_color_options = json.load(f)
    with open(os.path.join(DATA_FOLDER, "hair_labels.json"), "r") as f:
        hair_options = json.load(f)
    with open(os.path.join(DATA_FOLDER, "hair_color_labels.json"), "r") as f:
        hair_color_options = json.load(f)
    with open(os.path.join(DATA_FOLDER, "eyes_color_labels.json"), "r") as f:
        eyes_color_options = json.load(f)
    with open(os.path.join(DATA_FOLDER, "skin_color_labels.json"), "r") as f:
        skin_tone_options = json.load(f)

    detected_features = {}
    detected_features["beard"], _ = find_best_match(image, beard_options, "beard")
    detected_features["beard_color"], _ = find_best_match(image, beard_color_options, "beard_color")
    detected_features["hair"], _ = find_best_match(image, hair_options, "hair")
    detected_features["hair_color"], _ = find_best_match(image, hair_color_options, "hair_color")
    detected_features["eyes_color"], _ = find_best_match(image, eyes_color_options, "eyes_color")
    detected_features["skin_tone"], _ = find_best_match(image, skin_tone_options, "skin_tone")
    
    return detected_features

@app.route("/process", methods=["GET"])
def process():
    try:
        features = analyze_image_and_get_features()
        return jsonify({"status": "success", "features": features})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/trigger", methods=["GET", "POST"])
def trigger():
    try:
        features = analyze_image_and_get_features()
        socketio.emit('avatar_update', {
            'status': 'success',
            'features': features,
            'glb_url': 'data/avatar_custom_20260108_173302.glb'
        })
        return jsonify({"status": "success", "features": features})
    except Exception as e:
        print(f"Error in /trigger: {e}", flush=True)
        import traceback
        traceback.print_exc()
        socketio.emit('avatar_update', {'status': 'error', 'message': str(e)})
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'OK'})

@socketio.on('request_avatar')
def handle_request_avatar():
    try:
        features = analyze_image_and_get_features()
        emit('avatar_update', {
            'status': 'success',
            'features': features,
            'glb_url': 'data/avatar_custom_20260108_173302.glb'
        })
    except Exception as e:
        emit('avatar_update', {'status': 'error', 'message': str(e)})

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/data/<path:filename>")
def serve_data(filename):
    file_path = os.path.join(DATA_FOLDER, filename)
    if not os.path.exists(file_path):
        return Response("File not found", status=404)
    response = send_from_directory(DATA_FOLDER, filename)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/tts", methods=["POST", "OPTIONS"])
def tts():
    if request.method == "OPTIONS":
        return Response(status=200, headers={
            "Access-Control-Allow-Origin": "http://localhost:8000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    r = requests.post("http://tts:5002", json=request.json)
    return Response(r.content, mimetype="audio/wav", headers={"Access-Control-Allow-Origin": "http://localhost:8000"})

@app.route("/stt", methods=["POST", "OPTIONS"])
def stt():
    if request.method == "OPTIONS":
        return Response(status=200, headers={
            "Access-Control-Allow-Origin": "http://localhost:8000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })
    r = requests.post("http://stt_timestamp:5004/api/word_timestamp", files=request.files)
    return Response(r.content, headers={"Access-Control-Allow-Origin": "http://localhost:8000"})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5003, debug=False, allow_unsafe_werkzeug=True)
