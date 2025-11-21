import sys
import time
from pathlib import Path
from typing import List, Dict

# Ajouter le dossier src au path
sys.path.append(str(Path(__file__).parent / "src"))

# MAJ de ces fichiers pour créer des classes
from audio.speech_to_text import SpeechToText
from audio.text_to_speech import TextToSpeech
from core.traductor import LanguageProcessor
from core.orchestrator import Orchestrator

class VoiceAssistant:
    def __init__(self, isOffline=True):
        """Initialize the voice assistant with all components."""
        self.stt = SpeechToText()
        self.tts = TextToSpeech(isOffline=isOffline)
        self.language_processor = LanguageProcessor()
        self.orchestrator = Orchestrator(isOffline=isOffline)

        #Historique des conversations
        self.conversation_history: List[Dict[str, str]] = []
        print("[Voice Assistant] Initialized successfully!")
    
    def listen(self) -> str:
        """Listen to user speech and convert to text."""
        print("[Listening] Speak now...")
        audio_text = self.stt.listen()
        print(f"[You said] {audio_text}")
        return audio_text
    
    def process(self, user_input: str) -> str:
        """Process the complete pipeline: translate -> orchestrate -> translate back."""
        # 1. Detect language and translate to English
        english_input, original_lang = self.language_processor.process_input(user_input)
        print(f"[Language] Detected: {original_lang} | Translated: {english_input}")

        # Check for exit commands
        exit_words = ['exit', 'quit', 'stop', 'bye']
        if any(word in english_input.lower() for word in exit_words):
            self.speak("Goodbye! Au revoir!")
            return False
        
        # 2. Process through orchestrator (intent classification + agent routing + conversation history)
        english_response = self.orchestrator.process_request(
            english_input,
            conversation_history=self.conversation_history
        )

        # 3. Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": english_input
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": english_response
        })
        
        # 4. Translate response back to original language
        final_response = self.language_processor.process_output(english_response, original_lang)
        print(f"[Assistant] {final_response}")
        
        return final_response
    
    def speak(self, text: str):
        """Convert text to speech."""
        print("[Speaking] ...")
        self.tts.speak(text)
    
    def run(self):
        """Run the voice assistant in interactive mode."""
        print("\n" + "="*60)
        print("🎤 Voice Assistant Ready!")
        print("Say 'exit' or 'quit' to stop")
        print("="*60 + "\n")
        
        stop = 0
        while True and stop==0:
            try:
                # Step 1: Listen to user
                user_input = self.listen()
                
                if not user_input:
                    print("[Error] Could not understand audio")
                    continue

                # Step 2-3-4: Process (translate -> orchestrate -> translate back)
                response = self.process(user_input)

                # Exit si il a demandé de partir
                if not response : break
                
                # Step 5: Speak the response
                self.speak(response)
                
                print("\n" + "-"*60 + "\n")
                #stop = 1
                
            except KeyboardInterrupt:
                print("\n[Interrupted] Shutting down...")
                self.speak("Goodbye!")
                stop = 1
                break
            except Exception as e:
                print(f"[Error] {str(e)}")
                self.speak("Sorry, I encountered an error. Please try again.")
                stop = 1

def main():
    """Main entry point."""
    isOffline = False
    
    assistant = VoiceAssistant(isOffline=isOffline)
    assistant.run()

if __name__ == "__main__":
    main()