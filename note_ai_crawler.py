#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import random
import re
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class NoteAICrawler:
    # 各要素の取得に使用するセレクタを定数として定義
    TITLE_SELECTORS = [
        "h1.o-noteContentHeader__title",  # パターン1: o-noteContentHeader__title クラスのh1タグ
        "meta[property='og:title']",  # パターン2: メタタグ
        "title",  # パターン3: titleタグ
        "h1",  # パターン4: 任意のh1タグ
    ]

    AUTHOR_SELECTORS = [
        "a[data-note-user-name]",  # パターン1: data-note-user-name属性
        "meta[property='og:site_name']",  # パターン3: メタタグから著者名を抽出
    ]

    LIKES_SELECTORS = [
        "button[data-like-count]",  # パターン1: data-like-count属性
        ".o-noteContentHeader__titleAttachment",  # パターン2: o-noteContentHeader__titleAttachment クラスの要素
        "span[class*='like'], div[class*='like'], span[class*='heart'], div[class*='heart']",  # パターン3: likeやheartを含むクラス名の要素
    ]

    TAGS_SELECTORS = [
        "a[href^='/hashtag/']",  # パターン1: /hashtag/へのリンク
        "a[class*='tag'], span[class*='tag']",  # パターン2: tagを含むクラス名の要素
    ]

    CONTENT_SELECTORS = [
        "div.note-common-styles__textnote-body p, div[class*='styles__text'] p, article p"  # 複数のパターンを試す
    ]

    # AI関連キーワード
    AI_KEYWORDS = [
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

    def __init__(
        self,
        search_keyword="AI",
        max_pages=5,
        output_dir="output",
        min_wait=1.0,
        max_wait=3.0,
        detail_min_wait=2.0,
        detail_max_wait=4.0,
        yesterday_only=False,
    ):
        """
        noteからAI関連の記事をクロールするクラス

        Args:
            search_keyword (str): 検索キーワード
            max_pages (int): クロールする最大ページ数
            output_dir (str): 出力ディレクトリ
            min_wait (float): 検索時の最小待機時間（秒）
            max_wait (float): 検索時の最大待機時間（秒）
            detail_min_wait (float): 詳細取得時の最小待機時間（秒）
            detail_max_wait (float): 詳細取得時の最大待機時間（秒）
            yesterday_only (bool): 昨日の記事のみを取得するかどうか
        """
        self.base_url = "https://note.com"
        self.search_url = f"{self.base_url}/search"
        self.search_keyword = search_keyword
        self.max_pages = max_pages
        self.output_dir = output_dir
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.detail_min_wait = detail_min_wait
        self.detail_max_wait = detail_max_wait
        self.yesterday_only = yesterday_only
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
                # 新しい順に記事を取得するためのパラメータを追加
                params = {
                    "q": self.search_keyword, 
                    "page": page,
                    "sort": "new"  # 新しい順に記事を取得
                }

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
                time.sleep(random.uniform(self.min_wait, self.max_wait))

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
                time.sleep(random.uniform(self.detail_min_wait, self.detail_max_wait))

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

        # パターン1: o-noteContentHeader__title クラスのh1タグ
        try:
            title_elem = soup.select_one(self.TITLE_SELECTORS[0])
            if title_elem and title_elem.text.strip():
                return title_elem.text.strip()
        except (AttributeError, TypeError) as e:
            print(f"タイトル取得パターン1でエラー: {e}")

        # パターン2: メタタグ
        try:
            meta_title = soup.find("meta", property="og:title")
            if meta_title:
                title_text = meta_title.get("content", "")
                # "｜note"や"｜著者名"などの部分を削除
                return re.sub(r"[\s\|｜].*$", "", title_text)
        except (AttributeError, TypeError) as e:
            print(f"タイトル取得パターン2でエラー: {e}")

        # パターン3: titleタグ
        try:
            title_elem = soup.title
            if title_elem:
                title_text = title_elem.text.strip()
                # "｜note"や"｜著者名"などの部分を削除
                return re.sub(r"[\s\|｜].*$", "", title_text)
        except (AttributeError, TypeError) as e:
            print(f"タイトル取得パターン3でエラー: {e}")

        # パターン4: 任意のh1タグ
        try:
            h1_elems = soup.find_all("h1")
            for h1 in h1_elems:
                if h1 and hasattr(h1, "text") and h1.text.strip():
                    return h1.text.strip()
        except (AttributeError, TypeError) as e:
            print(f"タイトル取得パターン4でエラー: {e}")

        # パターン5: URLからスラッグを抽出して、タイトルとして使用
        try:
            url_parts = article["url"].split("/")
            if len(url_parts) > 0:
                slug = url_parts[-1]
                # スラッグをタイトルらしい形式に変換（ハイフンをスペースに置換など）
                return slug.replace("-", " ").replace("_", " ").replace("n", "")
        except Exception as e:
            print(f"タイトル取得パターン5でエラー: {e}")

        return title or "タイトル不明"

    def _get_author(self, soup, article):
        """記事の著者を取得する"""
        # パターン1: data-note-user-name属性
        try:
            author_elem = soup.select_one(self.AUTHOR_SELECTORS[0])
            if author_elem:
                return author_elem.get("data-note-user-name")
        except (AttributeError, TypeError) as e:
            print(f"著者取得パターン1でエラー: {e}")

        # パターン2: URLから著者名を抽出
        try:
            author_match = re.search(r"note\.com/([^/]+)", article["url"])
            if author_match:
                return author_match.group(1)
        except Exception as e:
            print(f"著者取得パターン2でエラー: {e}")

        # パターン3: メタタグから著者名を抽出
        try:
            meta_author = soup.find("meta", property="og:site_name")
            if meta_author:
                author_text = meta_author.get("content", "")
                if author_text and author_text != "note":
                    return author_text
        except (AttributeError, TypeError) as e:
            print(f"著者取得パターン3でエラー: {e}")

        return "著者不明"

    def _get_published_date(self, soup):
        """記事の投稿日を取得する"""
        try:
            date_elem = soup.select_one("time")
            if date_elem:
                return date_elem.get("datetime")
        except (AttributeError, TypeError) as e:
            print(f"投稿日取得でエラー: {e}")
        return None

    def _get_likes(self, soup):
        """記事のいいね数を取得する"""
        # パターン1: data-like-count属性
        try:
            like_elem = soup.select_one(self.LIKES_SELECTORS[0])
            if like_elem:
                return like_elem.get("data-like-count")
        except (AttributeError, TypeError) as e:
            print(f"いいね数取得パターン1でエラー: {e}")

        # パターン2: o-noteContentHeader__titleAttachment クラスの要素
        try:
            like_elem = soup.select_one(self.LIKES_SELECTORS[1])
            if like_elem:
                like_text = like_elem.text.strip()
                like_match = re.search(r"\d+", like_text)
                if like_match:
                    return like_match.group(0)
        except (AttributeError, TypeError) as e:
            print(f"いいね数取得パターン2でエラー: {e}")

        # パターン3: likeやheartを含むクラス名の要素
        try:
            like_text_elem = soup.select_one(self.LIKES_SELECTORS[2])
            if like_text_elem:
                like_text = like_text_elem.text.strip()
                like_match = re.search(r"\d+", like_text)
                if like_match:
                    return like_match.group(0)
        except (AttributeError, TypeError) as e:
            print(f"いいね数取得パターン3でエラー: {e}")

        return "0"

    def _get_tags(self, soup):
        """記事のタグを取得する"""
        tags = []

        # パターン1: /hashtag/へのリンク
        try:
            tags_elems = soup.select(self.TAGS_SELECTORS[0])
            if tags_elems:
                return [tag.text.strip() for tag in tags_elems if tag.text.strip()]
        except (AttributeError, TypeError) as e:
            print(f"タグ取得パターン1でエラー: {e}")

        # パターン2: tagを含むクラス名の要素
        try:
            tags_elems = soup.select(self.TAGS_SELECTORS[1])
            if tags_elems:
                return [tag.text.strip() for tag in tags_elems if tag.text.strip()]
        except (AttributeError, TypeError) as e:
            print(f"タグ取得パターン2でエラー: {e}")

        return tags

    def _get_content_preview(self, soup):
        """記事の本文プレビューを取得する"""
        try:
            # 複数のパターンを試す
            content_elems = soup.select(self.CONTENT_SELECTORS[0])
            if content_elems:
                return "\n".join([p.text.strip() for p in content_elems[:3] if p.text.strip()])
        except (AttributeError, TypeError) as e:
            print(f"本文プレビュー取得でエラー: {e}")

        return ""

    def filter_ai_articles(self):
        """AI関連の記事のみをフィルタリング"""
        filtered_articles = []

        for article in self.articles:
            # タイトル、タグ、本文のいずれかにAI関連キーワードが含まれているか確認
            title = article.get("title", "").lower()
            tags = [tag.lower() for tag in article.get("tags", [])]
            content = article.get("content_preview", "").lower()

            is_ai_related = False
            for keyword in self.AI_KEYWORDS:
                keyword_lower = keyword.lower()
                if keyword_lower in title or any(keyword_lower in tag for tag in tags) or keyword_lower in content:
                    is_ai_related = True
                    break

            if is_ai_related:
                filtered_articles.append(article)

        print(f"AI関連の記事は {len(filtered_articles)}/{len(self.articles)} 件でした。")
        self.articles = filtered_articles

    def filter_yesterday_articles(self):
        """昨日の記事のみをフィルタリング"""
        if not self.yesterday_only:
            return

        # 昨日の日付を取得
        yesterday = (datetime.now() - timedelta(days=1)).date()
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        
        filtered_articles = []
        
        print(f"昨日（{yesterday_str}）の記事のみをフィルタリングします...")
        
        for article in self.articles:
            # 投稿日を取得
            published_date = article.get("published_date")
            if published_date:
                try:
                    # 投稿日時文字列をdatetimeオブジェクトに変換し、日付部分のみを取得
                    published_date_obj = datetime.fromisoformat(published_date.replace("Z", "+00:00")).date()
                    
                    # 昨日の記事のみをフィルタリング
                    if published_date_obj == yesterday:
                        filtered_articles.append(article)
                except (ValueError, TypeError) as e:
                    print(f"投稿日の解析中にエラー: {e}")
        
        print(f"昨日の記事は {len(filtered_articles)}/{len(self.articles)} 件でした。")
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
            # 昨日の記事のみをフィルタリング
            if self.yesterday_only:
                self.filter_yesterday_articles()
            self.filter_ai_articles()
            self.save_results()
            return True
        return False


if __name__ == "__main__":
    # クローラーの設定
    search_keyword = "AI"  # 検索キーワード
    max_pages = 5  # 検索する最大ページ数
    output_dir = "output"  # 出力ディレクトリ
    yesterday_only = True  # 昨日の記事のみを取得

    # クローラーの実行
    crawler = NoteAICrawler(
        search_keyword=search_keyword,
        max_pages=max_pages,
        output_dir=output_dir,
        min_wait=1.0,
        max_wait=3.0,
        detail_min_wait=2.0,
        detail_max_wait=4.0,
        yesterday_only=yesterday_only,
    )

    crawler.run()