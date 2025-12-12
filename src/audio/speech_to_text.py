import whisper
import sounddevice as sd
import numpy as np
import soundfile as sf

class SpeechToText:
    def __init__(self, model_name="base", duration=5, samplerate=16000):
        """Initialize the Speech-to-Text engine."""
        self.model = whisper.load_model(model_name)
        self.duration = duration
        self.samplerate = samplerate
    
    def record_audio(self, filename="static/enregistrement.mp3"):
        """Record audio from microphone."""
        print("Enregistrement...")
        audio = sd.rec(int(self.duration * self.samplerate), 
                      samplerate=self.samplerate, channels=1)
        sd.wait()
        
        audio_int16 = (audio.flatten() * 32767).astype(np.int16)
        sf.write(filename, audio_int16, self.samplerate, format='mp3')
        print(f"Audio sauvegardé sous : {filename}")
        
        return filename
    
    def transcribe(self, audio_file):
        """Transcribe audio file to text."""
        result = self.model.transcribe(audio_file)
        return result['text']
    
    def listen(self):
        """Record audio and return transcribed text."""
        audio_file = self.record_audio()
        text = self.transcribe(audio_file)
        return text