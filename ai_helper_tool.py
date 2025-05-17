import os
import re
import requests
from bs4 import BeautifulSoup
import yt_dlp
from urllib.parse import urlparse, parse_qs
from gpt4all import GPT4All

# Specify the path to your downloaded GPT4All model
MODEL_PATH = os.path.expanduser("/Applications/gpt4all/models/Meta-Llama-3.1-8B-Instruct-128k-Q4_0.gguf")

def query_optimization(input_text):
    """You are an in-game AI assistant. Turn vague gamer questions into short, fandom-compatible search queries using game names, boss names, or item names. Avoid extra explanation."""
    try:
        model = GPT4All(MODEL_PATH)
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
    
def clean_query_for_fandom(raw_query, game_name):
    """Normalize and simplify search queries for game-specific Fandom wiki search."""
    raw = raw_query.lower()

    # Remove common fluff
    phrases_to_remove = [
        "how to beat", "how do i beat", "boss fight", "walkthrough",
        "strategies", "tutorial", "guide", "tips", "best way to",
        "faq", "in", "for", game_name
    ]
    for phrase in phrases_to_remove:
        raw = raw.replace(phrase, "")

    # Fix minor typos or autocorrections
    typo_fixes = {
        "elden rg": "elden ring",
        "red lion": "red lion general",  # if you want to guide it further
    }
    for typo, fix in typo_fixes.items():
        raw = raw.replace(typo, fix)

    # Remove quotes and non-word characters
    raw = re.sub(r'[^\w\s]', '', raw)

    # Normalize whitespace
    cleaned = ' '.join(raw.split())

    # Prepend game name again (once)
    return f"{cleaned}"

def search_fandom(query, game_subdomain="eldenring"):
    """Search directly on a specific game's Fandom wiki via its internal search page."""
    try:
        search_url = f"https://{game_subdomain}.fandom.com/wiki/Special:Search?query={query.replace(' ', '+')}&limit=5"
        print(f"Searching: {search_url}")
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

def search_youtube(query):
    """Search YouTube using yt_dlp and return video titles and URLs."""
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            results = ydl.extract_info(f"ytsearch2:{query}", download=False)['entries']
            return [(vid['title'], vid['webpage_url']) for vid in results]
    except Exception as e:
        return [(f"[ERROR] YouTube search failed: {e}", "")]

def run_assistant(player_input):
    print(f"\nPlayer Input: {player_input}")
    print("Optimizing query with GPT4All...")
    refined_query = query_optimization(player_input)
    # print(f"Refined Query: {refined_query}\n")
    print("Searching Fandom...")
    search_query = clean_query_for_fandom(refined_query, game_name="elden ring")
    print(f"Search Query: {search_query}\n")
    fandom_results = search_fandom(search_query, game_subdomain="eldenring")
    for i, link in enumerate(fandom_results, 1):
        print(f"Fandom Result {i}: {link}")

    # print("\nSearching YouTube...")
    # youtube_results = search_youtube(refined_query)
    # for i, (title, url) in enumerate(youtube_results, 1):
    #     print(f"YouTube Video {i}: {title}\nURL: {url}")

# Example usage
if __name__ == "__main__":
    run_assistant("how do I beat the red lion in elden ring")