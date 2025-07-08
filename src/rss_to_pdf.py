import feedparser
import requests
from bs4 import BeautifulSoup
from jinja2 import Template
from weasyprint import HTML
import json
import os
import datetime
import dropbox

# === HENT KONFIGURASJON ===
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

today = datetime.date.today().strftime("%d.%m.%y")
output_pdf = f"KopperstadNytt - {today}.pdf"

# === HJELPEFUNKSJONER ===
def fetch_full_article(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html5lib')
        paragraphs = soup.find_all('p')
        text = "\n\n".join(p.get_text() for p in paragraphs if len(p.get_text()) > 50)
        return text.strip()
    except Exception as e:
        return f"[Fulltekst ikke tilgjengelig: {e}]"

# === LES RSS ===
all_articles = []
for kategori in config["Kategorier"]:
    entries = []
    for feed_url in kategori["kilder"]:
        d = feedparser.parse(feed_url)
        for entry in d.entries[:10]:
            full = fetch_full_article(entry.link)
            entries.append({
                "title": entry.title,
                "link": entry.link,
                "full": full
            })
    all_articles.append({
        "name": kategori["navn"],
        "entries": entries[:10]
    })

# === RENDER PDF ===
with open("src/layout.html", encoding="utf-8") as f:
    template = Template(f.read())

html_out = template.render(articles=all_articles, now=datetime.datetime.now())
HTML(string=html_out).write_pdf(output_pdf)

# === DROPPBOX-UPPLASTING ===
token = os.getenv("DROPBOX_TOKEN")
if token:
    dbx = dropbox.Dropbox(token)
    with open(output_pdf, "rb") as f:
        dbx.files_upload(f.read(), f"/{output_pdf}", mode=dropbox.files.WriteMode.overwrite)
