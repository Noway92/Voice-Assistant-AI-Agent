from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

class LanguageProcessor:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')
        self.detected_language = 'en'
    
    def detect_language(self, text: str) -> str:
        """Detect the language of the input text."""
        try:
            lang = detect(text)
            self.detected_language = lang
            return lang
        except LangDetectException:
            self.detected_language = 'en'
            return 'en'
    
    def translate_to_english(self, text: str) -> tuple[str, str]:
        """
        Translate text to English if needed.
        Returns: (translated_text, original_language)
        """
        lang = self.detect_language(text)
        
        if lang == 'en':
            return text, lang
        
        try:
            translated = self.translator.translate(text)
            return translated, lang
        except Exception as e:
            print(f"Translation error: {e}")
            return text, lang
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """Translate response back to original language."""
        if target_lang == 'en':
            return text
        
        try:
            translator = GoogleTranslator(source='en', target=target_lang)
            return translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def process_input(self, text: str) -> tuple[str, str]:
        """
        Process input: detect language and translate to English.
        Returns: (english_text, original_language)
        """
        return self.translate_to_english(text)
    
    def process_output(self, text: str, original_language: str) -> str:
        """
        Process output: translate back to original language if needed.
        """
        return self.translate_from_english(text, original_language)