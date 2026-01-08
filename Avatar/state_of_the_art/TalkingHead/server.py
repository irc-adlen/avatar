from flask import Flask, request, Response
import requests

app = Flask(__name__)

@app.route("/tts", methods=["POST", "OPTIONS"])
def tts():
    # Réponse au preflight CORS
    if request.method == "OPTIONS":
        return Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:8000",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    # Requête réelle vers Piper
    r = requests.post(
        "http://localhost:5002",
        json=request.json
    )

    return Response(
        r.content,
        mimetype="audio/wav",
        headers={
            "Access-Control-Allow-Origin": "http://localhost:8000"
        }
    )

app.run(port=5003)
