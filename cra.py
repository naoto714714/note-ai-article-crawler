import requests
from bs4 import BeautifulSoup

params = {"f": "new", "paid_only": "false", "page": "50000"}
search_url = "https://note.com/hashtag/AI"

response = requests.get(search_url, params=params)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")
print(soup)

# soupをファイルに保存
with open("soup.html", "w") as f:
    f.write(soup.prettify())

# 現在のnoteのWebサイト構造に合わせて記事リンクを取得
article_links = soup.find_all("a", class_=["a-link", "m-largeNoteWrapper__link", "fn"])

# 記事リンクをファイルに保存
with open("article_links.txt", "w") as f:
    for link in article_links:
        f.write(link.get("href") + "\n")

# 記事リンクをファイルに保存
with open("article_links.txt", "w") as f:
    for link in article_links:
        f.write(link.get("href") + "\n")
