import pyttsx3

import os
from openai import OpenAI

def tts_offline(text):
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)
    engine.say(text)
    engine.runAndWait()

def tts_online(input_text: str, output_path: str = "output_tts_online.mp3", client: OpenAI = None):
    if client is None:
        client = OpenAI(api_key=os.environ["API_KEY_OPENAI"])
    
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=input_text
    )
    
    # Récupération des bytes audio
    audio_bytes = response.read()

    # Sauvegarde directe dans le fichier
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    
    print(f"Audio sauvegardé dans : {output_path}")
  

#tts_offline("Bonjour, je suis votre assistant vocal.")
tts_online("Bonjour, je suis votre assistant vocal.")
