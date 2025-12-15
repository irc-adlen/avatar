from flask import Flask, request, jsonify
import whisper_timestamped as whisper
import json
import os

app = Flask(__name__)

@app.route('/api/word_timestamp', methods=['POST'])
def word_timestamp():
    # Vérifie si le fichier audio a bien été envoyé
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Sauvegarder le fichier audio temporairement
    temp_file_path = "temp_audio.wav"
    audio_file.save(temp_file_path)

    try:
        # Charger l'audio et le modèle
        audio = whisper.load_audio(temp_file_path)
        model = whisper.load_model("medium", device="cpu")

        # Transcrire avec les timestamps
        result = whisper.transcribe(model, audio, language="fr")

        # Retourner le résultat en JSON
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Supprimer le fichier audio temporaire
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
