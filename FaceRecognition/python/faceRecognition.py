import cv2
import numpy as np
from datetime import datetime, timedelta
from insightface.app import FaceAnalysis
import os
from flask import Flask, Response, request, jsonify
import requests
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
import secrets

flaskApp = Flask(__name__)
# ---------------- MongoDB ----------------
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.environ.get("MONGO_DB", "cpe_assistant_db")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "people")

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[MONGO_DB]
people_collection = mongo_db[MONGO_COLLECTION]
conversations_collection = mongo_db["conversations"]


# ---------------- InsightFace ----------------
app = FaceAnalysis(name="buffalo_l", providers=["ROCMExecutionProvider"])
app.prepare(ctx_id=0, det_size=(640, 640))

# ---------------- ENV ----------------
env_path = find_dotenv()
if not env_path:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

# ---------------- Utils ----------------
def get_embedding_from_image(img_path):
    """Load image, detect face and return embedding."""
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Image not found: {img_path}")

    faces = app.get(img)
    if not faces:
        raise ValueError(f"No face detected in {img_path}")

    return faces[0].embedding

def update_detection(name, promo, lastseen):
    """Update last_seen field in MongoDB."""
    try:
        people_collection.update_one(
            {"name": name, "promo": promo},
            {"$set": {"last_seen": lastseen}}
        )
    except Exception as e:
        print("MongoDB update error:", e)

def select_allPeople():
    """Load all known people from MongoDB."""
    try:
        result = {}
        for doc in people_collection.find():
            name = doc.get("name")
            promo = doc.get("promo")
            img_path = doc.get("image_path", "")
            last_seen = doc.get("last_seen")

            result[name] = {
                "embed": get_embedding_from_image(img_path),
                "promo": promo,
                "lastSeen": last_seen
            }
        return result
    except Exception as e:
        print("MongoDB select error:", e)
        return {}

def generate_unique_hash(conversations_collection, length=16):
    """
    Generate a unique random hash not already present in MongoDB.

    :param collection: pymongo collection
    :param field_name: field to check uniqueness
    :param length: length of the generated hash (in bytes)
    :return: unique hash string
    """
    while True:
        # Generate cryptographically strong random hash
        random_hash = secrets.token_hex(length)

        # Check if hash already exists in MongoDB
        exists = conversations_collection.find_one({"session_id": random_hash})

        if not exists:
            return random_hash

# Load known faces at startup
try:
    known_faces = select_allPeople()
except Exception as e:
    print("Warning: could not load known faces:", e)
    known_faces = {}

# ---------------- Face recognition ----------------
def cosine_similarity(a, b):
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    return np.dot(a_norm, b_norm)

def start_video_capture():
    global known_faces

    cap = cv2.VideoCapture(0)
    THRESHOLD = 0.3

    ret, frame = cap.read()
    if not ret:
        return None

    faces = app.get(frame)
    best_name_size = None
    best_size = -1

    for face in faces:
        emb = face.embedding
        best_name = "Inconnu"
        best_score = -1

        for name, values in known_faces.items():
            score = cosine_similarity(emb, values["embed"])
            if score > best_score:
                best_score = score
                best_name = name

        if best_score < THRESHOLD:
            best_name = "Inconnu"

        if best_name != "Inconnu":
            last_seen = known_faces[best_name]["lastSeen"]
            if last_seen is None or datetime.now() - last_seen > timedelta(minutes=1):
                print(f"{best_name} ({known_faces[best_name]['promo']}) reconnu")

            update_detection(best_name, known_faces[best_name]["promo"], datetime.now())
            known_faces[best_name]["lastSeen"] = datetime.now()

        x1, y1, x2, y2 = face.bbox.astype(int)
        if x2 - x1 > best_size:
            best_size = x2 - x1
            best_name_size = best_name

    return best_name_size

@flaskApp.route('/check_camera', methods=['GET'])
def check_camera():
    global conversations_collection
    name = start_video_capture()
    url = 'http://host.docker.internal:8000/chat'
    hash = generate_unique_hash(conversations_collection)
    if name is not None:
        myobj = {
            "prompt": f"Dis bonjour à {name}",
            "voice": "default_voice.wav",
            "session_id": hash
        }
    else:
        myobj = {
            "prompt": "Demande le prenom de la personne",
            "voice": "default_voice.wav",
            "session_id": hash
        }

    requests.post(url, json=myobj)
    return Response(status=200)

@flaskApp.route('/save_image', methods=['POST'])
def save_image():
    if not request.is_json:
        return jsonify({"error": "Expected JSON body"}), 400

    # Parse JSON body
    data = request.get_json()

    cap = cv2.VideoCapture(0)

    # Read one frame from the camera
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image")
        cap.release()
        exit(1)

    # Save the captured frame as an image file
    output_path = "captured_image.jpg"
    cv2.imwrite(output_path, frame)
    return Response(status=200)


def main():
    flaskApp.run(host='0.0.0.0', port=5006)

if __name__ == "__main__":
    main()
