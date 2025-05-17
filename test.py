import mss
import numpy as np
import pytesseract
import pyautogui
import cv2
from gpt4all import GPT4All
from pynput import keyboard
import threading
import sys
import os
import pytesseract

print("Paina K ottaaksesi kuvan hiiren kohdalta. Esc lopettaa.")
MODEL_PATH = os.path.expanduser("/Applications/gpt4all/models/Meta-Llama-3.1-8B-Instruct-128k-Q4_0.gguf")
# Load your LLM once
model = GPT4All(MODEL_PATH)
def process_capture():
    # Get mouse position
    x, y = pyautogui.position()

    # Define capture region (120x40 centered)
    region = {
        "top": y - 20,
        "left": x - 60,
        "width": 120,
        "height": 40
    }

    with mss.mss() as sct:
        img = np.array(sct.grab(region))

    # OCR
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
    text = pytesseract.image_to_string(img, config='--psm 6').strip()
    print("Teksti hiiren kohdalta:", text)

    # GPT4All inference
    prompt = "What is this in Witcher 3 game: " + text
    with model.chat_session():
        resp = model.generate(prompt, max_tokens=100)
        print(resp)

def on_press(key):
    try:
        if key.char.lower() == 'k':
            # Run capture in a thread so we don't block the listener
            threading.Thread(target=process_capture, daemon=True).start()

    except AttributeError:
        # Special keys (e.g. Esc)
        if key == keyboard.Key.esc:
            print("Lopetetaan.")
            # Returning False stops the listener
            return False

if __name__ == "__main__":
    # Start the listener; this will block until Esc is pressed
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
    sys.exit(0)