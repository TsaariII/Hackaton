import os
import re
import mss
import cv2
import sys
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
import sqlite3
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
# def do_after_window_opens():
#     update_window_prompt_text("This is a test prompt for the item idk\n It works?")
#     update_item_name("Name of item")
#     update_status()

# root.after(1, do_after_window_opens)
# root.mainloop()

#df is your dataframe
#example function is applicable for all INT dataframe 
df_squared = df.apply(yourFunction)

MODEL_PATH = os.path.expanduser("/Applications/gpt4all/models/Meta-Llama-3.1-8B-Instruct-128k-Q4_0.gguf")
TESSERACT_PATH = "/opt/homebrew/bin/tesseract"
GAME_NAME = "Heroes of Might and Magic 3"
# FANDOM_SUBDOMAIN = "witcher"

model = GPT4All(MODEL_PATH)

# ──────────────────────────────────────────────────────────────
# 🧠 GPT4All: Refine query
# ──────────────────────────────────────────────────────────────

def query_optimization(input_text):
    """Find matching titles even with extra characters in the input."""
    print(f"Input text: {input_text}")
    try:
        conn = sqlite3.connect("wiki_data.db")
        cursor = conn.cursor()
        
        # Split input text into words for better matching
        search_words = input_text.lower().split()
        
        # Step 1: Try to find titles that contain all the main words from input
        if search_words:
            # Start with the first word
            title_query = f"SELECT title FROM wiki_pages WHERE LOWER(title) LIKE ?"
            params = [f"%{search_words[0]}%"]
            
            # Add conditions for additional words
            for i in range(1, min(3, len(search_words))):  # Use up to first 3 words
                if len(search_words[i]) > 2:  # Skip very short words
                    title_query += f" AND LOWER(title) LIKE ?"
                    params.append(f"%{search_words[i]}%")
            
            cursor.execute(title_query, params)
            matches = cursor.fetchall()
            
            if matches:
                titles = [match[0] for match in matches]
                
                # If multiple matches, use GPT to find best match
                if len(titles) > 1:
                    titles_text = "\n".join(titles)
                    with model.chat_session():
                        title_prompt = (
                            f"You are helping find the most relevant wiki page. "
                            f"Which of these titles best matches the player's question?\n\n"
                            f"Player question: {input_text}\n\n"
                            f"Available titles:\n{titles_text}\n\n"
                            f"Return only the most relevant title name:"
                        )
                        best_title = model.generate(title_prompt, max_tokens=50).strip()
                else:
                    best_title = titles[0]
                
                # Get content for the selected title
                cursor.execute("SELECT content FROM wiki_pages WHERE title = ?", (best_title,))
                result = cursor.fetchone()
                if result:
                    content = result[0]
                    # Truncate content to fit within token limit
                    content = content[:1500] if len(content) > 1500 else content
                    
                    with model.chat_session():
                        answer_prompt = (
                            f"You are an in-game AI assistant. Answer this question based on the following wiki content:\n\n"
                            f"TITLE: {best_title}\n\n"
                            f"CONTENT: {content}\n\n"
                            f"Player question: {input_text}\n\n"
                            f"Provide a concise answer:"
                        )
                        response = model.generate(answer_prompt, max_tokens=300)
                        conn.close()
                        return response.strip()
        
        # Step 2: Try more aggressive search if no matches yet
        # This handles cases where all words don't match but some might
        cursor.execute("SELECT title FROM wiki_pages ORDER BY title")
        all_titles = cursor.fetchall()
        
        # Check each title for partial matches with any of the input words
        potential_matches = []
        for title_row in all_titles:
            title = title_row[0].lower()
            match_score = 0
            
            for word in search_words:
                if len(word) > 2 and word in title:  # Only count significant words
                    match_score += 1
            
            if match_score > 0:
                potential_matches.append((title_row[0], match_score))
        
        # Sort by match score (highest first)
        potential_matches.sort(key=lambda x: x[1], reverse=True)
        
        if potential_matches:
            best_title = potential_matches[0][0]
            
            # Get content for the best matching title
            cursor.execute("SELECT content FROM wiki_pages WHERE title = ?", (best_title,))
            result = cursor.fetchone()
            
            if result:
                content = result[0]
                content = content[:1500] if len(content) > 1500 else content
                
                with model.chat_session():
                    answer_prompt = (
                        f"You are an in-game AI assistant. Answer this question based on the following wiki content:\n\n"
                        f"TITLE: {best_title}\n\n"
                        f"CONTENT: {content}\n\n"
                        f"Player question: {input_text}\n\n"
                        f"Provide a concise answer:"
                    )
                    response = model.generate(answer_prompt, max_tokens=300)
                    conn.close()
                    return response.strip()
        
        # Step 3: Fallback to content search
        query_parts = []
        params = []
        
        for word in search_words:
            if len(word) > 2:  # Only use words with more than 2 characters
                query_parts.append("LOWER(content) LIKE ?")
                params.append(f"%{word}%")
        
        if query_parts:
            content_query = f"SELECT title, content FROM wiki_pages WHERE {' OR '.join(query_parts)} LIMIT 1"
            cursor.execute(content_query, params)
            content_match = cursor.fetchone()
            
            if content_match:
                title, content = content_match
                content = content[:1500] if len(content) > 1500 else content
                
                with model.chat_session():
                    prompt = (
                        f"You are an in-game AI assistant. Answer this question based on the following wiki content:\n\n"
                        f"TITLE: {title}\n\n"
                        f"CONTENT: {content}\n\n"
                        f"Player question: {input_text}\n\n"
                        f"Provide a concise answer:"
                    )
                    response = model.generate(prompt, max_tokens=300)
                    conn.close()
                    return response.strip()
        
        conn.close()
        return f"[INFO] No relevant information found for: {input_text}"

    except Exception as e:
        return f"[ERROR] Database or AI query failed: {e}"


