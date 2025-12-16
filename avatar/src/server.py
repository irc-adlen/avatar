from flask import Flask, request, Response, render_template
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tts", methods=["POST", "OPTIONS"])
def tts():
    if request.method == "OPTIONS":
        return Response(
            status=200,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:8000",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    r = requests.post(
        "http://tts:5002",
        json=request.json
    )

    return Response(
        r.content,
        mimetype="audio/wav",
        headers={
            "Access-Control-Allow-Origin": "http://localhost:8000"
        }
    )

app.run(host="0.0.0.0", port=5003)
