#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Language Detection Module for Cross-Lingual Information Retrieval (CLIR)
Implements Bangla/English language detection using Unicode ranges and statistical methods.

Phase 2: Query Processing - Language Detection (Bangla/English)
"""

import sys
import re
from typing import Dict, Tuple, Optional
from collections import Counter


class LanguageDetector:
    """
    Detect whether text is Bangla or English.
    
    Uses multiple detection methods:
    1. Unicode range detection (primary method)
    2. Character frequency analysis
    3. Script mixing detection
    """
    
    # Unicode ranges for Bangla (Bengali) script
    BANGLA_RANGE = (0x0980, 0x09FF)  # Bengali Unicode block
    
    # Common Bangla characters for additional validation
    BANGLA_CHARS = set('অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎংঃঁািীুূৃেৈোৌ্ৗ')
    
    # English alphabet
    ENGLISH_CHARS = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    def __init__(self, threshold: float = 0.3):
        """
        Initialize language detector.
        
        Args:
            threshold: Minimum ratio of language-specific characters to classify
                      (default: 0.3 means 30% of text must be in target script)
        """
        self.threshold = threshold
    
    def detect(self, text: str) -> str:
        """
        Detect language of the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            'bn' for Bangla, 'en' for English
        """
        if not text or not text.strip():
            return 'en'  # Default to English for empty text
        
        # Count characters in each script
        bangla_count = sum(1 for char in text if self._is_bangla_char(char))
        english_count = sum(1 for char in text if self._is_english_char(char))
        
        # Determine language based on character counts
        if bangla_count > english_count:
            return 'bn'
        else:
            return 'en'
    
    def detect_with_confidence(self, text: str) -> Tuple[str, float, Dict[str, int]]:
        """
        Detect language with confidence score and detailed statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_code, confidence, statistics)
            - language_code: 'bn' or 'en'
            - confidence: float between 0 and 1
            - statistics: dict with character counts
        """
        if not text or not text.strip():
            return 'en', 0.0, {'bangla': 0, 'english': 0, 'other': 0, 'total': 0}
        
        # Count different character types
        bangla_count = 0
        english_count = 0
        other_count = 0
        
        for char in text:
            if self._is_bangla_char(char):
                bangla_count += 1
            elif self._is_english_char(char):
                english_count += 1
            elif not char.isspace() and char not in '.,;:!?-_()[]{}"\'/\\':
                other_count += 1
        
        total_chars = bangla_count + english_count + other_count
        
        # Calculate confidence
        if total_chars == 0:
            return 'en', 0.0, {'bangla': 0, 'english': 0, 'other': 0, 'total': 0}
        
        bangla_ratio = bangla_count / total_chars
        english_ratio = english_count / total_chars
        
        # Determine language and confidence
        if bangla_ratio > english_ratio:
            language = 'bn'
            confidence = bangla_ratio
        else:
            language = 'en'
            confidence = english_ratio
        
        statistics = {
            'bangla': bangla_count,
            'english': english_count,
            'other': other_count,
            'total': total_chars,
            'bangla_ratio': bangla_ratio,
            'english_ratio': english_ratio
        }
        
        return language, confidence, statistics
    
    def is_bangla(self, text: str) -> bool:
        """
        Check if text is primarily Bangla.
        
        Args:
            text: Input text
            
        Returns:
            True if text is Bangla, False otherwise
        """
        return self.detect(text) == 'bn'
    
    def is_english(self, text: str) -> bool:
        """
        Check if text is primarily English.
        
        Args:
            text: Input text
            
        Returns:
            True if text is English, False otherwise
        """
        return self.detect(text) == 'en'
    
    def is_mixed(self, text: str, threshold: float = 0.2) -> bool:
        """
        Check if text contains significant mixing of Bangla and English.
        
        Args:
            text: Input text
            threshold: Minimum ratio for both languages to be considered mixed
            
        Returns:
            True if text is mixed language, False otherwise
        """
        _, _, stats = self.detect_with_confidence(text)
        
        if stats['total'] == 0:
            return False
        
        bangla_ratio = stats['bangla'] / stats['total']
        english_ratio = stats['english'] / stats['total']
        
        # Both languages must meet threshold
        return bangla_ratio >= threshold and english_ratio >= threshold
    
    def _is_bangla_char(self, char: str) -> bool:
        """
        Check if a character is Bangla.
        
        Args:
            char: Single character
            
        Returns:
            True if Bangla character, False otherwise
        """
        return self.BANGLA_RANGE[0] <= ord(char) <= self.BANGLA_RANGE[1]
    
    def _is_english_char(self, char: str) -> bool:
        """
        Check if a character is English alphabetic.
        
        Args:
            char: Single character
            
        Returns:
            True if English character, False otherwise
        """
        return char in self.ENGLISH_CHARS
    
    def analyze_text(self, text: str) -> Dict:
        """
        Comprehensive text analysis with language detection.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with detailed analysis
        """
        language, confidence, stats = self.detect_with_confidence(text)
        is_mixed = self.is_mixed(text)
        
        # Word count
        words = text.split()
        word_count = len(words)
        
        # Character count (excluding whitespace)
        char_count = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        return {
            'language': language,
            'language_name': 'Bangla' if language == 'bn' else 'English',
            'confidence': confidence,
            'is_mixed': is_mixed,
            'statistics': stats,
            'word_count': word_count,
            'character_count': char_count,
            'text_length': len(text)
        }
    
    def batch_detect(self, texts: list) -> list:
        """
        Detect language for multiple texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of language codes
        """
        return [self.detect(text) for text in texts]
    
    def get_language_distribution(self, text: str) -> Dict[str, float]:
        """
        Get percentage distribution of languages in text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with language percentages
        """
        _, _, stats = self.detect_with_confidence(text)
        
        if stats['total'] == 0:
            return {'bangla': 0.0, 'english': 0.0, 'other': 0.0}
        
        return {
            'bangla': (stats['bangla'] / stats['total']) * 100,
            'english': (stats['english'] / stats['total']) * 100,
            'other': (stats['other'] / stats['total']) * 100
        }


def detect_language(text: str) -> str:
    """
    Convenience function for quick language detection.
    
    Args:
        text: Input text
        
    Returns:
        'bn' for Bangla, 'en' for English
    """
    detector = LanguageDetector()
    return detector.detect(text)


def main():
    """Demo of language detection capabilities."""
    print("="*80)
    print("Language Detection Module - Demo")
    print("Phase 2: Query Processing - Language Detection (Bangla/English)")
    print("="*80)
    
    detector = LanguageDetector()
    
    # Test cases
    test_texts = [
        ("Hello, how are you?", "English"),
        ("আমি ভালো আছি", "Bangla"),
        ("Bangladesh is a beautiful country", "English"),
        ("ঢাকা বাংলাদেশের রাজধানী", "Bangla"),
        ("করোনা ভাইরাস pandemic", "Mixed"),
        ("ক্রিকেট খেলা cricket match", "Mixed"),
        ("The Daily Star newspaper", "English"),
        ("প্রথম আলো পত্রিকা", "Bangla"),
    ]
    
    print("\n" + "="*80)
    print("Basic Language Detection")
    print("="*80)
    
    for text, expected in test_texts:
        lang = detector.detect(text)
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"\nText: {text}")
        print(f"Expected: {expected}")
        print(f"Detected: {lang_name} ({lang})")
    
    print("\n" + "="*80)
    print("Detection with Confidence Scores")
    print("="*80)
    
    for text, _ in test_texts[:4]:
        lang, confidence, stats = detector.detect_with_confidence(text)
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"\nText: {text}")
        print(f"Language: {lang_name} ({lang})")
        print(f"Confidence: {confidence:.2%}")
        print(f"Stats: Bangla={stats['bangla']}, English={stats['english']}, Other={stats['other']}")
    
    print("\n" + "="*80)
    print("Mixed Language Detection")
    print("="*80)
    
    for text, _ in test_texts[4:6]:
        is_mixed = detector.is_mixed(text)
        distribution = detector.get_language_distribution(text)
        print(f"\nText: {text}")
        print(f"Is Mixed: {is_mixed}")
        print(f"Distribution: Bangla={distribution['bangla']:.1f}%, English={distribution['english']:.1f}%")
    
    print("\n" + "="*80)
    print("Comprehensive Analysis")
    print("="*80)
    
    sample_text = "বাংলাদেশ দক্ষিণ এশিয়ার একটি দেশ"
    analysis = detector.analyze_text(sample_text)
    
    print(f"\nText: {sample_text}")
    print(f"Language: {analysis['language_name']} ({analysis['language']})")
    print(f"Confidence: {analysis['confidence']:.2%}")
    print(f"Is Mixed: {analysis['is_mixed']}")
    print(f"Word Count: {analysis['word_count']}")
    print(f"Character Count: {analysis['character_count']}")
    print(f"Bangla Chars: {analysis['statistics']['bangla']}")
    print(f"English Chars: {analysis['statistics']['english']}")
    
    print("\n" + "="*80)
    print("Batch Detection")
    print("="*80)
    
    batch_texts = [
        "Hello World",
        "আসসালামু আলাইকুম",
        "Good morning",
        "শুভ সকাল"
    ]
    
    results = detector.batch_detect(batch_texts)
    for text, lang in zip(batch_texts, results):
        lang_name = "Bangla" if lang == "bn" else "English"
        print(f"{text:30s} → {lang_name} ({lang})")
    
    print("\n" + "="*80)
    print("Language Detection Module Ready!")
    print("="*80)


if __name__ == "__main__":
    main()
