#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import random
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class NoteAICrawler:
    def __init__(self, search_keyword="AI", max_pages=5, output_dir="output"):
        """
        noteからAI関連の記事をクロールするクラス

        Args:
            search_keyword (str): 検索キーワード
            max_pages (int): クロールする最大ページ数
            output_dir (str): 出力ディレクトリ
        """
        self.base_url = "https://note.com"
        self.search_url = f"{self.base_url}/search"
        self.search_keyword = search_keyword
        self.max_pages = max_pages
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
        self.articles = []

        # 出力ディレクトリの作成
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def search_articles(self):
        """検索ページから記事のリンクを取得"""
        print(f"「{self.search_keyword}」に関する記事を検索中...")

        for page in tqdm(range(1, self.max_pages + 1), desc="ページ"):
            try:
                params = {"q": self.search_keyword, "page": page}

                response = requests.get(self.search_url, params=params, headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # 現在のnoteのWebサイト構造に合わせて記事リンクを取得
                article_links = soup.find_all("a", class_=["a-link", "m-largeNoteWrapper__link", "fn"])

                if not article_links:
                    # クラス名での検索がうまくいかない場合は、パスで検索
                    article_links = [link for link in soup.find_all("a", href=True) if "/n/" in link.get("href")]

                if not article_links:
                    print(f"ページ {page} に記事が見つかりませんでした。終了します。")
                    break

                for link in article_links:
                    article_url = link.get("href")
                    if article_url:
                        # 検索結果ページや無効なURLは除外
                        if "search?" in article_url or article_url == "#" or "help-note.com" in article_url:
                            continue

                        # 相対パスの場合は絶対パスに変換
                        if article_url.startswith("/"):
                            article_url = self.base_url + article_url

                        # 既に取得済みのURLでなければリストに追加
                        if article_url not in [a["url"] for a in self.articles]:
                            # 検索結果ページから記事のタイトルを取得
                            title_elem = link.find("h3") or link.find(
                                "div", class_=lambda c: c and "title" in c.lower()
                            )
                            title = title_elem.text.strip() if title_elem else ""

                            self.articles.append({"url": article_url, "title_from_search": title})

                # サーバーに負荷をかけないよう少し待機
                time.sleep(random.uniform(1.0, 3.0))

            except Exception as e:
                print(f"ページ {page} の取得中にエラーが発生しました: {e}")
                continue

        print(f"合計 {len(self.articles)} 件の記事が見つかりました。")

    def get_article_details(self):
        """各記事の詳細情報を取得"""
        print("記事の詳細情報を取得中...")

        for i, article in enumerate(tqdm(self.articles, desc="記事")):
            try:
                # URLが無効な場合はスキップ
                if article["url"] == "#" or "help-note.com" in article["url"] or "search?" in article["url"]:
                    self.articles[i].update(
                        {
                            "title": article.get("title_from_search", "無効なURL"),
                            "author": "不明",
                            "published_date": None,
                            "likes": "0",
                            "tags": [],
                            "content_preview": "無効なURLのため取得できませんでした",
                        }
                    )
                    continue

                response = requests.get(article["url"], headers=self.headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # 記事の各要素を取得
                title = self._get_title(soup, article)
                author = self._get_author(soup, article)
                published_date = self._get_published_date(soup)
                likes = self._get_likes(soup)
                tags = self._get_tags(soup)
                content_preview = self._get_content_preview(soup)

                # 記事情報を更新
                self.articles[i].update(
                    {
                        "title": title,
                        "author": author,
                        "published_date": published_date,
                        "likes": likes,
                        "tags": tags,
                        "content_preview": content_preview,
                    }
                )

                # サーバーに負荷をかけないよう少し待機
                time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                print(f"記事 {article['url']} の詳細取得中にエラーが発生しました: {e}")
                self.articles[i].update(
                    {
                        "title": article.get("title_from_search", "取得エラー"),
                        "author": "不明",
                        "published_date": None,
                        "likes": "0",
                        "tags": [],
                        "content_preview": f"エラーにより取得できませんでした: {str(e)}",
                    }
                )

    def _get_title(self, soup, article):
        """記事のタイトルを取得する"""
        title = article.get("title_from_search", "")

        # 複数のパターンを試す
        try:
            # パターン1: o-noteContentHeader__title クラスのh1タグ
            title_elem = soup.select_one("h1.o-noteContentHeader__title")
            if title_elem and title_elem.text.strip():
                return title_elem.text.strip()
        except (AttributeError, TypeError):
            pass

        try:
            # パターン2: メタタグ
            meta_title = soup.find("meta", property="og:title")
            if meta_title:
                title_text = meta_title.get("content", "")
                # "｜note"や"｜著者名"などの部分を削除
                return re.sub(r"[\s\|｜].*$", "", title_text)
        except (AttributeError, TypeError):
            pass

        try:
            # パターン3: titleタグ
            title_elem = soup.title
            if title_elem:
                title_text = title_elem.text.strip()
                # "｜note"や"｜著者名"などの部分を削除
                return re.sub(r"[\s\|｜].*$", "", title_text)
        except (AttributeError, TypeError):
            pass

        try:
            # パターン4: 任意のh1タグ
            h1_elems = soup.find_all("h1")
            for h1 in h1_elems:
                if h1 and hasattr(h1, "text") and h1.text.strip():
                    return h1.text.strip()
        except (AttributeError, TypeError):
            pass

        try:
            # パターン5: URLからスラッグを抽出して、タイトルとして使用
            url_parts = article["url"].split("/")
            if len(url_parts) > 0:
                slug = url_parts[-1]
                # スラッグをタイトルらしい形式に変換（ハイフンをスペースに置換など）
                return slug.replace("-", " ").replace("_", " ").replace("n", "")
        except Exception:
            pass

        return title or "タイトル不明"

    def _get_author(self, soup, article):
        """記事の著者を取得する"""
        try:
            # パターン1: data-note-user-name属性
            author_elem = soup.select_one("a[data-note-user-name]")
            if author_elem:
                return author_elem.get("data-note-user-name")
        except (AttributeError, TypeError):
            pass

        try:
            # パターン2: URLから著者名を抽出
            author_match = re.search(r"note\.com/([^/]+)", article["url"])
            if author_match:
                return author_match.group(1)
        except Exception:
            pass

        try:
            # パターン3: メタタグから著者名を抽出
            meta_author = soup.find("meta", property="og:site_name")
            if meta_author:
                author_text = meta_author.get("content", "")
                if author_text and author_text != "note":
                    return author_text
        except (AttributeError, TypeError):
            pass

        return "著者不明"

    def _get_published_date(self, soup):
        """記事の投稿日を取得する"""
        try:
            date_elem = soup.select_one("time")
            if date_elem:
                return date_elem.get("datetime")
        except (AttributeError, TypeError):
            pass
        return None

    def _get_likes(self, soup):
        """記事のいいね数を取得する"""
        try:
            # パターン1: data-like-count属性
            like_elem = soup.select_one("button[data-like-count]")
            if like_elem:
                return like_elem.get("data-like-count")
        except (AttributeError, TypeError):
            pass

        try:
            # パターン2: o-noteContentHeader__titleAttachment クラスの要素
            like_elem = soup.select_one(".o-noteContentHeader__titleAttachment")
            if like_elem:
                like_text = like_elem.text.strip()
                like_match = re.search(r"\d+", like_text)
                if like_match:
                    return like_match.group(0)
        except (AttributeError, TypeError):
            pass

        try:
            # パターン3: likeやheartを含むクラス名の要素
            like_text_elem = soup.select_one(
                "span[class*='like'], div[class*='like'], span[class*='heart'], div[class*='heart']"
            )
            if like_text_elem:
                like_text = like_text_elem.text.strip()
                like_match = re.search(r"\d+", like_text)
                if like_match:
                    return like_match.group(0)
        except (AttributeError, TypeError):
            pass

        return "0"

    def _get_tags(self, soup):
        """記事のタグを取得する"""
        tags = []

        try:
            # パターン1: /hashtag/へのリンク
            tags_elems = soup.select("a[href^='/hashtag/']")
            if tags_elems:
                return [tag.text.strip() for tag in tags_elems if tag.text.strip()]
        except (AttributeError, TypeError):
            pass

        try:
            # パターン2: tagを含むクラス名の要素
            tags_elems = soup.select("a[class*='tag'], span[class*='tag']")
            if tags_elems:
                return [tag.text.strip() for tag in tags_elems if tag.text.strip()]
        except (AttributeError, TypeError):
            pass

        return tags

    def _get_content_preview(self, soup):
        """記事の本文プレビューを取得する"""
        try:
            # 複数のパターンを試す
            content_elems = soup.select(
                "div.note-common-styles__textnote-body p, div[class*='styles__text'] p, article p"
            )
            if content_elems:
                return "\n".join([p.text.strip() for p in content_elems[:3] if p.text.strip()])
        except (AttributeError, TypeError):
            pass

        return ""

    def filter_ai_articles(self):
        """AI関連の記事のみをフィルタリング"""
        ai_keywords = [
            "AI",
            "人工知能",
            "機械学習",
            "ディープラーニング",
            "ChatGPT",
            "GPT",
            "生成AI",
            "強化学習",
            "自然言語処理",
            "NLP",
            "OpenAI",
            "Claude",
            "Gemini",
            "LLM",
            "大規模言語モデル",
        ]

        filtered_articles = []

        for article in self.articles:
            # タイトル、タグ、本文のいずれかにAI関連キーワードが含まれているか確認
            title = article.get("title", "").lower()
            tags = [tag.lower() for tag in article.get("tags", [])]
            content = article.get("content_preview", "").lower()

            is_ai_related = False
            for keyword in ai_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in title or any(keyword_lower in tag for tag in tags) or keyword_lower in content:
                    is_ai_related = True
                    break

            if is_ai_related:
                filtered_articles.append(article)

        print(f"AI関連の記事は {len(filtered_articles)}/{len(self.articles)} 件でした。")
        self.articles = filtered_articles

    def save_results(self):
        """結果をCSVとJSONで保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 不要なフィールドを削除
        for article in self.articles:
            if "title_from_search" in article:
                del article["title_from_search"]

        # CSVとして保存
        df = pd.DataFrame(self.articles)
        csv_path = os.path.join(self.output_dir, f"note_ai_articles_{timestamp}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # JSONとして保存
        json_path = os.path.join(self.output_dir, f"note_ai_articles_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)

        print(f"結果を保存しました:")
        print(f"- CSV: {csv_path}")
        print(f"- JSON: {json_path}")

    def run(self):
        """クローラーを実行"""
        self.search_articles()
        if self.articles:
            self.get_article_details()
            self.filter_ai_articles()
            self.save_results()
            return True
        return False


if __name__ == "__main__":
    # クローラーの設定
    search_keyword = "AI"  # 検索キーワード
    max_pages = 5  # 検索する最大ページ数
    output_dir = "output"  # 出力ディレクトリ

    # クローラーの実行
    crawler = NoteAICrawler(search_keyword=search_keyword, max_pages=max_pages, output_dir=output_dir)

    crawler.run()
