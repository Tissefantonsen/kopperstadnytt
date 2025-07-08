import feedparser
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
from weasyprint import HTML
import dropbox
import os
from datetime import datetime

# Hent token fra GitHub Secrets
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

# RSS-feeder gruppert i kategorier
FEEDS = {
    "Norske nyheter": [
        "https://www.nrk.no/toppsaker.rss",
        "https://www.tv2.no/rss/section/nyhetene"
    ],
    "Tekniske nyheter": [
        "https://www.tu.no/static/rss.php"
    ],
    "Rockenyheter": [
        "https://www.blabbermouth.net/feed/"
    ]
}

# Hjelpefunksjon for å hente full artikkeltekst fra lenke
def fetch_full_article(url):
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        # Eksempel: NRK
        if "nrk.no" in url:
            content_div = soup.find('div', class_='article-body') or soup.find('article')
        # Eksempel: TV2
        elif "tv2.no" in url:
            content_div = soup.find('div', class_='article-body') or soup.find('article')
        # TU
        elif "tu.no" in url:
            content_div = soup.find('div', class_='ArticleBody') or soup.find('article')
        # Blabbermouth
        elif "blabbermouth" in url:
            content_div = soup.find('div', class_='td-post-content') or soup.find('article')
        else:
            content_div = soup.find('article') or soup.find('div')

        if not content_div:
            return "Fant ikke hovedinnhold."

        paragraphs = [p.get_text(strip=True) for p in content_div.find_all(['p', 'h3'])]
        return '\n\n'.join([p for p in paragraphs if p])
    except Exception as e:
        return f"Feil ved henting av artikkel: {e}"

# Bygg artikkelstruktur
all_articles = []

for category in FEEDS:
    entries = []
    for url in FEEDS[category]:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link = getattr(entry, 'link', None)
            if link:
                full = fetch_full_article(link)
            else:
                print(f"Advarsel: RSS-artikkel mangler link: {entry.title}")
                full = entry.get("summary", "Ingen artikkeltekst tilgjengelig.")

            entries.append({
                "title": entry.title,
                "full": full
            })
    all_articles.append({
        "name": category,
        "entries": entries[:10]  # maks 10 artikler per kategori
    })

# Generer HTML via Jinja2
with open("src/layout.html", encoding="utf-8") as f:
    template = Template(f.read())
    html_out = template.render(articles=all_articles, now=datetime.now())

# Lagre som PDF
pdf_file = f"KopperstadNytt - {datetime.now().strftime('%d.%m.%y')}.pdf"
HTML(string=html_out).write_pdf(pdf_file)

# Last opp til Dropbox hvis token finnes
if DROPBOX_TOKEN:
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    dropbox_path = f"/{pdf_file}"
    with open(pdf_file, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
    print(f"PDF lastet opp til Dropbox: {dropbox_path}")
else:
    print("Dropbox-token ikke satt. Hopper over opplasting.")

print(f"✅ Ferdig: {pdf_file}")
