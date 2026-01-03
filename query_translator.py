#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Query Translation Module for Cross-Lingual Information Retrieval (CLIR)
Implements bidirectional translation between English and Bangla.

Phase 2: Query Processing - Query Translation (English ↔ Bangla)
"""

import sys
from typing import Optional, Dict, List, Tuple
from functools import lru_cache
import hashlib

# Try to import translation libraries
try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False

try:
    from googletrans import Translator as GoogletransTranslator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False


class TranslationError(Exception):
    """Custom exception for translation errors."""
    pass


class QueryTranslator:
    """
    Bidirectional query translator for English ↔ Bangla.
    
    Features:
    - Automatic language detection
    - Translation caching for performance
    - Multiple translation backend support
    - Error handling and fallback
    - Batch translation support
    """
    
    def __init__(self, backend: str = 'auto', use_cache: bool = True):
        """
        Initialize the query translator.
        
        Args:
            backend: Translation backend ('deep_translator', 'googletrans', or 'auto')
            use_cache: Enable translation caching for performance
        """
        self.use_cache = use_cache
        self.translator = None
        self.backend_name = None
        
        # Initialize translation backend
        self._initialize_backend(backend)
        
        # Translation cache
        if self.use_cache:
            self._cache = {}
    
    def _initialize_backend(self, backend: str):
        """Initialize the translation backend."""
        if backend == 'auto':
            # Auto-select best available backend
            if HAS_DEEP_TRANSLATOR:
                self.translator = 'deep_translator'
                self.backend_name = 'deep_translator'
            elif HAS_GOOGLETRANS:
                self.translator = GoogletransTranslator()
                self.backend_name = 'googletrans'
            else:
                raise ImportError(
                    "No translation library available. Install 'deep-translator' or 'googletrans':\n"
                    "  pip install deep-translator\n"
                    "  or\n"
                    "  pip install googletrans==4.0.0-rc1"
                )
        elif backend == 'deep_translator':
            if not HAS_DEEP_TRANSLATOR:
                raise ImportError("deep-translator not installed. Install it with: pip install deep-translator")
            self.translator = 'deep_translator'
            self.backend_name = 'deep_translator'
        elif backend == 'googletrans':
            if not HAS_GOOGLETRANS:
                raise ImportError("googletrans not installed. Install it with: pip install googletrans==4.0.0-rc1")
            self.translator = GoogletransTranslator()
            self.backend_name = 'googletrans'
        else:
            raise ValueError(f"Unknown backend: {backend}. Use 'deep_translator', 'googletrans', or 'auto'")
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code ('en' or 'bn')
            target_lang: Target language code ('en' or 'bn')
            
        Returns:
            Translated text
            
        Raises:
            TranslationError: If translation fails
        """
        if not text or not text.strip():
            return text
        
        # Check if source and target are the same
        if source_lang == target_lang:
            return text
        
        # Check cache first
        if self.use_cache:
            cache_key = self._get_cache_key(text, source_lang, target_lang)
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        # Perform translation
        try:
            if self.backend_name == 'deep_translator':
                translated = self._translate_deep_translator(text, source_lang, target_lang)
            elif self.backend_name == 'googletrans':
                translated = self._translate_googletrans(text, source_lang, target_lang)
            else:
                raise TranslationError(f"Unknown backend: {self.backend_name}")
            
            # Cache the result
            if self.use_cache:
                self._cache[cache_key] = translated
            
            return translated
            
        except Exception as e:
            raise TranslationError(f"Translation failed: {str(e)}")
    
    def _translate_deep_translator(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using deep-translator library."""
        # Convert language codes
        source = 'en' if source_lang == 'en' else 'bn'
        target = 'en' if target_lang == 'en' else 'bn'
        
        translator = GoogleTranslator(source=source, target=target)
        return translator.translate(text)
    
    def _translate_googletrans(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using googletrans library."""
        # Convert language codes
        source = 'en' if source_lang == 'en' else 'bn'
        target = 'en' if target_lang == 'en' else 'bn'
        
        result = self.translator.translate(text, src=source, dest=target)
        return result.text
    
    def english_to_bangla(self, text: str) -> str:
        """
        Translate English text to Bangla.
        
        Args:
            text: English text
            
        Returns:
            Bangla translation
        """
        return self.translate(text, 'en', 'bn')
    
    def bangla_to_english(self, text: str) -> str:
        """
        Translate Bangla text to English.
        
        Args:
            text: Bangla text
            
        Returns:
            English translation
        """
        return self.translate(text, 'bn', 'en')
    
    def auto_translate(self, text: str, target_lang: str) -> str:
        """
        Auto-detect source language and translate to target.
        
        Args:
            text: Text to translate
            target_lang: Target language code ('en' or 'bn')
            
        Returns:
            Translated text
        """
        # Try to detect source language
        try:
            from language_detector import detect_language
            source_lang = detect_language(text)
        except ImportError:
            # Fallback: simple detection based on character ranges
            if any('\u0980' <= char <= '\u09FF' for char in text):
                source_lang = 'bn'
            else:
                source_lang = 'en'
        
        return self.translate(text, source_lang, target_lang)
    
    def batch_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """
        Translate multiple texts.
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        return [self.translate(text, source_lang, target_lang) for text in texts]
    
    def translate_with_original(self, text: str, source_lang: str, target_lang: str) -> Tuple[str, str]:
        """
        Translate and return both original and translated text.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Tuple of (original_text, translated_text)
        """
        translated = self.translate(text, source_lang, target_lang)
        return (text, translated)
    
    def _get_cache_key(self, text: str, source_lang: str, target_lang: str) -> str:
        """Generate cache key for translation."""
        key_string = f"{text}|{source_lang}|{target_lang}"
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def clear_cache(self):
        """Clear the translation cache."""
        if self.use_cache:
            self._cache.clear()
    
    def get_cache_size(self) -> int:
        """Get the number of cached translations."""
        return len(self._cache) if self.use_cache else 0
    
    def get_backend_info(self) -> Dict[str, str]:
        """Get information about the translation backend."""
        return {
            'backend': self.backend_name,
            'cache_enabled': self.use_cache,
            'cache_size': self.get_cache_size()
        }


# Convenience functions
def translate_query(text: str, source_lang: str, target_lang: str) -> str:
    """
    Quick translation function.
    
    Args:
        text: Text to translate
        source_lang: Source language ('en' or 'bn')
        target_lang: Target language ('en' or 'bn')
        
    Returns:
        Translated text
    
    Example:
        >>> translate_query("coronavirus vaccine", "en", "bn")
        'করোনাভাইরাস ভ্যাকসিন'
    """
    translator = QueryTranslator()
    return translator.translate(text, source_lang, target_lang)


def english_to_bangla(text: str) -> str:
    """
    Translate English to Bangla.
    
    Args:
        text: English text
        
    Returns:
        Bangla translation
    """
    translator = QueryTranslator()
    return translator.english_to_bangla(text)


def bangla_to_english(text: str) -> str:
    """
    Translate Bangla to English.
    
    Args:
        text: Bangla text
        
    Returns:
        English translation
    """
    translator = QueryTranslator()
    return translator.bangla_to_english(text)


if __name__ == "__main__":
    print("Query Translation Module - Quick Test")
    print("=" * 80)
    
    try:
        translator = QueryTranslator()
        
        print(f"\nBackend: {translator.backend_name}")
        print("=" * 80)
        
        # Test English to Bangla
        print("\n1. English to Bangla Translation:")
        en_queries = [
            "coronavirus vaccine",
            "cricket match",
            "election results"
        ]
        
        for query in en_queries:
            try:
                translated = translator.english_to_bangla(query)
                print(f"  EN: {query}")
                print(f"  BN: {translated}\n")
            except Exception as e:
                print(f"  Error translating '{query}': {e}\n")
        
        # Test Bangla to English
        print("\n2. Bangla to English Translation:")
        bn_queries = [
            "করোনা ভ্যাকসিন",
            "ক্রিকেট খেলা",
            "নির্বাচন ফলাফল"
        ]
        
        for query in bn_queries:
            try:
                translated = translator.bangla_to_english(query)
                print(f"  BN: {query}")
                print(f"  EN: {translated}\n")
            except Exception as e:
                print(f"  Error translating '{query}': {e}\n")
        
        # Cache info
        print(f"\nCache size: {translator.get_cache_size()} translations")
        
    except ImportError as e:
        print(f"\n⚠ Translation library not installed:")
        print(f"  {e}")
        print("\nInstall one of these:")
        print("  pip install deep-translator")
        print("  pip install googletrans==4.0.0-rc1")
