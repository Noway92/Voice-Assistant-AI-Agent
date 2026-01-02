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
    """Gère la logique métier des appels téléphoniques."""
    
    def __init__(self):
        """Initialise le gestionnaire d'appels."""
        self.audio_adapter = AudioAdapter(isOffline=False) # Utiliser le STT en ligne
        self.orchestrator = Orchestrator(isOffline=False) # Utiliser LLM en ligne
        self.tts = TextToSpeech(isOffline=False,UsePhone=True,use_custom_xtts=False)  # Utiliser le TTS en ligne pour téléphone
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
            # Télécharger et transcrire
            audio_file_path = self.audio_adapter.download_twilio_recording(recording_url)
            
            # Vérifier la taille du fichier
            file_size = os.path.getsize(audio_file_path)
            if file_size < 1000:  # < 1KB = probablement vide/corrompu
                print(f"Fichier audio trop petit ({file_size} bytes)")
                saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
                return None, saved_lang, False
            
            user_text = self.audio_adapter.transcribe_audio(audio_file_path)
            
            if not user_text:
                saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
                return None, saved_lang, False
            
            # Vérifier si la langue a déjà été détectée pour cet appel
            saved_lang = self.active_calls.get(call_sid, {}).get('language')
            
            if saved_lang:
                # Réutiliser la langue sauvegardée
                print(f"\n\nUtilisateur ({saved_lang}): {user_text}")
                detected_lang = saved_lang
            else:
                # Première fois : détecter la langue
                _, detected_lang = self.language_processor.process_input(user_text)
                print(f"\n\nUtilisateur ({detected_lang}) [DÉTECTÉ]: {user_text}")
                
                # Sauvegarder pour les prochains messages
                if call_sid not in self.active_calls:
                    self.active_calls[call_sid] = {}
                self.active_calls[call_sid]['language'] = detected_lang
            
            # Vérifier les mots de sortie (multilingue)
            exit_words = [
                'exit', 'quit', 'stop', 'bye', 'goodbye', 'good bye',
                'au revoir', 'aurevoir', 'salut', 'ciao', 'tchao',
                'adios', 'adiós', 'hasta luego',
                'auf wiedersehen', 'tschüss', 'tschüß',
                'thank you', 'thanks', 'merci', 'gracias', 'danke'
            ]
            
            user_text_lower = user_text.lower().strip()
            
            # Vérifier si un mot de sortie est présent dans la phrase
            if any(word in user_text_lower for word in exit_words):
                print(f"Mot de sortie détecté: '{user_text}'")
                # Nettoyer le fichier temporaire
                if os.path.exists(audio_file_path):
                    os.remove(audio_file_path)
                return user_text, detected_lang, True  # True = fin d'appel
            
            # Nettoyer le fichier temporaire
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            
            return user_text, detected_lang, False  # False = continuer
            
        except Exception as e:
            print(f"Erreur transcription: {e}")
            saved_lang = self.active_calls.get(call_sid, {}).get('language', 'en')
            return None, saved_lang, False
    
    def process_and_generate_response(self, user_text: str, detected_lang: str, call_sid: str, host: str) -> Tuple[str, str]:
        """
        Étape 2: Traite la demande et génère le MP3.
        
        Args:
            user_text: Texte transcrit de l'utilisateur
            detected_lang: Langue détectée
            call_sid: Identifiant de l'appel
            host: Host du serveur
            
        Returns:
            Tuple (texte_réponse, url_fichier_audio)
        """
        try:
            # Traduire en anglais
            english_input, _ = self.language_processor.process_input(user_text)
            print(f"Traduit EN: {english_input}")
            
            # Récupérer l'historique
            conversation_history = self.active_calls.get(call_sid, {}).get('history', [])
            #print(f"Voici l'historique actuel : \n{conversation_history}\n")
            
            # Traiter via l'orchestrateur (en anglais)
            english_response = self.orchestrator.process_request(
                user_input=english_input,
                conversation_history=conversation_history
            )
            
            # Traduire la réponse dans la langue détectée
            agent_response = self.language_processor.process_output(
                english_response, 
                detected_lang
            )
            
            print(f"Agent ({detected_lang}): {agent_response}")
            
            # Générer le fichier MP3
            audio_filename = f"response_{call_sid}_{uuid.uuid4().hex[:8]}.mp3"
            audio_dir = "static/audioGenerated"
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = os.path.join(audio_dir, audio_filename)
            
            # Générer l'audio
            self.tts.speak(agent_response, output_path=audio_path,language=detected_lang)
            
            # Construire l'URL
            base_url = os.getenv('BASE_URL', f"http://{host}")
            audio_url = f"{base_url}/static/audio-generated/{audio_filename}"
            
            # Mettre à jour l'historique
            conversation_history.append({
                "role": "user",
                "content": english_input
            })
            conversation_history.append({
                "role": "assistant",
                "content": english_response
            })
            
            # Mettre à jour le dictionnaire existant au lieu de le remplacer
            # Cela préserve les clés comme 'response_ready', 'processing', etc.
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
