# src/rss_to_pdf.py

import feedparser
import requests
from bs4 import BeautifulSoup

# --- RSS-kilder per kategori ---
FEEDS = {
    "Norske nyheter": [
        "https://www.nrk.no/toppsaker.rss",
        "https://www.tv2.no/rss/nyheter",
    ],
    "Teknologi": [
        "https://www.tu.no/rss",
    ],
    "Rock": [
        "https://www.blabbermouth.net/feed/"
    ]
}

def fetch_full_article(url):
    """Hent full artikkeltekst fra gitt URL. Returnerer plaintext-streng."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Fjern script/style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Heuristikk for å hente hovedinnholdet
        article_tags = soup.find_all(["p", "h2"])
        article_text = "\n\n".join([tag.get_text(strip=True) for tag in article_tags if tag.get_text(strip=True)])
        return article_text if article_text else "⚠️ Fant ingen artikkeltekst."
    except Exception as e:
        return f"⚠️ Feil ved henting: {str(e)}"

# --- Hovedprosess: Hent alle artikler strukturert ---
all_articles = []

for category, urls in FEEDS.items():
    entries = []
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = getattr(entry, 'link', None)
            title = getattr(entry, 'title', "(Uten tittel)")

            if not link:
                print(f"⚠️ RSS-artikkel mangler link: {title}")
                full = "⚠️ Ingen lenke tilgjengelig for full artikkel."
            else:
                full = fetch_full_article(link)

            entries.append({
                "title": title,
                "full": full
            })

    all_articles.append({
        "name": category,
        "entries": entries
    })

# Midlertidig utskrift for kontroll
if __name__ == "__main__":
    for section in all_articles:
        print(f"\n=== {section['name']} ===")
        for article in section["entries"]:
            print(f" - {article['title']}\n   {article['full'][:150]}...\n")
