from unittest import result
import cv2
import numpy as np
from datetime import datetime, timedelta
from insightface.app import FaceAnalysis
import os
import psycopg2
from dotenv import load_dotenv, find_dotenv
from flask import Flask, Response
import requests

flaskApp = Flask(__name__)

@flaskApp.route('/start_session', methods=['GET'])
def start_session():
    name = start_video_capture()
    if name is not None:
            url = 'http://host.docker.internal:8000/chat'
            myobj = {
                "prompt": f"Dis bonjour à {name}",
                "voice": "default_voice.wav"
            }
            requests.post(url, json = myobj)
    return Response(
        status=200,
    )

# Initialise l'application InsightFace
# "buffalo_l" contient SCRFD pour la détection et ArcFace pour l'embedding
# app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"]) # For CPU
app = FaceAnalysis(name="buffalo_l", providers=["ROCMExecutionProvider"]) # For AMD GPU with ROCm
# app = FaceAnalysis(name="buffalo_l") # Let ONNX Runtime choose the best available provider
app.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0 = CPU, -1 = auto

# Load .env file for DB connection
env_path = find_dotenv()
if not env_path:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
# --- Database connection setup -------------------------------------------------
# Read DB connection info from environment variables (defaults match docker-compose)
DB_HOST = "db"
DB_PORT = 5432
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

# --- Charger les visages connus ---
def get_embedding_from_image(img_path):
    """Charge une image, détecte un visage et renvoie son embedding."""
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Image introuvable : {img_path}")
    
    faces = app.get(img)
    if not faces:
        raise ValueError(f"Aucun visage détecté dans {img_path}")
    
    # On prend le premier visage détecté
    return faces[0].embedding

def get_db_conn():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                            user=DB_USER, password=DB_PASS)
    conn.autocommit = True
    return conn

def update_detection(name, promo, lastseen):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE people SET last_seen = %s where (name = %s AND promo = %s);",
            (lastseen, name, promo),
        )
        cur.close()
        conn.close()
    except Exception as e:
        print("DB insert error:", e)

def select_allPeople():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT name, promo, image_path, last_seen FROM people;")
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Format results as dict
        result = {}
        for row in rows:
            rowd = dict(zip(cols, row))
            name = rowd.get("name")
            promo = rowd.get("promo")
            img_path = rowd.get("image_path") or ""
            last_seen = rowd.get("last_seen")

            result[name] = {"embed": get_embedding_from_image(img_path), "promo": promo, "lastSeen":last_seen}

        return result
    except Exception as e:
        print("DB select_allPeople error:", e)
        return {}

# Ensure the detections table exists
try:
    known_faces = select_allPeople()
except Exception as e:
    print("Warning: could not connect to DB at startup:", e)

# Cosine distance between two embeddings
def cosine_similarity(a, b):
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    return np.dot(a_norm, b_norm)

def start_video_capture():
    global known_faces
    # Webcam capture
    cap = cv2.VideoCapture(0)

    THRESHOLD = 0.3  # seil to recognize face

    # while True:
    ret, frame = cap.read()
    if not ret:
        return

    faces = app.get(frame)
    best_name_size = None
    best_size = -1
    for face in faces:
        emb = face.embedding

        # Find the best matching known face
        best_name = "Inconnu"
        best_score = -1

        for name, values in known_faces.items():
            score = cosine_similarity(emb, values["embed"])
            if score > best_score:
                best_score = score
                best_name = name
            



        # Vérifie si la personne est reconnue
        if best_score < THRESHOLD:
            best_name = "Inconnu"
            
        if best_name != "Inconnu":
            # Check if the last time seen is in the last 5 minutes
            if known_faces[best_name]["lastSeen"] is None or datetime.now() - known_faces[best_name]["lastSeen"] > timedelta(minutes=1):
                print(f"{best_name} ({known_faces[best_name]['promo']}) reconnu à {datetime.now().strftime('%H:%M:%S')}")
            # Insert a detection record into Postgres
            try:
                update_detection(best_name, known_faces[best_name]['promo'], datetime.now())
            except Exception as e:
                print("Error inserting detection:", e)
            # Update the last seen time
            known_faces[best_name]["lastSeen"] = datetime.now()


        # Calcul de la personne la plus proche (plus grand visage)
        x1, y1, x2, y2 = face.bbox.astype(int)
        if x2-x1 > best_size:
            best_size = x2-x1
            best_name_size = best_name

    print(best_name_size)
    return best_name_size

def main():
    flaskApp.run(host='0.0.0.0', port=5006)

if __name__ == "__main__":
    main()