#!/usr/bin/env python3
"""Simple test script for query translator - no UTF-8 wrapper"""

import sys
import io

# Prevent the modules from overwriting stdout/stderr
_original_stdout = sys.stdout
_original_stderr = sys.stderr

from query_translator import QueryTranslator
from query_normalizer import QueryNormalizer
from language_detector import LanguageDetector

# Restore original stdout/stderr
sys.stdout = _original_stdout
sys.stderr = _original_stderr

print("=" * 80)
print("CLIR Query Translation - Simple Test")
print("=" * 80)

# Test 1: Basic Translation
print("\n1. Basic Translation Test")
print("-" * 80)
translator = QueryTranslator()

print("\nEnglish to Bangla:")
en_query = "coronavirus vaccine news"
bn_query = translator.english_to_bangla(en_query)
print(f"  EN: {en_query}")
print(f"  BN: {bn_query}")

print("\nBangla to English:")
bn_query = "করোনা ভ্যাকসিন সংবাদ"
en_query = translator.bangla_to_english(bn_query)
print(f"  BN: {bn_query}")
print(f"  EN: {en_query}")

# Test 2: Integrated Pipeline
print("\n\n2. Integrated Pipeline Test")
print("-" * 80)
normalizer = QueryNormalizer()
detector = LanguageDetector()

query = "  COVID-19   vaccine   news  "
print(f"\nUser input: '{query}'")

# Normalize
normalized = normalizer.normalize(query)
print(f"Normalized: '{normalized}'")

# Detect language
lang = detector.detect(normalized)
print(f"Language:   {lang}")

# Translate
target = 'bn' if lang == 'en' else 'en'
translated = translator.translate(normalized, lang, target)
print(f"Translated: '{translated}' ({target})")

# Test 3: Cache Test
print("\n\n3. Translation Cache Test")
print("-" * 80)
print(f"Cache size before: {translator.get_cache_size()}")

# Translate same query again (should use cache)
result = translator.english_to_bangla("coronavirus vaccine news")
print(f"Translation result: {result}")
print(f"Cache size after:  {translator.get_cache_size()}")

# Test 4: Batch Translation
print("\n\n4. Batch Translation Test")
print("-" * 80)
queries = [
    "cricket match",
    "election results",
    "weather forecast"
]

print("Translating batch of English queries to Bangla:")
translations = translator.batch_translate(queries, "en", "bn")
for orig, trans in zip(queries, translations):
    print(f"  {orig:20s} -> {trans}")

# Test 5: Backend Info
print("\n\n5. Backend Information")
print("-" * 80)
info = translator.get_backend_info()
print(f"Backend:       {info['backend']}")
print(f"Cache enabled: {info['cache_enabled']}")
print(f"Cache size:    {info['cache_size']}")

print("\n" + "=" * 80)
print("All tests completed successfully!")
print("=" * 80)
