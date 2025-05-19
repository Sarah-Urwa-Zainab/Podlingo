from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import shutil
from main import download_audio_from_url, transcribe_audio

app = Flask(__name__)
CORS(app)

@app.route('/transcribe', methods=['POST'])
def handle_transcription():
    input_language = request.form.get("input_language")
    target_language = request.form.get("target_language")
    audio_file = request.files.get("audio")
    video_url = request.form.get("video_url")

    if not input_language:
        return jsonify({"error": "Missing input_language"}), 400

    audio_path = None
    os.makedirs("uploads", exist_ok=True)

    try:
        if audio_file:
            audio_path = f"uploads/{int(time.time())}_{audio_file.filename}"
            audio_file.save(audio_path)
        elif video_url:
            audio_path = download_audio_from_url(video_url)
            if not audio_path:
                return jsonify({"error": "Failed to download audio"}), 500
        else:
            return jsonify({"error": "No audio file or video URL provided"}), 400

        transcribed_segments = transcribe_audio(audio_path, input_language, target_language)
        if not transcribed_segments:
            return jsonify({"error": "Transcription failed"}), 500

        return jsonify({"translated": " ".join(transcribed_segments)})

    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists("audio_segments"):
            shutil.rmtree("audio_segments")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
