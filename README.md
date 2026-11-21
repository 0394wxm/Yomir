# Yomir — 漢文（白文）→ 書き下し文 変換 Web MVP

> リポジトリ名 **Yomir** と開発コード名 **kanbun-kakikudashi** は、同じプロジェクトの二つの名前です（漢文を「書き下す」= kakikudashi することから）。

漢文（白文）を訓読して書き下し文へ変換する Web アプリケーション。二つの入口が同じ訓読パイプラインに集約されます。

- **入口 A**: 活字漢文テキストを貼り付けて訓読
- **入口 B**: 画像をアップロード（くずし字対応。国立国会図書館の ndlkotenocr-lite エンジンを内蔵）

出力は 4 点：①返り点付き原文（縦書き＋ルビ）②書き下し文（送り仮名を含む）③現代語訳（API key 未設定時はプレースホルダ）④語釈（文語 500 語の辞書引き）。行単位の対照表示、逐行修正、履歴と行単位キャッシュ、EPUB 書き出し（縦書き）を備えます。

---

## 数字（2026-11-21 時点、`master` 54d2410 のコード／アーカイブから実測）

| 項目 | 数値 |
| --- | --- |
| テスト | `pytest tests` 全量 **214 passed** |
| 評価セット | `eval/golden_4000.json` **4000 組**（白文ユニーク 3975。kanbun.info の白文・書き下し文ペアから構築。拡張版 `golden_7908.json` **7908 組**も同梱済みだが、既定の評価口径は golden_4000 のまま） |
| 規則エンジン | 平均編集距離 **13.719** ／ 完全一致 **24/3998**（4000 条中 error 2 条を除く。正規化口径：空白を除いた文字単位比較。N64 マージ後の `eval/night64_results_4000.json` 口径） |
| ルールチェーン | Rule A（表示スタイル：ふ→う、「は曰く」→「曰く」）／ Rule C'（て而して→て、「顧みて而して」はガードで保持）／ Rule D（これ→之、白文ガード付き）／ Rule E・F・G・H（かな→漢字の 4 系列、**5+4+4+3 の 16 語**、いずれも白文ガード＋長語マスク付き）／ Rule I（かな→漢字の第 5 系列、**6 語**：けだし→蓋し、いずくんぞ→焉くんぞ、もし→如し、それ→夫れ、ただ→惟だ、なかれ→毋かれ。いずれも白文ガード＋長語マスク付き） |
| 正字化 | `SHINJITAI_MAP` 旧字体→新字体 **246 組**（N64 で 99 組を追加。出力表示層のみ。白文入力は原文のまま保持） |
| 固有名詞結合 | `MERGE_WORDS` **21 語**（短文限定。長文では merge ガードが作動） |
| OCR 精度 | 人工採録 GT **92 行**（`eval/ocr_gt_100.tsv`）で CER raw **0.3568** ／ 正規化 **0.3053** |
| OCR 版面処理 | ゴミ行（検出枠）フィルタ、レイアウト幾何フィルタ（頁脚帯・上部書き入れ長条）、行順クラスタリング、主欄の並列枠の並べ直し、割注対の右先並べ直し（右先率基線 **98.57% / 98.63%**、厳密層 296 対 **100%**） |
| OCR 速度 | 1 行あたり約 1〜3 秒（CPU） |
| 語釈辞書 | 文語 500 語（`backend/glossary_lexicon.py`。自動整理・未人力校正） |

上記の主要数字は次のコマンドでプログラム的に再照合できます：

```bash
python tools/verify_readme_facts.py
```

### ブランチ統合状況（Night 65 時点）

以前「未統合」と記載していた 2 つの作業ブランチは、いずれも 2026-11-21 に `master` へ統合済みです（`498cfcb`＝night64-rulei、`e576172`＝night62-eval10000。その後の文書同期を含む最終 HEAD が `54d2410`）。上の「数字」表はすべて統合後の `master` 実測値です。

- **`night64-rulei`（統合済み）**：Rule I（かな→漢字第 5 批・6 語、白文ガード付き）と `SHINJITAI_MAP` 99 組追加（147→246）を反映。golden_4000 上で平均編集距離 13.889→**13.719**、完全一致 19→**24**（`eval/night64_results_4000.json`）。OCR GT CER は bit 単位で不変。
- **`night62-eval10000`（統合済み）**：拡張評価セット `golden_7908.json`（4000 基盤＋追加 3908。kanbun.info サイト全体 2696 ページの実査により「追加 6000／総量 10000」は制約内で到達不能と実証済み）をリポジトリへ取り込み済み。**既定の評価口径は golden_4000 のまま**で、7908 全量の実測は `eval/night62_results_7908.json` にアーカイブ（規則エンジン：平均編集距離 **13.241**／完全一致 **25**、n=7905・error 3）。

---

## セットアップ

### 1. バックエンド（Python 3.12）

```bash
python -m pip install -r backend/requirements.txt
```

`udkundoku==2.3.0` とその依存（udkanbun, unidic2ud, ufal.udpipe, mecab-python3, deplacy など）が入ります。

