"""
Adaptateur pour convertir les formats audio entre Twilio et les modules audio locaux.
"""

import os
import requests
import tempfile
from typing import Optional
from src.audio.speech_to_text import SpeechToText


class AudioAdapter:
    """Adapte les formats audio entre Twilio et le système local."""
    
    def __init__(self,isOffline=False):
        """Initialise l'adaptateur audio."""
        self.temp_dir = tempfile.gettempdir()
        self.isOffline = isOffline
        self.stt = SpeechToText(isOffline)  
        
    
    def download_twilio_recording(self, recording_url: str) -> str:
        """
        Télécharge un enregistrement depuis Twilio.
        
        Args:
            recording_url: URL de l'enregistrement Twilio (format: .wav)
            
        Returns:
            Chemin local du fichier téléchargé
        """
        try:
            # Ajouter l'extension .wav si nécessaire
            if not recording_url.endswith('.wav'):
                recording_url += '.wav'
            
            #Utiliser l'authent de twillio pour récup les infos
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            # Télécharger le fichier
            response = requests.get(
                recording_url, 
                auth=(account_sid, auth_token),  # ← FIX ICI
                timeout=30
            )
            
            # Sauvegarder temporairement
            temp_file = os.path.join(self.temp_dir, f"twilio_recording_{os.urandom(8).hex()}.wav")
            
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            print(f"Enregistrement téléchargé: {temp_file}")
            return temp_file
            
        except Exception as e:
            print(f"Erreur lors du téléchargement: {e}")
            raise
    
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcrit un fichier audio en texte.
        
        Args:
            audio_file_path: Chemin du fichier audio
            
        Returns:
            Texte transcrit ou None en cas d'erreur
        """
        try:
            if self.isOffline :
                transcription = self.stt.transcribe_offline(audio_file_path)
            else:
                transcription = self.stt.transcribe_online(audio_file_path)
            
            if transcription and transcription.strip():
                return transcription.strip()
            
            print("Transcription vide")
            return None
            
        except Exception as e:
            print(f"Erreur lors de la transcription: {e}")
            return None
    
    def convert_to_twilio_format(self, audio_file_path: str) -> str:
        """
        Convertit un fichier audio au format compatible Twilio (μ-law, 8kHz).
        
        Args:
            audio_file_path: Chemin du fichier audio source
            
        Returns:
            Chemin du fichier converti
        """
        # Pour l'instant, Twilio accepte plusieurs formats
        # On peut implémenter une conversion avec pydub si nécessaire
        return audio_file_path
    
    def cleanup_temp_files(self, file_path: str):
        """
        Nettoie les fichiers temporaires.
        
        Args:
            file_path: Chemin du fichier à supprimer
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Fichier temporaire supprimé: {file_path}")
        except Exception as e:
            print(f"Impossible de supprimer {file_path}: {e}")
