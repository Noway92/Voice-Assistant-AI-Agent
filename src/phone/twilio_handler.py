"""
Management of webhooks and interactions with Twilio - ASYNCHRONOUS VERSION.
"""


import os
import urllib.parse
import threading
from typing import Dict, Any
from .phone_main import PhoneMain
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client


class TwilioHandler:
    """Manages interactions with the Twilio API."""
    
    def __init__(self):
        """Initialize the Twilio handler with credentials."""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            print("Twilio credentials not configured. Demo mode only.")
        
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
        
        # Welcome message with custom MP3 file
        base_url = os.getenv('BASE_URL', f"http://{request.host}")
        response.play(f"{base_url}/static/audio-automatic/welcome.mp3")
        
        # Record the user's response
        response.record(
            action='/recording',
            method='POST',
            max_length=30,              # Maximum duration
            timeout=3,                   # 3s of silence → end recording
            finish_on_key='#',           # Only # terminates (not 0-9)
            play_beep=True,
            transcribe=False,
            recording_status_callback='/recording-status'
        )
        
        return str(response)
    
    def process_recording(self, request: Any) -> str:
        """
        Process the voice recording - launches asynchronous processing in the background.
        Returns immediately with waiting music.
        """
        response = VoiceResponse()
        
        try:
            # Retrieve the recording URL
            recording_url = request.values.get('RecordingUrl')
            call_sid = request.values.get('CallSid')
            
            if not recording_url:
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                response.play(f"{base_url}/static/audio-automatic/error.mp3")
                response.redirect('/voice')
                return str(response)
            
            # Initialize call state
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            self.phone_main.active_calls[call_sid]['response_ready'] = False
            self.phone_main.active_calls[call_sid]['processing'] = True
            
            # Launch asynchronous processing in the background (DO NOT WAIT)
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            thread = threading.Thread(
                target=self._process_recording_async,
                args=(recording_url, call_sid, base_url)
            )
            thread.daemon = True
            thread.start()
            
            # Play a short waiting music
            response.play(f"{base_url}/static/audio-automatic/waiting.mp3")
            
            # Redirect to a waiting page that will check the result
            params = urllib.parse.urlencode({'call_sid': call_sid})
            response.redirect(f'/wait-for-response?{params}', method='POST')
            
        except Exception as e:
            print(f"Error during processing: {e}")
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            response.play(f"{base_url}/static/audio-automatic/error.mp3")
            response.hangup()
        
        return str(response)
    
    def _process_recording_async(self, recording_url: str, call_sid: str, base_url: str):
        """
        TRULY asynchronous processing in the background (in a thread).
        Not called by the Twilio webhook directly.
        """
        try:
            print(f"[ASYNC] Début du traitement pour {call_sid}\n\n\n")
            
            # Ensure call_sid exists in active_calls
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            # Detect language and transcribe
            user_text, detected_lang, should_end_call = self.phone_main.detect_language_and_transcribe(
                recording_url, 
                call_sid
            )
            
            # If exit word detected
            if should_end_call:
                print(f"[ASYNC] Call termination requested by user")
                # Store the result
                self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/goodbye.mp3"
                self.phone_main.active_calls[call_sid]['should_hangup'] = True
                self.phone_main.active_calls[call_sid]['response_ready'] = True
                self.phone_main.active_calls[call_sid]['processing'] = False
                return
            
            # Si pas de texte (erreur/silence)
            if not user_text:
                print(f"[ASYNC] No text detected")
                self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/error.mp3"
                self.phone_main.active_calls[call_sid]['response_ready'] = True
                self.phone_main.active_calls[call_sid]['processing'] = False
                return
            
            # THIS IS THE PART THAT CAN TAKE A LONG TIME (30+ seconds)
            print(f"[ASYNC] Call to process_and_generate_response (may take time)")
            agent_response_text, audio_url = self.phone_main.process_and_generate_response(
                user_text,
                detected_lang,
                call_sid,
                base_url
            )
            print(f"[ASYNC] Response received: {agent_response_text}")
            
            # Store the result so the webhook can retrieve it
            self.phone_main.active_calls[call_sid]['response_audio'] = audio_url
            self.phone_main.active_calls[call_sid]['response_ready'] = True
            self.phone_main.active_calls[call_sid]['processing'] = False
            
        except Exception as e:
            print(f"[ASYNC] Error during processing: {e}")
            import traceback
            traceback.print_exc()
            
            # Ensure call_sid exists before writing
            if call_sid not in self.phone_main.active_calls:
                self.phone_main.active_calls[call_sid] = {}
            
            self.phone_main.active_calls[call_sid]['response_audio'] = f"{base_url}/static/audio-automatic/error.mp3"
            self.phone_main.active_calls[call_sid]['response_ready'] = True
            self.phone_main.active_calls[call_sid]['processing'] = False
    
    def wait_for_response(self, request: Any) -> str:
        """
        Webhook called after waiting music.
        Checks if the agent's response is ready, otherwise replays music.
        """
        response = VoiceResponse()
        call_sid = request.values.get('call_sid')
        
        try:
            # Retrieve call info
            call_info = self.phone_main.active_calls.get(call_sid, {})
            
            # Check if response is ready
            if call_info.get('response_ready'):
                print(f"[WAIT] Response ready for {call_sid}")
                audio_url = call_info.get('response_audio')
                response.play(audio_url)
                
                # Clean the flag
                call_info['response_ready'] = False
                
                # Check if we should hang up
                if call_info.get('should_hangup'):
                    response.hangup()
                else:
                    # Restart recording (loop)
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
                # Response is not ready yet, replay waiting music
                print(f"[WAIT] Response not ready yet for {call_sid}, waiting...")
                base_url = os.getenv('BASE_URL', f"http://{request.host}")
                
                # Play waiting music
                response.play(f"{base_url}/static/audio-automatic/waiting.mp3")
                
                # Redirect to self (waiting loop)
                params = urllib.parse.urlencode({'call_sid': call_sid})
                response.redirect(f'/wait-for-response?{params}', method='POST')
        
        except Exception as e:
            print(f"Error during waiting: {e}")
            base_url = os.getenv('BASE_URL', f"http://{request.host}")
            response.play(f"{base_url}/static/audio-automatic/error.mp3")
            response.hangup()
        
        return str(response)
    
    # NOT NECESSARILY USEFUL FOR NOW
    def make_outbound_call(self, to_number: str, audio_url: str = None, message: str = None) -> Dict[str, Any]:
        """
        Makes an outbound call (e.g.: reservation confirmation).
        
        Args:
            to_number: Number to call
            audio_url: URL of the MP3 file to play (priority)
            message: Text message (used if audio_url is None, generates an MP3)
            
        Returns:
            Call information
        """
        if not self.client:
            return {"error": "Twilio client not initialized"}
        
        try:
            # If we have an audio_url, use it directly
            if audio_url:
                twiml = f'<Response><Play>{audio_url}</Play></Response>'
            elif message:
                # Otherwise, fallback to Say (or generate an MP3)
                twiml = f'<Response><Say language="fr-FR" voice="Polly.Lea">{message}</Say></Response>'
            else:
                return {"error": "Neither audio_url nor message provided"}
            
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
