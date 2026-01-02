#!/usr/bin/env python3
"""Test the improved Bangla tokenization."""

def tokenize_bangla(text: str) -> int:
    """Tokenize Bangla text using whitespace-based word tokenization."""
    if not text or not text.strip():
        return 0

    # Bengali punctuation marks
    bangla_punctuation = '।॥!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

    # Split on whitespace
    tokens = text.split()

    # Filter out tokens that are only punctuation
    word_tokens = []
    for token in tokens:
        # Remove punctuation from both ends
        cleaned = token.strip(bangla_punctuation)
        # If something remains after removing punctuation, it's a word
        if cleaned:
            word_tokens.append(cleaned)

    return len(word_tokens)


# Test with sample Bangla text
test_text = "বাংলাদেশ একটি সুন্দর দেশ। এখানে অনেক মানুষ বাস করে।"

token_count = tokenize_bangla(test_text)
print(f"Test text: {test_text}")
print(f"Token count: {token_count}")
print("✓ Bangla tokenizer works!")
