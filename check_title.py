#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup


def check_title():
    """特定の記事ページのHTMLを解析して、タイトル要素を確認する"""

    url = "https://note.com/goto_finance/n/n2edf753c0fe5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # titleタグ
        print("Title tag:", soup.title.text)

        # h1タグ
        print("\nH1 tags:")
        for h1 in soup.find_all("h1"):
            print(f"- {h1.text.strip()}")
            print(f"  Classes: {h1.get('class')}")

        # メタタグ
        print("\nMeta tags:")
        for meta in soup.find_all("meta", property=["og:title", "twitter:title"]):
            print(f"- {meta.get('property')}: {meta.get('content')}")

        # 特定のクラス名を持つ要素
        print("\nElements with 'title' in class name:")
        for elem in soup.find_all(class_=lambda c: c and "title" in c.lower()):
            print(f"- Tag: {elem.name}, Text: {elem.text.strip()}")
            print(f"  Classes: {elem.get('class')}")

        # JavaScriptデータ
        print("\nJSON data:")
        for script in soup.find_all("script", type="application/json"):
            print(f"- Script ID: {script.get('id')}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    check_title()
