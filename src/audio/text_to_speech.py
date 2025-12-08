import pyttsx3
import os
from openai import OpenAI
import time
import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import sounddevice as sd
import soundfile as sf

class TextToSpeech:
    def __init__(self, isOffline=True, rate=170, voice="echo", use_custom_xtts=False):
        """Initialize the Text-to-Speech engine."""
        self.use_offline = isOffline
        self.rate = rate
        self.voice = voice
        self.use_custom_xtts = use_custom_xtts
        
        # Initialize custom XTTS model if requested
        if use_custom_xtts:
            print("[XTTS] Loading custom voice model...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.xtts_model_path = os.path.join(script_dir, "tts", "best_model.pth")
            self.xtts_config_path = os.path.join(script_dir, "tts", "config.json")
            self.xtts_reference_wav = os.path.join(script_dir, "tts", "reference.wav")
            
            # Load config and model
            self.xtts_config = XttsConfig()
            self.xtts_config.load_json(self.xtts_config_path)
            self.xtts_model = Xtts.init_from_config(self.xtts_config)
            self.xtts_model.load_checkpoint(
                self.xtts_config, 
                checkpoint_path=self.xtts_model_path,
                use_deepspeed=False
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.xtts_model.cuda()
                print("[XTTS] Model loaded on GPU")
            else:
                print("[XTTS] Model loaded on CPU")
            
            print("[XTTS] Custom voice model ready!")
        
        # ON UTILISE QUE OFFLINE POUR L'INSTANT CAR ONLINE MAUVAIS
        # MAIS ON INITIALISE A CHAQUE FOIS CAR pyttsx3 bug
        """if isOffline:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 170)
        else:
            self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))"""
        # ON UTILISE QUE OFFLINE POUR L'INSTANT CAR ONLINE MAUVAIS
    
    
    def speak_offline(self, text):
        """Use pyttsx3 for offline TTS."""
        print(f"[TTS Offline] Speaking: {text}")
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
        time.sleep(0.5) # Pour que speak offline lise tout le temps
    
    def speak_custom_xtts(self, text, language='en', output_path="output_xtts.wav"):
        """Use custom trained XTTS model for TTS with optimal parameters."""
        print(f"[Custom XTTS] Speaking in {language}: {text}")
        
        try:
            # Clear GPU cache before generation (important for 6GB VRAM)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Compute speaker latents from reference audio
            gpt_cond_latent, speaker_embedding = self.xtts_model.get_conditioning_latents(
                audio_path=[self.xtts_reference_wav]
            )
            
            # Generate speech with optimal parameters from deployment guide
            # (Moderate settings: balanced quality and stability)
            out = self.xtts_model.inference(
                text=text,
                language=language,  # Dynamic language from detection
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                temperature=0.6,           # Moderate (recommended)
                repetition_penalty=15.0,   # Moderate (recommended)
                top_k=15,                  # Moderate (recommended)
                top_p=0.725,               # Moderate (recommended)
                length_penalty=2.0,
            )
            
            # Save audio
            import torchaudio
            torchaudio.save(output_path, torch.tensor(out["wav"]).unsqueeze(0), 24000)
            
            # Play the audio directly (no file needed, plays immediately)
            data, samplerate = sf.read(output_path)
            sd.play(data, samplerate)
            sd.wait()
            
            print(f"[Custom XTTS] Audio generated successfully (GPU: {torch.cuda.is_available()})")
            
        except Exception as e:
            print(f"[Custom XTTS] Error: {str(e)}")
            print("[Custom XTTS] Falling back to offline TTS")
            self.speak_offline(text)
    
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
    
    def speak(self, text, language='en'):
        """Speak the text using the configured method."""
        if self.use_custom_xtts:
            self.speak_custom_xtts(text, language=language)
        else:
            self.speak_offline(text)
        
        """if self.use_offline:
            self.speak_offline(text)
        else:
            self.speak_online(text)"""
        # ON UTILISE QUE OFFLINE POUR L'INSTANT CAR ONLINE MAUVAIS
        # self.speak_offline(text)