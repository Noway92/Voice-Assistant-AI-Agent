import whisper
import os
import sounddevice as sd
import numpy as np
import soundfile as sf
from openai import OpenAI
import threading

class SpeechToText:
    def __init__(self,isOffline=True, model_name="base", duration=5, samplerate=16000):
        """Initialize the Speech-to-Text engine."""
        self.duration = duration
        self.samplerate = samplerate
        self.isOffline = isOffline
        
        if isOffline:
            self.model = whisper.load_model(model_name)
        else:
            self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))
    
    def record_audio(self, filename="static/audioListened/enregistrement.mp3"):
        """Record audio from microphone until Enter is pressed."""
        print("Enregistrement en cours... Appuyez sur Entrée pour arrêter.")
        
        audio_chunks = []
        stop_recording = threading.Event()
        
        def record():
            """Thread d'enregistrement continu."""
            chunk_duration = 0.5  # chunks de 500ms
            chunk_samples = int(chunk_duration * self.samplerate)
            
            while not stop_recording.is_set():
                chunk = sd.rec(chunk_samples, 
                            samplerate=self.samplerate, 
                            channels=1, 
                            blocking=False)
                sd.wait()
                audio_chunks.append(chunk)
        
        # Démarrer l'enregistrement
        record_thread = threading.Thread(target=record, daemon=True)
        record_thread.start()
        
        # Attendre Entrée
        input()
        stop_recording.set()
        record_thread.join()
                
        # Fusionner et sauvegarder
        if audio_chunks:
            audio = np.vstack(audio_chunks)
            audio_int16 = (audio.flatten() * 32767).astype(np.int16)
            sf.write(filename, audio_int16, self.samplerate, format='mp3')
            print(f"Audio sauvegardé sous : {filename}")

            return filename

    
    def transcribe_offline(self, audio_file):
        """Offline : Transcribe audio file to text."""
        print("[STT Offline]\n")
        result = self.model.transcribe(audio_file)
        return result['text']
    
    def transcribe_online(self, audio_file):
        """Online : Transcribe audio file to text."""
        print("[STT Online]\n")
        with open(audio_file, "rb") as f:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text
    
    def listen(self):
        """Record audio and return transcribed text."""
        audio_file = self.record_audio()
        if self.isOffline :
            text = self.transcribe_offline(audio_file)
        else : 
            text = self.transcribe_online(audio_file)
        return text