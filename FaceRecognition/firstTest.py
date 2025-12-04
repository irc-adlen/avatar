import cv2
import numpy as np
import insightface
from datetime import datetime, timedelta
from insightface.app import FaceAnalysis

# Initialise l'application InsightFace
# "buffalo_l" contient SCRFD pour la détection et ArcFace pour l'embedding
# app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"]) # For CPU
app = FaceAnalysis(name="buffalo_l", providers=["ROCMExecutionProvider"]) # For AMD GPU with ROCm
# app = FaceAnalysis(name="buffalo_l") # Let ONNX Runtime choose the best available provider
app.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0 = CPU, -1 = auto

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
            if known_faces[best_name]["lastSeen"] is None or datetime.now() - known_faces[best_name]["lastSeen"] > timedelta(minutes=5):
                print(f"{best_name} ({known_faces[best_name]['promo']}) reconnu à {datetime.now().strftime('%H:%M:%S')}")
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


