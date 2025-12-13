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
            <h2>Endpoints Twilio:</h2>
            <ul>
                <li><code>POST /voice</code> - Appels entrants</li>
                <li><code>POST /recording</code> - Traitement des enregistrements (réponse immédiate)</li>
                <li><code>POST /process-async</code> - Traitement asynchrone (peut prendre du temps)</li>
                <li><code>POST /recording-status</code> - Status enregistrement</li>
            </ul>
            <h2>Endpoints Système:</h2>
            <ul>
                <li><code>GET /health</code> - Status du serveur</li>
                <li><code>GET /static/audioAutomatic/&lt;filename&gt;</code> - Fichiers audio automatiques</li>
                <li><code>GET /static/audio_generated/&lt;filename&gt;</code> - Fichiers audio générés</li>
            </ul>
            <h2>Endpoints Debug:</h2>
            <ul>
                <li><code>GET /debug/active-calls</code> - Voir les appels actifs</li>
                <li><code>GET /debug/call/&lt;call_sid&gt;</code> - Détails d'un appel</li>
                <li><code>POST /debug/clear-calls</code> - Nettoyer la mémoire</li>
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
    Retourne immédiatement avec musique d'attente.
    """
    try:
        twiml_response = twilio_handler.process_recording(request)
        return Response(twiml_response, mimetype='text/xml')
    except Exception as e:
        print(f"Erreur /recording: {e}")
        return Response(
            '<Response><Say language="fr-FR">Erreur du serveur</Say></Response>',
            mimetype='text/xml'
        )


@app.route('/process-async', methods=['POST'])
def process_async():
    """
    Route de traitement asynchrone (peut prendre du temps).
    Appelée après la musique d'attente.
    """
    try:
        recording_url = request.values.get('recording_url')
        call_sid = request.values.get('call_sid')
        
        twiml_response = twilio_handler.process_async_recording(
            recording_url, 
            call_sid,
            request
        )
        return Response(twiml_response, mimetype='text/xml')
    except Exception as e:
        print(f"Erreur /process-async: {e}")
        base_url = os.getenv('BASE_URL', f"http://{request.host}")
        return Response(
            f'<Response><Play>{base_url}/static/audioAutomatic/error.mp3</Play><Hangup/></Response>',
            mimetype='text/xml'
        )
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


# Endpoint for Debug
@app.route('/debug/active-calls', methods=['GET'])
def get_active_calls():
    """Récupère tous les appels actifs en mémoire."""
    return {
        "active_calls": twilio_handler.phone_orchestrator.active_calls,
        "count": len(twilio_handler.phone_orchestrator.active_calls)
    }


@app.route('/debug/call/<call_sid>', methods=['GET'])
def get_call_details(call_sid):
    """Récupère les détails d'un appel spécifique."""
    call_info = twilio_handler.phone_orchestrator.active_calls.get(call_sid)
    
    if call_info:
        return {
            "call_sid": call_sid,
            "language": call_info.get('language'),
            "last_interaction": call_info.get('last_interaction'),
            "history": call_info.get('history', []),
            "history_count": len(call_info.get('history', []))
        }
    else:
        return {
            "error": "Call not found",
            "call_sid": call_sid
        }, 404


@app.route('/debug/clear-calls', methods=['POST'])
def clear_all_calls():
    """Nettoie tous les appels actifs (utile pour tests)."""
    count = len(twilio_handler.phone_orchestrator.active_calls)
    twilio_handler.phone_orchestrator.active_calls.clear()
    
    return {
        "message": f"Cleared {count} active calls",
        "cleared_count": count
    }


@app.route('/static/audio-automatic/<filename>')
def serve_audio_automatic(filename):
    """Sert les fichiers audio automatiques (welcome, goodbye, error)."""
    return send_from_directory('static/audioAutomatic', filename)


@app.route('/static/audio-generated/<filename>')
def serve_audio_generated(filename):
    """Sert les fichiers audio générés dynamiquement (réponses)."""
    return send_from_directory('static/audioGenerated', filename)


def generate_static_audio():
    """Génère les messages audio standards au démarrage."""
    audio_dir = 'static/audioAutomatic'
    generated_dir = 'static/audioGenerated'
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(generated_dir, exist_ok=True)
    
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
    # Générer les fichiers audio standards
    generate_static_audio()

    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 60)
    print("Serveur Flask démarré")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
