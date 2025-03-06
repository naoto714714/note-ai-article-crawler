# Note AI記事クローラー

このプロジェクトは、Webサイト「note」からAI関連の記事を自動的に収集するクローラーです。

## 機能

- noteの検索機能を使用してAI関連の記事を検索
- 記事のタイトル、著者、投稿日、いいね数、タグ、本文の一部を取得
- AI関連キーワードによるフィルタリング
- 結果をCSVとJSONファイルで保存

## 必要条件

- Python 3.7以上
- 必要なライブラリ（requirements.txtに記載）

## インストール方法

1. リポジトリをクローン、またはダウンロードします。

```bash
git clone https://github.com/yourusername/note-ai-crawler.git
cd note-ai-crawler
```

2. 必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

## 使い方

基本的な使い方:

```bash
python note_ai_crawler.py
```

デフォルトでは、以下の設定で実行されます:
- 検索キーワード: "AI"
- 検索ページ数: 5ページ
- 出力ディレクトリ: "output"

### カスタマイズ

スクリプト内の以下の部分を編集することで、設定を変更できます:

```python
if __name__ == "__main__":
    # クローラーの設定
    search_keyword = "AI"  # 検索キーワード
    max_pages = 5  # 検索する最大ページ数
    output_dir = "output"  # 出力ディレクトリ

    # クローラーの実行
    crawler = NoteAICrawler(
        search_keyword=search_keyword,
        max_pages=max_pages,
        output_dir=output_dir
    )

    crawler.run()
```

### フィルタリングキーワードの変更

AI関連記事のフィルタリングに使用するキーワードは、`filter_ai_articles`メソッド内の`ai_keywords`リストで定義されています。必要に応じて編集してください。

## 注意事項

- Webスクレイピングを行う際は、対象サイトの利用規約を遵守してください。
- サーバーに過度な負荷をかけないよう、リクエスト間に適切な待機時間を設けています。
- noteのHTMLの構造が変更された場合、スクリプトが正常に動作しなくなる可能性があります。

## ライセンス

MITライセンス

## 免責事項

このツールは教育目的で提供されています。実際の使用に関しては、ユーザー自身の責任で行ってください。
