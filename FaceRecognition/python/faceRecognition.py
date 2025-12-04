import cv2
import numpy as np
from datetime import datetime, timedelta
from insightface.app import FaceAnalysis
import os
import psycopg2
from dotenv import load_dotenv, find_dotenv


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

print(f"Loaded env from: {env_path}")

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
    """Return all rows from the `people` table as a list of dicts.

    If the table does not exist or an error occurs, prints the error and
    returns an empty list.
    """
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM people;")
        cols = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]
    except Exception as e:
        print("DB select_allPeople error:", e)
        return []

# Ensure the detections table exists
try:
    print(select_allPeople())
except Exception as e:
    print("Warning: could not connect to DB at startup:", e)

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

# Exemple : liste de visages connus
known_faces = {
    "Mathis": {"embed": get_embedding_from_image("./faces/mathis.jpeg"), "promo": "5IRC", "lastSeen":None},
    "Clem": {"embed": get_embedding_from_image("./faces/clem.jpeg"), "promo": "4IRC", "lastSeen":None}
}

# Distance cosinus entre deux embeddings
def cosine_similarity(a, b):
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    return np.dot(a_norm, b_norm)

# --- Lecture webcam ---
cap = cv2.VideoCapture(0)

THRESHOLD = 0.3  # seuil typique pour ArcFace (plus proche de 1 = plus strict)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = app.get(frame)

    for face in faces:
        # Récupère embedding du visage filmé
        emb = face.embedding

        # Trouve la meilleure correspondance
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
            if datetime.now() - known_faces[best_name]["lastSeen"] > timedelta(seconds=10):
                try:
                    update_detection(best_name, known_faces[best_name]['promo'], datetime.now())
                except Exception as e:
                    print("Error inserting detection:", e)
            # Update the last seen time
            known_faces[best_name]["lastSeen"] = datetime.now()

        # Dessin sur l'image
        x1, y1, x2, y2 = face.bbox.astype(int)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{best_name} ({best_score:.2f})", 
                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (0, 255, 0), 2)

    cv2.imshow("InsightFace - ArcFace + SCRFD", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()


