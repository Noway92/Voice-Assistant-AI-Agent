"""
Gestion des webhooks et interactions avec Twilio - VERSION ASYNCHRONE.
"""


import os
import urllib.parse
import threading
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
        Traite l'enregistrement vocal - lance le traitement asynchrone en arrière-plan.
        Retourne immédiatement avec musique d'attente.
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
            
            # Initialiser l'état de l'appel
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            self.phone_main.active_calls[call_sid]['response_ready'] = False
            self.phone_main.active_calls[call_sid]['processing'] = True
            
            # Lancer le traitement asynchrone en arrière-plan (NE PAS ATTENDRE)
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            thread = threading.Thread(
                target=self._process_recording_async,
                args=(recording_url, call_sid, base_url)
            )
            thread.daemon = True
            thread.start()
            
            # Jouer une musique d'attente courte
            response.play(f"{base_url}/static/audio-automatic/waiting.mp3")
            
            # Rediriger vers une page d'attente qui va checker le résultat
            params = urllib.parse.urlencode({'call_sid': call_sid})
            response.redirect(f'/wait-for-response?{params}', method='POST')
            
        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            response.play(f"{base_url}/static/audio-automatic/error.mp3")
            response.hangup()
        
        return str(response)
    
    def _process_recording_async(self, recording_url: str, call_sid: str, base_url: str):
        """
        Traitement VRAIMENT asynchrone en arrière-plan (dans un thread).
        N'est pas appelé par le webhook Twilio directement.
        """
        try:
            print(f"[ASYNC] Début du traitement pour {call_sid}\n\n\n")
            
            # S'assurer que le call_sid existe dans active_calls
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            # Détecter la langue et transcrire
            user_text, detected_lang, should_end_call = self.phone_main.detect_language_and_transcribe(
                recording_url, 
                call_sid
            )
            
            # Si mot de sortie détecté
            if should_end_call:
                print(f"[ASYNC] Fin d'appel demandée par l'utilisateur")
                # Stocker le résultat
                self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/goodbye.mp3"
                self.phone_main.active_calls[call_sid]['should_hangup'] = True
                self.phone_main.active_calls[call_sid]['response_ready'] = True
                self.phone_main.active_calls[call_sid]['processing'] = False
                return
            
            # Si pas de texte (erreur/silence)
            if not user_text:
                print(f"[ASYNC] Pas de texte détecté")
                self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/error.mp3"
                self.phone_main.active_calls[call_sid]['response_ready'] = True
                self.phone_main.active_calls[call_sid]['processing'] = False
                return
            
            # ICI C'EST LA PARTIE QUI PEUT DURER LONGTEMPS (30+ secondes)
            print(f"[ASYNC] Appel à process_and_generate_response (peut prendre du temps)")
            agent_response_text, audio_url = self.phone_main.process_and_generate_response(
                user_text,
                detected_lang,
                call_sid,
                base_url
            )
            print(f"[ASYNC] Réponse reçue: {agent_response_text}")
            
            # Stocker le résultat pour que le webhook puisse le récupérer
            self.phone_main.active_calls[call_sid]['response_audio'] = audio_url
            self.phone_main.active_calls[call_sid]['response_ready'] = True
            self.phone_main.active_calls[call_sid]['processing'] = False
            
        except Exception as e:
            print(f"[ASYNC] Erreur lors du traitement: {e}")
            import traceback
            traceback.print_exc()
            
            # S'assurer que le call_sid existe avant d'écrire
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/error.mp3"
            self.phone_main.active_calls[call_sid]['response_ready'] = True
            self.phone_main.active_calls[call_sid]['processing'] = False
    
    def wait_for_response(self, request: Any) -> str:
        """
        Webhook appelé après la musique d'attente.
        Vérifie si la réponse de l'agent est prête, sinon rejoue de la musique.
        """
        response = VoiceResponse()
        call_sid = request.values.get('call_sid')
        
        try:
            # Récupérer les infos de l'appel
            call_info = self.phone_main.active_calls.get(call_sid, {})
            
            # Vérifier si la réponse est prête
            if call_info.get('response_ready'):
                print(f"[WAIT] Réponse prête pour {call_sid}")
                audio_url = call_info.get('response_audio')
                response.play(audio_url)
                
                # Nettoyer le flag
                call_info['response_ready'] = False
                
                # Vérifier si on doit raccrocher
                if call_info.get('should_hangup'):
                    response.hangup()
                else:
                    # Remettre un enregistrement (boucle)
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
            else:
                # La réponse n'est pas encore prête, rejouer musique d'attente
                print(f"[WAIT] Réponse pas encore prête pour {call_sid}, on attend...")
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                
                # Jouer musique d'attete
                response.play(f"{base_url}/static/audio-automatic/waiting.mp3")
                
                # Rediriger vers soi-même (boucle d'attente)
                params = urllib.parse.urlencode({'call_sid': call_sid})
                response.redirect(f'/wait-for-response?{params}', method='POST')
        
        except Exception as e:
            print(f"Erreur lors de l'attente: {e}")
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
