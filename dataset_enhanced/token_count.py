import stanza
import re

# Download models (run once)
stanza.download("en")
stanza.download("bn")

# Load pipelines once (important for performance)
nlp_en = stanza.Pipeline("en", processors="tokenize", use_gpu=False, verbose=False)
nlp_bn = stanza.Pipeline("bn", processors="tokenize", use_gpu=False, verbose=False)

def detect_language(text: str) -> str:
    """
    Simple heuristic:
    If Bangla Unicode present → bn
    Else → en
    """
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"
    return "en"

def count_tokens(sentence: str):
    """
    Automatically detects language and returns:
    - language
    - token count
    - token list
    """
    lang = detect_language(sentence)
    nlp = nlp_bn if lang == "bn" else nlp_en

    doc = nlp(sentence)

    tokens = [
        token.text
        for sent in doc.sentences
        for token in sent.tokens
    ]

    return {
        "language": lang,
        "token_count": len(tokens),
        "tokens": tokens
    }


# ------------------ Example ------------------

if __name__ == "__main__":
    sentences = [
        "Stanza is a great NLP library.",
        "আমি স্ট্যানজা ব্যবহার করে টোকেন গুনছি।"
    ]

    for s in sentences:
        result = count_tokens(s)
        print("\nSentence:", s)
        print("Language:", result["language"])
        print("Token Count:", result["token_count"])
        print("Tokens:", result["tokens"])
