# 

# transcriber_core.py

import os
import time
import yt_dlp
from pydub import AudioSegment
import speech_recognition as sr
from googletrans import Translator

def download_audio_from_url(video_url):
    output_template = "downloaded_audio.%(ext)s"
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            audio_file = audio_file.rsplit('.', 1)[0] + ".mp3"
            return audio_file if os.path.exists(audio_file) else None
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def split_audio(file_path, segment_duration_ms=30000, overlap_ms=1000):
    audio = AudioSegment.from_file(file_path).set_frame_rate(16000).set_channels(1).normalize()
    segment_paths = []
    folder = "audio_segments"
    os.makedirs(folder, exist_ok=True)

    start = 0
    i = 0
    while start < len(audio):
        end = start + segment_duration_ms
        segment = audio[start:end]
        segment_path = os.path.join(folder, f"segment_{i}.wav")
        segment.export(segment_path, format="wav")
        segment_paths.append(segment_path)
        start += segment_duration_ms - overlap_ms
        i += 1

    return segment_paths

def file_to_text(recognizer, file_path, input_language):
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data, language=input_language)
    except sr.UnknownValueError:
        return "[Unrecognized speech]"
    except sr.RequestError as e:
        return ""

def translate_text(text, target_language):
    if target_language == "none":
        return text
    translator = Translator()
    try:
        return translator.translate(text, dest=target_language).text
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def transcribe_audio(audio_file_path, input_language, target_language):
    results = []
    if not os.path.exists(audio_file_path):
        return results

    recognizer = sr.Recognizer()
    segment_duration_ms = 30000
    audio = AudioSegment.from_file(audio_file_path).set_frame_rate(16000).set_channels(1).normalize()

    if len(audio) > segment_duration_ms:
        segment_paths = split_audio(audio_file_path, segment_duration_ms)
        for segment_path in segment_paths:
            original_text = file_to_text(recognizer, segment_path, input_language)
            translated_text = translate_text(original_text, target_language) if original_text else ""
            results.append(translated_text)
            os.remove(segment_path)
    else:
        original_text = file_to_text(recognizer, audio_file_path, input_language)
        translated_text = translate_text(original_text, target_language)
        results.append(translated_text)

    return results
