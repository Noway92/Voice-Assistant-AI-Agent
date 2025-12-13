"""
Gestion des webhooks et interactions avec Twilio.
"""


import os
import urllib.parse
from typing import Dict, Any
from .phone_main import PhoneMain
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client


class TwilioHandler:
    """Gère les interactions avec l'API Twilio."""
    
    def __init__(self):
        """Initialise le handler Twilio avec les credentials."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Credentials Twilio non configurées. Mode démo uniquement.")
        
        self.phone_main = PhoneMain()
    
    def handle_incoming_call(self, request: Any) -> str:
        """
        Gère un appel entrant de Twilio.
        
        Args:
            request: L'objet request Flask/FastAPI contenant les données Twilio
            
        Returns:
            XML TwiML response
        """
        response = VoiceResponse()
        
        # Message de bienvenue avec fichier MP3 personnalisé
        base_url = os.getenv('BASE_URL', f"http://{request.host}")
        response.play(f"{base_url}/static/audio-automatic/welcome.mp3")
        
        # Enregistrer la réponse de l'utilisateur
        response.record(
            action='/recording',
            method='POST',
            max_length=30,              # Durée maximale
            timeout=3,                   # 3s de silence → fin d'enregistrement
            finish_on_key='#',           # Seulement # termine (pas 0-9)
            play_beep=True,
            transcribe=False,
            recording_status_callback='/recording-status'
        )
        
        return str(response)
    
    def process_recording(self, request: Any) -> str:
        """
        Traite l'enregistrement vocal - retourne immédiatement avec musique d'attente.
        """
        response = VoiceResponse()
        
        try:
            # Récupérer l'URL de l'enregistrement
            recording_url = request.values.get('RecordingUrl')
            call_sid = request.values.get('CallSid')
            
            if not recording_url:
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                response.play(f"{base_url}/static/audio-automatic/error.mp3")
                response.redirect('/voice')
                return str(response)
            
            saved_lang = self.phone_main.active_calls.get(call_sid, {}).get('language')
        
            # Messages d'attente multilingues
            waiting_messages = {
                'fr': ("Un instant s'il vous plaît", 'fr-FR', 'Polly.Lea'),
                'en': ("One moment please", 'en-US', 'Polly.Joanna'),
                'es': ("Un momento por favor", 'es-ES', 'Polly.Lucia'),
                'de': ("Einen Moment bitte", 'de-DE', 'Polly.Vicki')
            }
            
            # Utiliser la langue sauvegardée ou défaut anglais
            message, lang_code, voice = waiting_messages.get(saved_lang or 'fr', waiting_messages['fr'])
            
            # Dire le message d'attente dans la bonne langue
            response.say(message, language=lang_code, voice=voice)
            # Rediriger vers le traitement asynchrone (passe les paramètres en query)
            
            params = urllib.parse.urlencode({
                'recording_url': recording_url,
                'call_sid': call_sid
            })
            response.redirect(f'/process-async?{params}', method='POST')
            
        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            response.play(f"{base_url}/static/audio-automatic/error.mp3")
            response.hangup()
        
        return str(response)
    
    def process_async_recording(self, recording_url: str, call_sid: str, request: Any) -> str:
        """
        Traitement asynchrone (peut prendre du temps sans timeout Twilio).
        """
        response = VoiceResponse()
        
        try:
            # Détecter la langue, transcrire et vérifier sortie
            user_text, detected_lang, should_end_call = self.phone_main.detect_language_and_transcribe(
                recording_url, 
                call_sid
            )
            
            # Si mot de sortie détecté
            if should_end_call:
                print(f"Fin d'appel demandée par l'utilisateur")
                self.phone_main.end_call(call_sid)
                
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                response.play(f"{base_url}/static/audio-automatic/goodbye.mp3")
                response.hangup()
                return str(response)
            
            # Si pas de texte (erreur/silence)
            if not user_text:
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                response.play(f"{base_url}/static/audio-automatic/error.mp3")
            
            if user_text:   
    
                agent_response_text, audio_url = self.phone_main.process_and_generate_response(
                    user_text,
                    detected_lang,
                    call_sid,
                    request.host
                )
                
                # Répondre à l'utilisateur avec le fichier MP3 généré
                response.play(audio_url)
            
            # Remettre automatiquement un enregistrement (boucle)
            response.record(
                action='/recording',
                method='POST',
                max_length=30,
                timeout=3,  
                finish_on_key='#',
                play_beep=False,
                transcribe=False,
                recording_status_callback='/recording-status'
            )
            
        except Exception as e:
            print(f"Erreur lors du traitement async: {e}")
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            response.play(f"{base_url}/static/audio-automatic/error.mp3")
            response.hangup()
        
        return str(response)
    
    # PAS FORCEMENT UTILE POUR l'INSTANT
    def make_outbound_call(self, to_number: str, audio_url: str = None, message: str = None) -> Dict[str, Any]:
        """
        Effectue un appel sortant (ex: confirmation de réservation).
        
        Args:
            to_number: Numéro à appeler
            audio_url: URL du fichier MP3 à lire (prioritaire)
            message: Message texte (utilisé si audio_url est None, génère un MP3)
            
        Returns:
            Informations sur l'appel
        """
        if not self.client:
            return {"error": "Client Twilio non initialisé"}
        
        try:
            # Si on a un audio_url, l'utiliser directement
            if audio_url:
                twiml = f'<Response><Play>{audio_url}</Play></Response>'
            elif message:
                # Sinon, fallback sur Say (ou générer un MP3)
                twiml = f'<Response><Say language="fr-FR" voice="Polly.Lea">{message}</Say></Response>'
            else:
                return {"error": "Ni audio_url ni message fourni"}
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                twiml=twiml
            )
            return {
                "success": True,
                "call_sid": call.sid,
                "status": call.status
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
