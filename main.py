000000# !pip install vosk pyaudio rapidfuzz colorama

import vosk
import pyaudio
import json
import time
import simpleaudio as sa
import threading
from rapidfuzz import fuzz
from colorama import init, Fore, Back, Style
import os
import numpy as np
import whisper
from constants import EXACT_THRESHOLD, FUZZY_THRESHOLD, SIMILAR_THRESHOLD, WHISPER_MODEL_NAME, SAMPLE_RATE

# Initialize colorama for colored console output
init()

def clear_screen():
    """Clear console screen for better UI"""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_welcome_screen():
    """Display an attractive welcome screen"""
    clear_screen()
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.WHITE}🎤 {Fore.YELLOW}Voice-Based Name Detection System{Fore.WHITE} 🎤")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    print(f"{Fore.GREEN}[System Configuration]")
    print(f"{Fore.WHITE}• Model: Indian English (vosk-model-en-in-0.5)")
    print(f"• Sample Rate: 16000 Hz")
    print(f"• Buffer Size: 4096\n")

def get_user_settings():
    """Get user settings - simplified to only ask for names"""
    print(f"{Fore.YELLOW}[Settings Configuration]{Style.RESET_ALL}")
    
    while True:
        target_names = input(f"{Fore.WHITE}Enter names to detect (comma-separated): ").lower()
        if target_names.strip():
            break
        print(f"{Fore.RED}Please enter at least one name.{Style.RESET_ALL}")
    
    return target_names

# Whisper model name (can be 'base', 'small', 'medium', 'large', etc.)
WHISPER_MODEL_NAME = 'base'

# Sample rate for audio (Whisper expects 16000 Hz for PCM)
SAMPLE_RATE = 16000

# Alternative model paths (choose the most suitable one)
MODEL_PATHS = {
    'indian': r"vosk-model-en-in-0.5",
}

# Use the Indian model by default
MODEL_PATH = MODEL_PATHS['indian']

# Initialize Vosk model
try:
    model = vosk.Model(MODEL_PATH)
except Exception as e:
    print(f"Failed to load Vosk model. Error: {e}")
    exit(1)

# Initialize recognizer with sample rate
recognizer = vosk.KaldiRecognizer(model, 16000)
recognizer.SetWords(True)  # Enable word timing
recognizer.SetPartialWords(True)  # Enable partial results

# Set up PyAudio for real-time audio capture
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096)
stream.start_stream()

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

def play_beep():
    """
    Play an alert pattern with multiple beeps to simulate vibration effect.
    Requires 'beep.wav' in the project directory.
    """
    beep_wave = sa.WaveObject.from_wave_file("beep.wav")
    
    for _ in range(3):  # Play 3 quick beeps
        play_obj = beep_wave.play()
        play_obj.wait_done()
        time.sleep(0.05)  # Small delay between beeps


def play_alert_async():
    """
    Play alert sound with vibration effect in a separate thread.
    """
    alert_thread = threading.Thread(target=play_beep)
    alert_thread.start()

def display_status(recognized_text, matches):
    """Display real-time status with colored output"""
    print(f"\n{Fore.CYAN}Recognized Text: {Fore.WHITE}{recognized_text}")
    
    for match, score, target in matches:
        timestamp = time.strftime('%H:%M:%S')
        if score >= EXACT_THRESHOLD:
            print(f"{Fore.GREEN}[{timestamp}] Strong Match: '{match}' → '{target}' (Score: {score})")
        elif score >= FUZZY_THRESHOLD:
            print(f"{Fore.YELLOW}[{timestamp}] Possible Match: '{match}' → '{target}' (Score: {score})")
        elif score >= SIMILAR_THRESHOLD:
            print(f"{Fore.RED}[{timestamp}] Similar Name: '{match}' → '{target}' (Score: {score})")
    
    print(f"{Style.RESET_ALL}", end='')

# Main loop to listen and detect names in real-time
try:
    # Initialize the interface
    display_welcome_screen()
    TARGET_NAME = get_user_settings()  # Only get the target names
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.WHITE}🎯 Listening for names: {Fore.YELLOW}{TARGET_NAME}")
    print(f"{Fore.WHITE}📢 Say 'stop' to end the program")
    print(f"{Fore.CYAN}{'='*60}\n")

    while True:
        # Read audio data
        data = stream.read(4096, exception_on_overflow=False)
        
        if recognizer.AcceptWaveform(data):
            # Get recognition result
            result = json.loads(recognizer.Result())
            recognized_text = result.get("text", "")
            
            if recognized_text:  # Only process if there's recognized text
                print(f"\nRecognized: {recognized_text}")
                
                # Process the recognized text
                tokens = preprocess_text(recognized_text)
                matches = detect_name_fuzzy(tokens, TARGET_NAME, FUZZY_THRESHOLD)
                
                # Handle matches based on confidence levels
                for match, score, match_type, target in matches:
                    if score >= EXACT_THRESHOLD:
                        detection_log = f"[{time.strftime('%H:%M:%S')}] Strong Match: '{match}' matches '{target}' (Score: {score})"
                        print(detection_log)
                        play_alert_async()
                    elif score >= FUZZY_THRESHOLD:
                        detection_log = f"[{time.strftime('%H:%M:%S')}] Possible Match: '{match}' matches '{target}' (Score: {score})"
                        print(detection_log)
                        play_alert_async()
                    elif score >= SIMILAR_THRESHOLD:
                        detection_log = f"[{time.strftime('%H:%M:%S')}] Similar Name: '{match}' matches '{target}' (Score: {score})"
                        print(detection_log)
                
                # Check for stop command
                if "stop" in tokens:
                    print("\nStop command received. Stopping...")
                    break

except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}Interrupted by user. Stopping...{Style.RESET_ALL}")
except Exception as e:
    print(f"\n{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")
finally:
    # Clean up resources
    print(f"\n{Fore.CYAN}Cleaning up...{Style.RESET_ALL}")
    stream.stop_stream()
    stream.close()
    p.terminate()
    print(f"{Fore.GREEN}Program terminated successfully.{Style.RESET_ALL}")