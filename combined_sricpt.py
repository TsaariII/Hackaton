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

# ──────────────────────────────────────────────────────────────
# 🔧 Configuration
# ──────────────────────────────────────────────────────────────



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
    typo_fixes = {"elden rg": "elden ring", "red lion": "red lion general"}
    for typo, fix in typo_fixes.items():
        raw = raw.replace(typo, fix)
    raw = re.sub(r'[^\w\s]', '', raw)
    cleaned = ' '.join(raw.split())
    return f"{cleaned}"

# ──────────────────────────────────────────────────────────────
# 🌐 Fandom Wiki Search
# ──────────────────────────────────────────────────────────────

MODEL_PATH = os.path.expanduser("/home/fdessoy/.local/share/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf")
TESSERACT_PATH = "/opt/homebrew/bin/tesseract"
GAME_NAME = "Witcher 3"
FANDOM_SUBDOMAIN = "witcher"

def search_fandom(query, game_subdomain=FANDOM_SUBDOMAIN):
    """Search directly on a specific game's Fandom wiki via its internal search page."""
    try:
        search_url = f"https://{game_subdomain}.fandom.com/wiki/Special:Search?query={query.replace(' ', '+')}&limit=5"
        print(f"🔍 Searching: {search_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(search_url, headers=headers, allow_redirects=True)
        soup = BeautifulSoup(response.text, 'html.parser')

        # ✅ Detect redirect directly to article
        if response.url.startswith(f"https://{game_subdomain}.fandom.com/wiki/") and "Special:Search" not in response.url:
            return [response.url]

        # ✅ Fallback: parse search result list
        links = []
        for a in soup.select('a.mw-search-result-heading'):
            href = a.get('href')
            if href and href.startswith("/wiki/"):
                full_url = f"https://{game_subdomain}.fandom.com{href}"
                links.append(full_url)

        return links[:2] if links else ["[No search results found on Fandom]"]
    except Exception as e:
        return [f"[ERROR] Fandom direct search failed: {e}"]



def search_db(query, db_path='wiki_data.db'):
    """
    Search the SQLite database for entries matching the query.
    Returns a list of URLs similar to the search_fandom function.
    """
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

    fandom_results = look_at_me_uwu(search_query)
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
