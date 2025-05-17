import requests
from bs4 import BeautifulSoup
import sqlite3

# URL to scrape
# url = "https://mightandmagic.fandom.com/wiki/Barbarian_(H3)"
url = input()
# Connect to SQLite database
conn = sqlite3.connect('wiki_data.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS wiki_pages (
    id INTEGER PRIMARY KEY,
    url TEXT,
    title TEXT,
    content TEXT
)
''')
cursor.execute('''
CREATE VIRTUAL TABLE IF NOT EXISTS wiki_pages_fts USING fts5(title, content)
               ''')

# Scrape the page
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Extract title
title = soup.title.string

# Extract content from the main wiki content area
content_div = soup.find('div', class_='mw-parser-output')
content = ""
if content_div:
    # Remove unwanted elements
    for element in content_div.find_all(['script', 'style', 'nav', 'aside']):
        element.decompose()
    content = content_div.get_text(separator='\n', strip=True)

# Insert data into the database
cursor.execute("INSERT OR REPLACE INTO wiki_pages (url, title, content) VALUES (?, ?, ?)",
              (url, title, content))

cursor.execute("INSERT INTO wiki_pages_fts (title, content) VALUES (?, ?)", (title, content))

# Commit and close
conn.commit()
conn.close()

print(f"Scraped and stored: {title}")
print(f"Content length: {len(content)} characters")