### 2. qkana shim（インポートに必要）

`import udkundoku` は UniDic の qkana 辞書を要求し、未取得なら配布元（clrd.ninjal.ac.jp）から自動ダウンロードを試みます。**このサーバに到達できないネットワーク環境ではインポートが固まる**ため、PyPI の `unidic-lite`（unidic-cwj compact）から代替辞書（shim）を生成するスクリプトを同梱しています：

```bash
pip install unidic-lite        # 未インストールなら
python -I tools/make_qkana_shim.py          # 生成済みならスキップ
python -I tools/make_qkana_shim.py --force  # 再生成
```

shim は漢字見出しの代替辞書で、公式の qkana（假名見出し）とは一部の送り仮名推定が異なることがあります。到達可能な環境では `python -X utf8 tools/fetch_official_qkana.py` で公式辞書（280MB・レジューム対応）を取得し、shim を自動置換できます。**公式辞書を取得する前に shim を消さないでください**（`import udkundoku` が失敗します）。

### 3. OCR エンジン（入口 B を使う場合のみ）

エンジン本体・モデル（約 80MB）はリポジトリに含めません。NDL が配布する **ndlkotenocr-lite**（CC BY 4.0）の Windows 版 GUI に同梱される `app.zip` を展開します：

```bat
python -I -m zipfile -e "<ndlkotenocr-lite を展開した場所>\data\flutter_assets\app\app.zip" ocr_runtime
```

`ocr_runtime/` は .gitignore 済み。場所は環境変数 `KANBUN_OCR_SRC` で変更できます。展開しなくても入口 A（テキスト訓読）は動作します。

### 4. フロントエンド（Node.js）

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173/
```

バックエンド URL は既定で開発サーバのプロキシ経由（`vite.config.ts` → `http://127.0.0.1:8000`）です。別の場所に立てたバックエンドに向ける場合は `VITE_API_BASE` を設定します。

### 5. 起動とテスト

```bash
# バックエンド（http://127.0.0.1:8000）
python -X utf8 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# テスト（214 条）
python -X utf8 -m pytest tests -q
```

`start_backend.bat` ／ `start_frontend.bat` でワンクリック起動もできます。ビルド済みフロントを同一アプリから配信するデスクトップシェルモード（Tauri sidecar）もあります（`KANBUN_SERVE_WEB`／`KANBUN_SIDECAR`）。

---

## 環境変数（すべて任意）

`backend/` のコードが実際に読む変数の全量です。

| 変数 | 役割 | 既定 |
| --- | --- | --- |
| `KANBUN_DB` | SQLite のパス | `<repo>/kanbun.db` |
| `KANBUN_LLM_API_KEY` | 現代語訳・語釈の LLM key。未設定時は現代語訳＝プレースホルダ、語釈＝辞書引き | 未設定 |
| `KANBUN_LLM_BASE_URL` | OpenAI 互換エンドポイント | `https://api.openai.com/v1` |
| `KANBUN_LLM_MODEL` | モデル名 | `gpt-4o-mini` |
| `KANBUN_KANA_RATIO` | この比率を超えるかな入力を「訓読しない転写」に分岐する閾値 | `0.3` |
| `KANBUN_TIMING` | `1` で `/api/kundoku` の区間タイミングをログ出力 | 無効 |
| `KANBUN_LAZY_ENGINE` | `1` でポートを先に開けて訓読エンジンをバックグラウンド読込（デスクトップシェル用） | 無効 |
| `KANBUN_SERVE_WEB` | `1` で `frontend/dist` を同一アプリから配信 | 無効 |
| `KANBUN_SIDECAR` | `1` で `KANBUN_SERVE_WEB` と同義（Tauri sidecar 用） | 無効 |
| `KANBUN_OCR_SITE` | kotenocr-lite 側の依存パッケージ（onnxruntime 等）のディレクトリ | kotenocr-lite のインストール先 |
| `KANBUN_OCR_SRC` | OCR エンジンの展開先 `src` | `<repo>/ocr_runtime/src` |
| `KANBUN_OCR_ORDER` | 行順 `native`（公式順）／`cluster`（縦書き版式の列順クラスタリング） | `cluster` |
| `KANBUN_OCR_JUNK_FILTER` | `0` でゴミ行フィルタ（色票・定規・朱印などの検出枠）を無効化 | `1` |
| `KANBUN_OCR_LAYOUT_FILTER` | `0` でレイアウト幾何フィルタ（頁脚帯・上部手書き長条）を無効化 | `1` |
| `KANBUN_OCR_MAINCOL` | `0` で主欄の並列枠の並べ直しを無効化 | `1` |
| `KANBUN_OCR_WARICHU` | `0` で割注対の右先並べ直しを無効化 | `1` |

---

## API 一覧

