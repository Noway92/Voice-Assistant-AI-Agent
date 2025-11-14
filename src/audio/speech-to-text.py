import whisper
import sounddevice as sd
import numpy as np
import soundfile as sf
import io
import os
from pydub import AudioSegment

def record_audio(duration=5, samplerate=16000, filename="enregistrement.mp3"):
    print("🎙️ Enregistrement...")
    # Enregistrement de l'audio
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()
    
    # Conversion en format approprié pour l'export MP3
    audio_int16 = (audio.flatten() * 32767).astype(np.int16)
    
    # Sauvegarde en MP3
    sf.write(filename, audio_int16, samplerate, format='mp3')
    print(f"✅ Audio sauvegardé sous : {filename}")
    
    return filename

def stt_whisper(mp3_filename):
    # Charger le modèle Whisper
    model = whisper.load_model("base")
    
    # Transcrire directement le fichier MP3
    result = model.transcribe(mp3_filename)
    return result['text']



# Enregistrement audio et sauvegarde en MP3
#mp3_file = record_audio(4)
mp3_file="output_tts_online.mp3"

# Transcription de l'audio MP3
text = stt_whisper(mp3_file)
print("Texte reconnu :", text)
    
    