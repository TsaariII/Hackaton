import mss
import numpy as np
import pytesseract
import pyautogui
import cv2
import keyboard  # pip install keyboard
#from gpt4all import 
#model = GPT4All("ggml-gpt4all-j-v1.3-groovy.gguf") # downloads / loads a 4.66GB LLM
from ttkbootstrap import Style
import ttkbootstrap as ttk
from gtts import gTTS
import pygame

import time

import tkinter as tk


root = ttk.Window(themename='cyborg')           # Configure the themename when creating the window
root.geometry("600x800")                        # Sets the initial size of the window

title_label = ttk.Label(root, text="  Universal    -   \n   -    Smartass  ")
title_label.config(font=("Hobo Std", 40, "bold"))
title_label.pack(pady=30)

parent = ttk.Frame(root)
parent.pack(pady=5, padx=10, fill="x")

# PROGRESS STATE TITLE
status_label = ttk.Label(parent, text=" Finding... ", bootstyle="inverse-info")
status_label.config(font=("Helvetica", 30, "bold"))
status_label.pack(pady=1, padx=10)

# EMPTY SPACE (filler)
empty_label = ttk.Label(parent, text="\n")
empty_label.config(font=("Helvetica", 10, "bold"))
empty_label.pack(pady=1, padx=10)

# ITEM NAME TITLE
item_label = ttk.Label(parent, text="", bootstyle="inverse-primary", wraplength=550)
item_label.config(font=("Helvetica", 30, "bold"))
item_label.pack(pady=5, padx=10, fill="x")

# PROMPT TEXT OUTPUT
prompt_label = ttk.Label(parent, text="", bootstyle="primary", wraplength=550)
prompt_label.config(font=("Helvetica", 20))
prompt_label.pack(pady=5, padx=10, fill="x")


def update_status():
    status_label.config(text = " Got reply! ")

def update_item_name(new_text):
    new_text = " " + new_text + " "
    item_label.config(text = new_text)

def update_window_prompt_text(new_text):
    # Text to speech ==================
    #myobj = gTTS(text=new_text, lang='en', slow=False)
    #myobj.save("tts.mp3")
    #pygame.mixer.init()
    #pygame.mixer.music.load("tts.mp3")
    #pygame.mixer.music.play()
    # --------------------------------
    padding = 0
    while padding < 42:
        new_text = new_text + "\n"
        padding += 1
    prompt_label.config(text = new_text)

#ttk.Entry(parent).pack(side="left", fill="x", expand=True, padx=5) # Create & pack entry widget

# Close window function
def close_win(e):
   root.destroy()
   exit()

# Bind the ESC key with the callback function
root.bind('<Escape>', lambda e: close_win(e))
root.bind('<k>', lambda e: close_win(e))


#NOTE This function will be ran once after the window is open
def do_after_window_opens(text):
    update_window_prompt_text("This is a test prompt for the item idk\n It works?")
    update_item_name(text)
    update_status()


def strip_text(text):
    text = text.strip()  # Poistaa ylimääräiset välilyönnit edestä ja takaa
    #text = max(text.split("\n"), key=len)  # Valitse rivi, jossa on eniten tekstiä
    print("Puhdistettu teksti:", text)
    return text

def adjust_gamma(image, gamma=1.0):
    """
    Säädä kuvan gamma-arvoja.
    :param image: Syötekuva (numpy array)
    :param gamma: Gamma-arvo (oletus 1.0, ei muutosta)
    :return: Gamma-korjattu kuva
    """
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, table)

def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, strength=1.5):
    """
    Toteuttaa unsharp mask -terävöityksen.
    :param image: Syötekuva (numpy array)
    :param kernel_size: Gaussian blur -suodattimen koko
    :param sigma: Gaussian blur -suodattimen sigma-arvo
    :param strength: Terävöityksen vahvistuskerroin
    :return: Terävöitetty kuva
    """
    # Luo sumea versio kuvasta
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    
    # Luo terävöitetty kuva
    sharpened = cv2.addWeighted(image, 1 + strength, blurred, -strength, 0)
    return sharpened

#while True:
    #if keyboard.is_pressed("k"):
        # Odota että näppäin vapautetaan (jottei laukea useasti)
        #keyboard.wait("k", suppress=True)

        # Hae hiiren sijainti
x, y = pyautogui.position()

    # Määritä alue hiiren ympärillä (esim. 120x40 pikseliä)
region = {
    "top": y - 20,
    "left": x - 40,
    "width": 180,
    "height": 40
}

    #with mss.mss() as sct:
    #img = np.array(sct.grab(region))
    #img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)  # Remove alpha channel
    #gray = cv2.cvtColor(ocr_output.png, cv2.COLOR_BGR2GRAY)
#gray = ocr_output.png

    # Apply gamma correction to enhance contrast
    #gamma = adjust_gamma(gray, gamma=0.5)

    # Apply unsharp mask to enhance edges
    #sharpened = unsharp_mask(gamma, kernel_size=(5, 5), sigma=1.0, strength=1.5)

    # Resize the image to make text more readable
    #zoomed = cv2.resize(sharpened, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)

    # Apply adaptive thresholding for binarization
    #zoomed = cv2.adaptiveThreshold(zoomed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Binarisoi kuva
    #zoomed = cv2.threshold(zoomed, 130, 255, cv2.THRESH_BINARY)[1]
    #zoomed = cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    # Esikäsittelyt
    #gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
    #zoomed = cv2.GaussianBlur(zoomed, (3, 3), 0)
    #zoomed = cv2.threshold(zoomed, 180, 255, cv2.THRESH_BINARY)[1]
    

text = pytesseract.image_to_string("ocr_output.png", config='--psm 6')
print("Teksti hiiren kohdalta:", text.strip())

    # Näytä kuva debuggausta varten (sulje painamalla mitä tahansa)
    #gray = np.array(sct.grab(region))
    #gray = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # poistaa alpha-kanavan

    #cv2.imshow("Esikäsitelty kuva", zoomed)
    #cv2.imwrite("kuva.png", zoomed)
    #cv2.waitKey(1)
    #with model.chat_session():
        #print(model.generate("What is this in Witcher 3 game" + text, max_tokens=20))
    #print("Min pixel value is: ", gray.min())
    #print("Max pixel value is: ", gray.max())
    #print("Image dtype is: ", gray.dtype)
    #print("Image shape is: ", gray.shape)
text2 = strip_text(text.strip())
if keyboard.is_pressed("esc"):
    print("Lopetetaan.")
    #break

#cv2.destroyAllWindows()

root.after(1, do_after_window_opens(text2))
root.mainloop()