| メソッド | パス | 機能 |
| --- | --- | --- |
| GET | `/health` | 稼働確認（`engine_loaded` 等） |
| POST | `/api/kundoku` | 訓読本体。返り点付き原文・書き下し文・現代語訳・語釈・`request_id` を返す |
| GET | `/api/history` | 履歴一覧 |
| POST | `/api/ocr` | 画像 1 枚の OCR＋訓読 |
| POST | `/api/ocr/batch` | 同期の一括 OCR |
| POST | `/api/ocr/batch/async` | 非同期一括（`GET /api/ocr/batch/{job_id}` で進捗照会、`.../cancel` で中止） |
| GET | `/api/export/epub?ids=…` | 履歴項目から EPUB 3 書き出し |
| POST | `/api/export/epub` | 白文テキストの直渡し EPUB（訓読前の本文書き出し） |

EPUB は EPUB 3・`writing-mode: vertical-rl` の縦書き（非対応リーダーでは横書きに自動フォールバック）、目次付き、内容から決定論的 UUID を派生。フロントのボタンは「EPUB 出力」（訓読結果を保存済みのとき有効）と「白文 EPUB」（OCR／訂正済みの白文をそのまま書き出し）の 2 種類。

一冊丸ごとの取り込みは `tools/import_pid.py`：NDL デジタルコレクションの IIIF マニフェスト（PID 指定）→ 1400px 画像 → OCR → 訓読 → `book.md`。実績として『信長公記』巻之上の 51/51 ページ取り込み済み。

---

## 既知の問題（現状の実測に基づく）

1. **訓読の完全一致は 24/3998**。24 条はすべて 20 字以内の文（3041 条、平均編集距離 7.74）で、21 字超は 0。文体別では漢詩 6.903／詩経 5.157 に対し故事 20.861／論語 26.472（N64 マージ後の口径）。長文の助詞挿入位置、名詞化、動词条目などは mecab-kanbun／UD 系の解析層の課題で、表面規則では届かない。
2. **再読文字は「未」のみ**（udkundoku の既知上限）。應・當・須・蓋・宜・將 は未対応。
3. **現代語訳は key なしではプレースホルダ**。語釈の 500 語辞書は自動整理で未人力校正。
4. **かな比率 >30% の入力は訓読せず転写のみ**（分岐自体は正しい挙動だが、侯文・明治文書は対象外になる）。
5. **OCR は印刷物中心の精度**。草書・草仮名や絵本の散字ページは苦手で、GT 92 行も印刷物中心に人工採録した小規模なもの（人工 GT の作成が困難な草仮名・草書類 3 冊は対象外）。
6. **cached 経路で 2.4 秒級の外れ値が出ることがある**。原因は特定済み（D4：SQLite 書き込みの fsync が遅いディスクでは数十倍遅くなる環境依存。高速なディスク・`KANBUN_DB` 移設で緩和）。
7. **guwenbert（BERT 依存解析）は後端未統合**。チェックポイント互換はローダで解決済み、オフライン比較では漢詩系短句で規則エンジンと互角〜やや優勢（Night 60 口径。N62 の拡張分 3907 条対決では guwenbert **12.466** に対し規則 **12.577**、規則勝 1366／guwenbert 勝 1390／引分 1151）。統合は製品判断として保留中。

---

## 構成

```
backend/       FastAPI(8000)：main / kundoku_rules / ocr_engine / ocr_layout /
               ocr_postfix / db / llm / epub_export / glossary_lexicon(+extra)
frontend/      Vite + React + TS(5173)：行別対照・履歴・EPUB 出力・レスポンシブ
tests/         pytest 214 条
eval/          評価セット（golden*.json）＋実行結果アーカイブ＋OCR GT（ocr_gt_100.tsv）
tools/         評価・一括取り込み・検証・shim 生成などの補助スクリプト
ocr_runtime/   （非同梱）OCR エンジン展開先（.gitignore 済）
docs/          設計メモ
ROADMAP.md     夜間開発のタスクキュー
REPORT_*.md    各夜・各日の作業報告（数字はすべて eval/ のアーカイブ付き）
ACCEPT_LOG.md  毎夜の検収（tools/accept_night.py）の運行記録
```

## 出典・クレジット

- OCR エンジン・モデル：国立国会図書館 **ndl-lab/ndlkotenocr-lite**（CC BY 4.0）。推理フローは同梱 GUI の `main.py` をプロセス内に移植したもので、アルゴリズムは未改変。
- 評価セット：kanbun.info の白文・書き下し文のページペアから構築（expected は一字も改変しない運用ルールを厳守）。
- OCR GT（92 行）：NDL デジタル資料の印刷物から人工採録。
- 書誌取り込み：NDL デジタルコレクション IIIF。

## 開発ログ

本リポジトリは夜間バッチ開発で進めています。1 夜＝1 仕事単位で、計画は `ROADMAP.md`、実行報告は `REPORT_NIGHT*.md`／`REPORT_DAY*.md`、検収（テスト・評価アーカイブの整合性・規則回帰・性能包絡）は `tools/accept_night.py` が `ACCEPT_LOG.md` に記録します。負の結果（採用しなかった実験）もすべて報告・アーカイブ化しています。
