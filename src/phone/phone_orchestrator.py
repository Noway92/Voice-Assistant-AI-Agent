"""
Logique métier pour la gestion des appels.
"""

import os
import uuid
from typing import Dict, Any, Tuple
from .audio_adapter import AudioAdapter
from src.core.orchestrator import Orchestrator
from src.audio.text_to_speech import TextToSpeech


class PhoneOrchestrator:
    """Gère la logique métier des appels téléphoniques."""
    
    def __init__(self):
        """Initialise le gestionnaire d'appels."""
        self.audio_adapter = AudioAdapter()
        self.orchestrator = Orchestrator()
        self.tts = TextToSpeech(isOffline=False)  # Utiliser le TTS en ligne
        self.active_calls: Dict[str, Dict[str, Any]] = {}
    
    def process_user_input_with_audio(self, recording_url: str, call_sid: str, host: str) -> Tuple[str, str]:
        """
        Traite l'entrée vocale de l'utilisateur et génère un fichier MP3 de réponse.
        
        Args:
            recording_url: URL de l'enregistrement audio
            call_sid: Identifiant unique de l'appel
            host: Host du serveur pour construire l'URL
            
        Returns:
            Tuple (texte_réponse, url_fichier_audio)
        """
        try:
            # Télécharger et convertir l'audio Twilio
            audio_file_path = self.audio_adapter.download_twilio_recording(recording_url)
            
            # Transcrire l'audio en texte
            user_text = self.audio_adapter.transcribe_audio(audio_file_path)
            
            if not user_text:
                base_url = os.getenv('BASE_URL', f"http://{host}")
                return "Erreur de transcription", f"{base_url}/static/audio/error.mp3"
            
            print(f"Utilisateur (Call {call_sid}): {user_text}")
            
            # Récupérer l'historique de l'appel si existant
            conversation_history = self.active_calls.get(call_sid, {}).get('history', [])
            
            # Traiter via l'orchestrateur
            agent_response = self.orchestrator.process_request(
                user_input=user_text,
                conversation_history=conversation_history
            )
            
            print(f"Agent: {agent_response}")
            
            # Générer le fichier MP3 de la réponse
            audio_filename = f"response_{call_sid}_{uuid.uuid4().hex[:8]}.mp3"
            audio_dir = "static/audio"
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = os.path.join(audio_dir, audio_filename)
            
            # Générer l'audio avec le système TTS
            self.tts.speak(agent_response, output_path=audio_path)
            
            # Construire l'URL publique du fichier
            base_url = os.getenv('BASE_URL', f"http://{host}")
            audio_url = f"{base_url}/static/audio/{audio_filename}"
            
            # Mettre à jour l'historique
            conversation_history.append({
                "role": "user",
                "content": user_text
            })
            conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })
            
            self.active_calls[call_sid] = {
                "history": conversation_history,
                "last_interaction": user_text
            }
            
            # Nettoyer le fichier audio temporaire
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            
            return agent_response, audio_url
            
        except Exception as e:
            print(f"Erreur lors du traitement de l'appel: {e}")
            base_url = os.getenv('BASE_URL', f"http://{host}")
            return "Erreur technique", f"{base_url}/static/audio/error.mp3"
    
    # Fonction utile en Production, PAS UTILISE 
    def end_call(self, call_sid: str):
        """
        Termine un appel et nettoie les données associées.
        
        Args:
            call_sid: Identifiant de l'appel
        """
        if call_sid in self.active_calls:
            print(f"Fin de l'appel {call_sid}")
            del self.active_calls[call_sid]

    # Fonction utile en Production, PAS UTILISE
    def get_call_history(self, call_sid: str) -> list:
        """
        Récupère l'historique d'un appel.
        
        Args:
            call_sid: Identifiant de l'appel
            
        Returns:
            Liste des messages de la conversation
        """
        return self.active_calls.get(call_sid, {}).get('history', [])
