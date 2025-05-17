import os
import re
import mss
import sys
import cv2
import numpy as np
import requests
import threading
import pyautogui
import pytesseract
from bs4 import BeautifulSoup
from gpt4all import GPT4All
from pynput import keyboard
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ──────────────────────────────────────────────────────────────
# 🔧 Configuration
# ──────────────────────────────────────────────────────────────

MODEL_PATH = os.path.expanduser("/home/fdessoy/.local/share/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf")
TESSERACT_PATH = "/usr/bin/tesseract"  # Default path on many Linux systems
GAME_NAME = "Witcher 3"
FANDOM_SUBDOMAIN = "witcher"

# ──────────────────────────────────────────────────────────────
# ⚙️ Load GPT4All model once
# ──────────────────────────────────────────────────────────────

model = GPT4All(MODEL_PATH)

# ──────────────────────────────────────────────────────────────
# 🧠 GPT4All: Refine query
# ──────────────────────────────────────────────────────────────

def query_optimization(input_text):
    try:
        with model.chat_session():
            prompt = (
                "You are an in-game AI assistant. "
                "Turn vague gamer questions into short, fandom-compatible search queries using boss names, item names, or concise objectives. "
                "Do not explain. Output only the search query.\n\n"
                f"Player input: {input_text}"
            )
            response = model.generate(prompt, max_tokens=100)
            return response.strip()
    except Exception as e:
        return f"[ERROR] GPT4All failed: {e}"

# ──────────────────────────────────────────────────────────────
# 🧹 Clean search query for wiki compatibility
# ──────────────────────────────────────────────────────────────

def clean_query_for_fandom(raw_query, game_name):
    raw = raw_query.lower()
    phrases_to_remove = [
        "how to beat", "how do i beat", "boss fight", "walkthrough",
        "strategies", "tutorial", "guide", "tips", "best way to",
        "faq", "in", "for", game_name
    ]
    for phrase in phrases_to_remove:
        raw = raw.replace(phrase, "")
    typo_fixes = {"witchr": "witcher", "geralt": "geralt", "wild hunt": "wild hunt"}
    for typo, fix in typo_fixes.items():
        raw = raw.replace(typo, fix)
    raw = re.sub(r'[^\w\s]', '', raw)
    cleaned = ' '.join(raw.split())
    return f"{cleaned}"

# ──────────────────────────────────────────────────────────────
# 🌐 Fandom Wiki Search
# ──────────────────────────────────────────────────────────────

def search_fandom(query, game_subdomain=FANDOM_SUBDOMAIN):
    try:
        search_url = f"https://{game_subdomain}.fandom.com/wiki/Special:Search?query={query.replace(' ', '+')}&limit=5"
        print(f"🔍 Searching: {search_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')

        if response.url.startswith(f"https://{game_subdomain}.fandom.com/wiki/") and "Special:Search" not in response.url:
            return [response.url]

        links = []
        for a in soup.select('a.mw-search-result-heading'):
            href = a.get('href')
            if href and href.startswith("/wiki/"):
                full_url = f"https://{game_subdomain}.fandom.com{href}"
                links.append(full_url)

        return links[:2] if links else ["[No search results found on Fandom]"]
    except Exception as e:
        return [f"[ERROR] Fandom direct search failed: {e}"]

# ──────────────────────────────────────────────────────────────
# 📸 OCR + Assistant logic triggered by keypress
# ──────────────────────────────────────────────────────────────

def process_capture():
    x, y = pyautogui.position()
    region = {"top": y - 20, "left": x - 60, "width": 120, "height": 40}

    with mss.mss() as sct:
        img = np.array(sct.grab(region))

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    text = pytesseract.image_to_string(img, config='--psm 6').strip()
    print("\n🖼️ OCR Text:", text)

    refined_query = query_optimization(text)
    print("🤖 Optimized Query:", refined_query)

    search_query = clean_query_for_fandom(refined_query, GAME_NAME)
    print("🔍 Cleaned Query:", search_query)

    fandom_results = search_fandom(search_query)
    print("\n📚 Fandom Results:")
    for i, link in enumerate(fandom_results, 1):
        print(f"{i}. {link}")

# ──────────────────────────────────────────────────────────────
# ⌨️ Keyboard Listener
# ──────────────────────────────────────────────────────────────

def on_press(key):
    try:
        if key.char.lower() == 'k':
            threading.Thread(target=process_capture, daemon=True).start()
    except AttributeError:
        if key == keyboard.Key.esc:
            print("🛑 Exiting.")
            return False

# ──────────────────────────────────────────────────────────────
# 🚀 Main
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🎮 Press K to analyze screen under mouse. Press Esc to quit.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
    sys.exit(0)
