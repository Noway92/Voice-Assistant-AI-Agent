import pyttsx3
import os
from openai import OpenAI
import time
import winsound
import subprocess
import platform


# FONCTIONNE QUE POUR LE TELEPHONE PAS POUR l'ORCHESTRATOR
class TextToSpeech:
    def __init__(self, isOffline=True,UsePhone=True, rate=170, voice="echo"):
        """Initialize the Text-to-Speech engine."""
        self.use_offline = isOffline
        self.use_phone = UsePhone
        self.rate = rate
        self.voice = voice
        
        if isOffline:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 170)
        else:
            self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))
        
    def speak_offline(self, text):
        """Use pyttsx3 for offline TTS."""
        print(f"[TTS Offline] Speaking: {text}\n\n")
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
        time.sleep(0.5)
    
    def speak_online_computer(self, text):
        """Use OpenAI API to speak directly on computer."""
        print(f"[TTS Online Computer] {self.voice} Speaking: {text}\n\n")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        output_path="static/audioListened/output_tts.mp3"
        # Sauvegarder le fichier audio
        with open(output_path, "wb") as f:
            f.write(response.read())
        
        abs_path = os.path.abspath(output_path)
        # Lire le fichier selon l'OS
        try:
            # Lire le fichier avec ffplay et attendre la fin
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", abs_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except Exception as e:
            print(f"Erreur lors de la lecture audio: {e}")
    
    def speak_online_phone(self, text, output_path="output_tts_online.mp3"):
        """Use OpenAI API for online TTS."""
        print(f"[TTS Online Phone] {self.voice} Speaking: {text}\n\n")
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
        # Create a mp3 file for phone call
        if self.use_phone :
            self.speak_online_phone(text,output_path)
        # Read directly for computer use
        else:
            #self.speak_offline(text)
            # Pour l'instant non fonctionnel donc on garde que le offline
            if self.use_offline :
                self.speak_offline(text)
            else :
               self.speak_online_computer(text)
            
        