# ──────────────────────────────────────────────────────────────
# 🧹 Clean search query for wiki compatibility
# ──────────────────────────────────────────────────────────────

def clean_query_for_fandom(raw_query, game_name):
    # print(f"Raw query: {raw_query}")
    raw = raw_query.lower()
    phrases_to_remove = [
        "how to beat", "how do i beat", "boss fight", "walkthrough",
        "strategies", "tutorial", "guide", "tips", "best way to",
        "faq", "in", "for", game_name
    ]
    for phrase in phrases_to_remove:
        raw = raw.replace(phrase, "")
    typo_fixes = {"elden rg": "elden ring", "red lion": "red lion general"}
    for typo, fix in typo_fixes.items():
        raw = raw.replace(typo, fix)
    raw = re.sub(r'[^\w\s]', '', raw)
    cleaned = ' '.join(raw.split())
    return f"{cleaned}"

# ──────────────────────────────────────────────────────────────
# 🗿 DB search
# ──────────────────────────────────────────────────────────────

def search_db(query, db_path='wiki_data.db'):
    """
    Search the SQLite database for entries matching the query.
    Returns a list of URLs similar to the search_fandom function.
    """
    # print(f"Query: {query}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT url FROM wiki_pages 
            WHERE LOWER(title) = ? 
            LIMIT 1
        """, (query.lower(),))
        
        exact_match = cursor.fetchone()
        if exact_match:
            return [exact_match[0]]
        
        like_pattern = f"%{query.lower()}%"
        cursor.execute("""
            SELECT url FROM wiki_pages 
            WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
            ORDER BY 
                CASE 
                    WHEN LOWER(title) LIKE ? THEN 1
                    ELSE 2
                END,
                LENGTH(title)
            LIMIT 2
        """, (like_pattern, like_pattern, like_pattern))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return results if results else ["[No search results found in database]"]
    
    except Exception as e:
        return [f"[ERROR] Database search failed: {e}"]

def get_page_content(url, db_path='wiki_data.db'):
    """
    Retrieve the full content for a page by its URL.
    Similar to fetching a page after finding it in search results.
    """
    # print(f"URL: {url}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT title, content FROM wiki_pages 
            WHERE url = ?
        """, (url,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            title, content = result
            return {
                "url": url,
                "title": title,
                "content": content
            }
        else:
            return {
                "url": url,
                "title": "Page not found",
                "content": "The requested page could not be found in the database."
            }
    
    except Exception as e:
        return {
            "url": url,
            "title": "Error",
            "content": f"Failed to retrieve page: {e}"
        }

def look_at_me_uwu(query):
    """
    Search the database and return content for use with model.
    This replaces the original function with the same behavior pattern.
    """
    matching_urls = search_db(query)
    
    if matching_urls and not matching_urls[0].startswith('['):
        results = []
        for url in matching_urls:
            page_data = get_page_content(url)
            results.append(page_data)
        
        formatted_content = []
        for page in results:
            formatted_content.append(f"PAGE: {page['title']}\n\n{page['content']}")
        
        return {
            "urls": matching_urls,
            "pages": results,
            "formatted_content": "\n\n---\n\n".join(formatted_content)
        }
    else:
        return {
            "urls": matching_urls,
            "pages": [],
            "formatted_content": matching_urls[0]
        }


# ──────────────────────────────────────────────────────────────
# 📸 OCR + Assistant logic triggered by keypress
# ──────────────────────────────────────────────────────────────
def do_after_window_opens():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    text = pytesseract.image_to_string("ocr_output.png", config='--psm 6').strip()
    # print("\n🖼️ OCR Text:", text)
    update_item_name(text)
    update_window_prompt_text(query_optimization(text))
    update_status()

root.after(1, do_after_window_opens)

def process_capture():
    # x, y = pyautogui.position()
    # region = {"top": y - 20, "left": x - 60, "width": 120, "height": 40}

    # with mss.mss() as sct:
    #     img = np.array(sct.grab(region))

    # pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    # text = pytesseract.image_to_string("ocr_output.png", config='--psm 6').strip()
    # print("\n🖼️ OCR Text:", text)
    root.mainloop()
    
    
    # print("🤖 Optimized Query:", refined_query)

    # search_query = clean_query_for_fandom(refined_query, GAME_NAME)
    # print("🔍 Cleaned Query:", search_query)

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
