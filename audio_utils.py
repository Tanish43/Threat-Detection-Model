import json
from rapidfuzz import fuzz
import numpy as np
import whisper
from constants import EXACT_THRESHOLD, FUZZY_THRESHOLD, SIMILAR_THRESHOLD, WHISPER_MODEL_NAME, SAMPLE_RATE

# Load Whisper model
whisper_model = whisper.load_model(WHISPER_MODEL_NAME)

def preprocess_text(text):
    normalized_text = text.lower().split()
    indian_variations = {
        'wery': 'very',
        'dat': 'that',
        'dis': 'this',
    }
    filler_words = {
        "um", "uh", "ah", "like", "you", "know", "so", "well", 
        "right", "okay", "yeah", "the", "a", "an", "and", "but",
        "or", "if", "then", "that", "this", "these", "those",
        "accha", "haan", "matlab", "actually", "basically"
    }
    processed_tokens = []
    for word in normalized_text:
        word = indian_variations.get(word, word)
        if word and word not in filler_words:
            processed_tokens.append(word)
    return processed_tokens

def detect_name_fuzzy(tokens, target_names, threshold):
    matches = []
    tokens_list = list(tokens)
    word_pairs = list(zip(tokens_list[:-1], tokens_list[1:])) if len(tokens_list) > 1 else []
    for token in tokens:
        for target_name in target_names.split(','):
            target_name = target_name.strip().lower()
            ratio_similarity = fuzz.ratio(token, target_name)
            partial_similarity = fuzz.partial_ratio(token, target_name)
            token_score = max(ratio_similarity, partial_similarity)
            if token_score >= threshold:
                matches.append((token, token_score, "exact", target_name))
            elif token_score >= SIMILAR_THRESHOLD:
                matches.append((token, token_score, "similar", target_name))
    for first, second in word_pairs:
        combined = f"{first} {second}"
        for target_name in target_names.split(','):
            target_name = target_name.strip().lower()
            ratio_similarity = fuzz.ratio(combined, target_name)
            partial_similarity = fuzz.partial_ratio(combined, target_name)
            pair_score = max(ratio_similarity, partial_similarity)
            if pair_score >= threshold:
                matches.append((combined, pair_score, "compound", target_name))
    return matches

def process_audio_bytes(audio_bytes, target_names):
    # Convert bytes to numpy array (assume 16-bit PCM mono)
    audio_np = np.frombuffer(audio_bytes, np.int16).astype(np.float32) / 32768.0
    # Whisper expects float32 numpy array, 16kHz mono
    result = whisper_model.transcribe(audio_np, language='en', fp16=False, task='transcribe', verbose=False)
    recognized_text = result.get('text', '').strip()
    tokens = preprocess_text(recognized_text)
    matches = detect_name_fuzzy(tokens, target_names, FUZZY_THRESHOLD)
    is_beep = any(score >= EXACT_THRESHOLD for _, score, _, _ in matches)
    return recognized_text, is_beep