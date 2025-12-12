"""
Serveur Flask pour gérer les webhooks Twilio.
"""

from flask import Flask, request, Response, send_from_directory
from src.phone.twilio_handler import TwilioHandler
from src.audio.text_to_speech import TextToSpeech
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
twilio_handler = TwilioHandler()


@app.route('/')
def index():
    """Page d'accueil."""
    return """
    <html>
        <head><title>Assistant Vocal Restaurant</title></head>
        <body>
            <h1>🍽️ Assistant Vocal Restaurant</h1>
            <p>Serveur webhook Twilio actif</p>
            <h2>Endpoints disponibles:</h2>
            <ul>
                <li><code>POST /voice</code> - Appels entrants</li>
                <li><code>POST /recording</code> - Traitement des enregistrements</li>
                <li><code>POST /continue</code> - Continuation de conversation</li>
                <li><code>GET /health</code> - Status du serveur</li>
            </ul>
        </body>
    </html>
    """


@app.route('/voice', methods=['POST'])
def handle_incoming_call():
    """
    Webhook pour gérer les appels entrants.
    Twilio appelle cet endpoint quand quelqu'un appelle votre numéro.
    """
    try:
        twiml_response = twilio_handler.handle_incoming_call(request)
        return Response(twiml_response, mimetype='text/xml')
    except Exception as e:
        print(f"Erreur /voice: {e}")
        return Response(
            '<Response><Say language="fr-FR">Erreur du serveur</Say></Response>',
            mimetype='text/xml'
        )


@app.route('/recording', methods=['POST'])
def handle_recording():
    """
    Webhook pour traiter les enregistrements vocaux.
    Appelé après que l'utilisateur ait enregistré son message.
    """
    try:
        twiml_response = twilio_handler.process_recording(request)
        return Response(twiml_response, mimetype='text/xml')
    except Exception as e:
        print(f"Erreur /recording: {e}")
        return Response(
            '<Response><Say language="fr-FR">Erreur de traitement</Say></Response>',
            mimetype='text/xml'
        )


@app.route('/recording-status', methods=['POST'])
def recording_status():
    """
    Webhook pour le statut des enregistrements (optionnel).
    """
    recording_url = request.values.get('RecordingUrl')
    recording_status = request.values.get('RecordingStatus')
    print(f"Enregistrement: {recording_status} - {recording_url}")
    return Response('', status=200)


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour vérifier que le serveur fonctionne."""
    return {
        "status": "healthy",
        "service": "Voice Assistant AI Agent",
        "twilio_configured": twilio_handler.client is not None
    }


@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Sert les fichiers audio générés."""
    return send_from_directory('static/audio', filename)


def generate_static_audio():
    """Génère les messages audio standards au démarrage."""
    audio_dir = 'static/audio'
    os.makedirs(audio_dir, exist_ok=True)
    
    print("Génération des fichiers audio standards...")
    tts = TextToSpeech(isOffline=False)
    
    messages = {
        'welcome.mp3': 'Bonjour, bienvenue au restaurant. Comment puis-je vous aider?',
        'goodbye.mp3': 'Merci de votre appel. Au revoir!',
        'error.mp3': 'Désolé, une erreur est survenue. Veuillez rappeler plus tard.'
    }
    
    for filename, text in messages.items():
        filepath = os.path.join(audio_dir, filename)
        if not os.path.exists(filepath):
            try:
                tts.speak_online(text, output_path=filepath)
                print(f"Généré: {filename}")
            except Exception as e:
                print(f"Erreur pour {filename}: {e}")
        else:
            print(f"Existe déjà: {filename}")
    
    print("Fichiers audio prêts!\n")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("Serveur Flask démarré")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)
    
    # Générer les fichiers audio standards
    generate_static_audio()
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
