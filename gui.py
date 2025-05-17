from ttkbootstrap import Style
import ttkbootstrap as ttk
from gtts import gTTS
import pygame

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
    myobj = gTTS(text=new_text, lang='en', slow=False)
    myobj.save("tts.mp3")
    pygame.mixer.init()
    pygame.mixer.music.load("tts.mp3")
    pygame.mixer.music.play()
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
def do_after_window_opens():
    update_window_prompt_text("This is a test prompt for the item idk\n It works?")
    update_item_name("Name of item")
    update_status()

root.after(1, do_after_window_opens)
root.mainloop()

