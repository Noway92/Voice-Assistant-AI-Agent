import pyttsx3
import os
from openai import OpenAI

class TextToSpeech:
    def __init__(self, isOffline=True, rate=170, voice="echo"):
        """Initialize the Text-to-Speech engine."""
        self.use_online = isOffline
        self.rate = rate
        self.voice = voice
        
        if isOffline:
            self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))
        else:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", rate)
    
    def speak_offline(self, text):
        """Use pyttsx3 for offline TTS."""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def speak_online(self, text, output_path="output_tts_online.mp3"):
        """Use OpenAI API for online TTS."""
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        
        audio_bytes = response.read()
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio sauvegardé dans : {output_path}")
    
    def speak(self, text):
        """Speak the text using the configured method."""
        if self.use_online:
            self.speak_online(text)
        else:
            self.speak_offline(text)