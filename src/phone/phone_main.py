"""
Logique métier pour la gestion des appels.
"""

import os
import uuid
from typing import Dict, Any, Tuple
from .audio_adapter import AudioAdapter
from src.core.orchestrator import Orchestrator
from src.audio.text_to_speech import TextToSpeech
from src.core.traductor import LanguageProcessor


class PhoneMain:
    """Handles business logic for phone calls."""
    
    def __init__(self):
        """Initialise le gestionnaire d'appels."""
        self.audio_adapter = AudioAdapter(isOffline=False) # Utiliser le STT en ligne
        self.orchestrator = Orchestrator(isOffline=False) # Utiliser LLM en ligne
        self.tts = TextToSpeech(isOffline=False,UsePhone=True,use_custom_xtts=False)  # Use online TTS for phone
        self.language_processor = LanguageProcessor()
        self.active_calls: Dict[str, Dict[str, Any]] = {}
    
    def detect_language_and_transcribe(self, recording_url: str, call_sid: str) -> Tuple[str, str, bool]:
        """
        Transcrit, détecte la langue et vérifie les mots de sortie.
        
        Args:
            recording_url: URL de l'enregistrement Twilio
            call_sid: Pour récupérer la langue si déjà détectée
        
        Returns:
            Tuple (user_text, detected_language, should_end_call)
        """
        try:
            # Download and transcribe
            audio_file_path = self.audio_adapter.download_twilio_recording(recording_url)
            
            # Check file size
            file_size = os.path.getsize(audio_file_path)
            if file_size < 1000:  # < 1KB = probablement vide/corrompu
                print(f"Fichier audio trop petit ({file_size} bytes)")
                saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
                return None, saved_lang, False
            
            user_text = self.audio_adapter.transcribe_audio(audio_file_path)
            
            if not user_text:
                saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
                return None, saved_lang, False
            
            # Check if language has already been detected for this call
            saved_lang = self.active_calls.get(call_sid, {}).get('language')
            
            if saved_lang:
                # Reuse the saved language
                print(f"\nUtilisateur ({saved_lang}): {user_text}")
                detected_lang = saved_lang
            else:
                # First time: detect the language
                _, detected_lang = self.language_processor.process_input(user_text)
                print(f"\nUtilisateur ({detected_lang}) [DÉTECTÉ]: {user_text}")
                
                # Sauvegarder pour les prochains messages
                if call_sid not in self.active_calls:
                    self.active_calls[call_sid] = {}
                self.active_calls[call_sid]['language'] = detected_lang
            
            # Check exit words (multilingual)
            exit_words = [
                'exit', 'quit', 'stop', 'bye', 'goodbye', 'good bye',
                'au revoir', 'aurevoir', 'salut', 'ciao', 'tchao',
                'adios', 'adiós', 'hasta luego',
                'auf wiedersehen', 'tschüss', 'tschüß',
                'thank you', 'thanks', 'merci', 'gracias', 'danke'
            ]
            
            user_text_lower = user_text.lower().strip()
            
            # Check if an exit word is present in the sentence
            if any(word in user_text_lower for word in exit_words):
                print(f"Exit word detected: '{user_text}'")
                # Clean up temporary file
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                return user_text, detected_lang, True  # True = fin d'appel
            
            # Nettoyer le fichier temporaire
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            
            return user_text, detected_lang, False  # False = continuer
            
        except Exception as e:
            print(f"Transcription error: {e}")
            saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
            return None, saved_lang, False
    
    def process_and_generate_response(self, user_text: str, detected_lang: str, call_sid: str, host: str) -> Tuple[str, str]:
        """
        Step 2: Process the request and generate the MP3.
        
        Args:
            user_text: Transcribed user text
            detected_lang: Detected language
            call_sid: Call identifier
            host: Server host
            
        Returns:
            Tuple (response_text, audio_file_url)
        """
        try:
            # Translate to English
            english_input, _ = self.language_processor.process_input(user_text)
            print(f"Translated to EN: {english_input}")
            
            # Retrieve history
            conversation_history = self.active_calls.get(call_sid, {}).get('history', [])
            #print(f"Voici l'historique actuel : \n{conversation_history}\n")
            
            # Process via orchestrator (in English)
            english_response = self.orchestrator.process_request(
                user_input=english_input,
                conversation_history=conversation_history
            )
            
            # Translate response to detected language
            agent_response = self.language_processor.process_output(
                english_response, 
                detected_lang
            )
            
            print(f"\nAgent ({detected_lang}): {agent_response}\n")
            
            # Generate MP3 file
            audio_filename = f"response_output_tts_online_phone_{call_sid}_{uuid.uuid4().hex[:8]}.mp3"
            audio_dir = "static/audioGenerated"
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = os.path.join(audio_dir, audio_filename)
            
            # Generate audio
            self.tts.speak(agent_response, output_path=audio_path,language=detected_lang)
            
            # Construct URL
            base_url = os.getenv('BASE_URL', f"http://{host}")
            audio_url = f"{base_url}/static/audio-generated/{audio_filename}"
            
            # Update history
            conversation_history.append({
                "role": "user",
                "content": english_input
            })
            conversation_history.append({
                "role": "assistant",
                "content": english_response
            })
            
            # Update the existing dictionary instead of replacing it
            # This preserves keys like 'response_ready', 'processing', etc.
            if call_sid not in self.active_calls:
                self.active_calls[call_sid] = {}
            
            self.active_calls[call_sid]['history'] = conversation_history
            self.active_calls[call_sid]['last_interaction'] = user_text
            self.active_calls[call_sid]['language'] = detected_lang
            
            return agent_response, audio_url
            
        except Exception as e:
            print(f"Erreur traitement: {e}")
            base_url = os.getenv('BASE_URL', f"http://{host}")
            return "Erreur technique", f"{base_url}/static/audio-automatic/error.mp3"
