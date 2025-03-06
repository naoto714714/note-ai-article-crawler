#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

import requests
from bs4 import BeautifulSoup


def check_note_structure():
    """noteのWebサイト構造を確認する"""

    # ヘッダー情報
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    # 検索URL
    search_url = "https://note.com/search"
    params = {"q": "AI", "page": 1}

    try:
        # 検索ページを取得
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()

        # BeautifulSoupでHTMLを解析
        soup = BeautifulSoup(response.text, "lxml")

        # タイトルを表示
        print(f"ページタイトル: {soup.title.text}")

        # 検索結果の記事リンクを探す
        print("\n=== 記事リンクの検索 ===")

        # 一般的なリンク要素を探す
        links = soup.find_all("a", href=True)
        article_links = [link for link in links if "/n/" in link.get("href")]

        print(f"'/n/'を含むリンク数: {len(article_links)}")
        if article_links:
            print("最初の5つのリンク:")
            for i, link in enumerate(article_links[:5]):
                print(f"{i + 1}. {link.get('href')} - クラス: {link.get('class')}")

        # 記事カードの構造を探す
        print("\n=== 記事カードの構造 ===")
        cards = soup.find_all("div", class_=lambda c: c and "NoteCard" in c)
        print(f"'NoteCard'を含むdiv要素数: {len(cards)}")

        if cards:
            print("最初のカードのクラス:", cards[0].get("class"))

            # カード内のリンク
            card_links = cards[0].find_all("a", href=True)
            print(f"最初のカード内のリンク数: {len(card_links)}")
            for i, link in enumerate(card_links):
                print(f"{i + 1}. {link.get('href')} - クラス: {link.get('class')}")

        # 検索結果のコンテナを探す
        print("\n=== 検索結果コンテナ ===")
        containers = soup.find_all("div", class_=lambda c: c and "SearchResult" in c)
        print(f"'SearchResult'を含むdiv要素数: {len(containers)}")

        if containers:
            print("最初のコンテナのクラス:", containers[0].get("class"))

        # JavaScriptデータを探す
        print("\n=== JavaScriptデータ ===")
        scripts = soup.find_all("script", type="application/json")
        print(f"JSONスクリプト数: {len(scripts)}")

        if scripts:
            for i, script in enumerate(scripts):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        print(f"スクリプト {i + 1} のキー: {list(data.keys())}")

                        # 記事データを探す
                        if "props" in data and "pageProps" in data["props"]:
                            page_props = data["props"]["pageProps"]
                            print(f"pagePropsのキー: {list(page_props.keys())}")

                            # 検索結果を探す
                            if "searchResult" in page_props:
                                search_result = page_props["searchResult"]
                                print(f"searchResultのキー: {list(search_result.keys())}")

                                if "notes" in search_result:
                                    notes = search_result["notes"]
                                    print(f"記事数: {len(notes)}")
                                    if notes:
                                        print(f"最初の記事のキー: {list(notes[0].keys())}")
                                        print(f"最初の記事のURL: {notes[0].get('noteUrl')}")
                except Exception as e:
                    print(f"スクリプト {i + 1} の解析エラー: {e}")

    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    check_note_structure()
