import pyttsx3
import os
from openai import OpenAI
import time
import subprocess
import torch
import torchaudio

#from TTS.tts.configs.xtts_config import XttsConfig
#from TTS.tts.models.xtts import Xtts
import sounddevice as sd
import soundfile as sf

# FONCTIONNE QUE POUR LE TELEPHONE PAS POUR l'ORCHESTRATOR
class TextToSpeech:
    def __init__(self, isOffline=False,UsePhone=True, use_custom_xtts=False, rate=170, voice="echo"):
        """Initialize the Text-to-Speech engine."""
        self.use_offline = isOffline
        self.use_phone = UsePhone
        self.use_custom_xtts = use_custom_xtts
        self.rate = rate
        self.voice = voice
        
        if use_custom_xtts:
            print("[XTTS] Loading custom voice model...")
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                self.xtts_model_path = os.path.join(script_dir, "tts", "best_model.pth")
                self.xtts_config_path = os.path.join(script_dir, "tts", "config.json")
                self.xtts_reference_wav = os.path.join(script_dir, "tts", "reference.wav")
                
                # Load config and model
                #self.xtts_config = XttsConfig()
                self.xtts_config.load_json(self.xtts_config_path)
                #self.xtts_model = Xtts.init_from_config(self.xtts_config)
                
                # Get the directory containing the model files
                checkpoint_dir = os.path.dirname(self.xtts_model_path)
                
                # Check for required vocab files
                vocab_path = os.path.join(checkpoint_dir, "vocab.json")
                if not os.path.exists(vocab_path):
                    raise FileNotFoundError(f"Missing vocab.json in {checkpoint_dir}. XTTS requires vocab.json and model files in the same directory.")
                
                self.xtts_model.load_checkpoint(
                    self.xtts_config, 
                    checkpoint_dir=checkpoint_dir,
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
            except Exception as e:
                print(f"[XTTS] Failed to load custom model: {str(e)}")
                print("[XTTS] Falling back to offline TTS (pyttsx3)")
                self.use_custom_xtts = False  # Disable custom XTTS on failure
        else:
            if isOffline:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", 170)
            else:
                self.client = OpenAI(api_key=os.environ.get("API_KEY_OPENAI"))
        
    def speak_offline(self, text):
        """Use pyttsx3 for offline TTS."""
        print(f"[TTS Offline] Speaking ...")
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.say(text)
        engine.runAndWait()
        time.sleep(0.5)
    
    def speak_custom_xtts(self, text, language='en', output_path="static/audioGenerated/output_xtts.wav"):
        """Use custom trained XTTS model for TTS with optimal parameters."""
        print(f"[Custom XTTS] Speaking in {language} ...")
        
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
    
    def speak_online_computer(self, text, output_path="static/audioGenerated/output_tts_online_computer.mp3"):
        """Use OpenAI API to speak directly on computer."""
        print(f"[TTS Online Computer] {self.voice} Speaking ...")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        
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
    
    def speak_online_phone(self, text, output_path="static/audioGenerated/output_tts_online_phone.mp3"):
        """Use OpenAI API for online TTS."""
        print(f"[TTS Online Phone] {self.voice} Speaking ...")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        
        audio_bytes = response.read()
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"Audio sauvegardé dans : {output_path}")
    
    def speak(self, text, output_path="output_tts_online.mp3", language='en'):
        """Speak the text using the configured method."""
        # Create a mp3 file for phone call
        if self.use_phone :
            self.speak_online_phone(text,output_path)
        else:
            if self.use_custom_xtts:
                self.speak_custom_xtts(text, language=language)
            else :
                # Read directly for computer use
                if self.use_offline :
                    self.speak_offline(text)
                else :
                    self.speak_online_computer(text)
            
        