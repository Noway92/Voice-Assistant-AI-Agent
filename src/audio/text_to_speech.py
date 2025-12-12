import pyttsx3
import os
from openai import OpenAI
import time


# FONCTIONNE QUE POUR LE TELEPHONE PAS POUR l'ORCHESTRATOR
class TextToSpeech:
    def __init__(self, isOffline=True, rate=170, voice="echo"):
        """Initialize the Text-to-Speech engine."""
        self.use_offline = isOffline
        self.rate = rate
        self.voice = voice
        
        """ if isOffline:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 170)
        else:"""
        self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))
        
    
    
    def speak_offline(self, text):
        """Use pyttsx3 for offline TTS."""
        print(f"[TTS Offline] Speaking: {text}")
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
        time.sleep(0.5) # Pour que speak offline lise tout le temps
    
    #NON FONCTIONNEL ( ACTUELLEMENT CREE UN FICHIER .mp3 mais ne lis pas le texte)
    def speak_online(self, text, output_path="output_tts_online.mp3"):
        """Use OpenAI API for online TTS."""
        print(f"{self.voice} Speaking: {text}")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        
        audio_bytes = response.read()
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio sauvegardé dans : {output_path}")
    
    def speak(self, text,output_path="output_tts_online.mp3"):
        """Speak the text using the configured method."""
        """if self.use_offline:
            self.speak_offline(text)
        else:
            self.speak_online(text)"""
        # ON UTILISE QUE OFFLINE POUR L'INSTANT CAR ONLINE MAUVAIS
        self.speak_online(text,output_path)