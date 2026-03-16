# 汎用 AI エージェント

Anthropic SDK を直接使って実装した、対話型 CLI AI エージェントです。
pydantic-ai などのフレームワークを使わず、Tool Use プロトコルと Agentic Loop を自前で実装しています。

---

## 必要環境

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Anthropic API キー

---

## セットアップ

### 1. 依存関係のインストール

```bash
uv sync
```

### 2. API キーの設定

`.env` ファイルを作成して API キーを記載します。

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## 起動方法

```bash
# Windows PowerShell
$env:PYTHONIOENCODING="utf-8"; uv run python main.py

# bash / Git Bash
PYTHONIOENCODING=utf-8 uv run python main.py
```

起動すると対話プロンプトが表示されます。

```
CLI AI エージェント起動（終了: exit / quit / Ctrl+C）
==================================================

>
```

---

## 使い方

### 基本的な会話

```
> こんにちは
こんにちは！私はCLI AIエージェントです。ファイル操作やコマンド実行などをお手伝いします。
```

### ファイルを読む

```
> main.py の内容を教えてください

[Tool] read(file_path='main.py')
  → ...

main.py はCLIエントリポイントで、REPLループと会話履歴の管理を担当しています。
```

### ファイルを探す

```
> このディレクトリの Python ファイルを一覧してください

[Tool] glob(pattern='**/*.py', path='.')
  → agent.py, main.py, tools/...

プロジェクトのPythonファイルは agent.py、main.py、tools/ 以下の3ファイルです。
```

### コードを検索する

```
> def で始まる関数定義を探してください

[Tool] grep(pattern='def ', file_glob='*.py')
  → agent.py:19: def run_agent_loop ...

```

### シェルコマンドを実行する

```
> Python のバージョンを確認してください

[Tool] bash(command='python --version')
  → Python 3.12.x

Python 3.12 が使用されています。
```

### 複数ステップのタスク

エージェントは自律的にツールを組み合わせてタスクを完了します。

```
> tools ディレクトリにある全ファイルの行数を合計してください

[Tool] glob(pattern='tools/**/*.py')
  → ...
[Tool] bash(command='wc -l tools/*.py')
  → ...

tools/ ディレクトリの合計行数は XXX 行です。
```

### マルチターン会話

会話の文脈は自動的に保持されます。

```
> agent.py の行数を教えてください
agent.py は 65 行です。

> そのファイルの最初の5行を見せてください   ← 「そのファイル」が agent.py と認識される

[Tool] read(file_path='agent.py', limit=5)
  → ...
```

---

## 終了方法

以下のいずれかで終了します。

```
> exit
> quit
```

または `Ctrl+C` / `Ctrl+D`

---

## 利用可能なツール

エージェントが自律的に使用するツールの一覧です。ユーザーが直接指定する必要はありません。

| ツール | 機能 | 主な引数 |
|--------|------|---------|
| `read` | ファイルを読み込む | `file_path`, `offset`, `limit` |
| `write` | ファイルを作成・上書き | `file_path`, `content` |
| `edit` | ファイル内の文字列を置換 | `file_path`, `old_string`, `new_string` |
| `glob` | パターンでファイルを検索 | `pattern`, `path` |
| `grep` | 正規表現でファイル内容を検索 | `pattern`, `path`, `file_glob` |
| `bash` | シェルコマンドを実行 | `command`, `timeout` |

---

## プロジェクト構成

```
dev_ai_agent/
├── main.py              # エントリポイント（REPLループ）
├── agent.py             # Agenticループ（Claude API 呼び出し）
├── tools/
│   ├── __init__.py      # ツール一覧・ディスパッチ
│   ├── file_tools.py    # read / write / edit / glob / grep
│   └── bash_tool.py     # bash
├── prompts/
│   └── default.md       # システムプロンプト
├── .env                 # API キー（git 管理外）
└── pyproject.toml       # 依存関係
```

設計の詳細は以下のドキュメントを参照してください。

| ドキュメント | 内容 |
|-------------|------|
| `要件仕様書.md` | 何を作るか（機能要件・非機能要件） |
| `アーキテクチャ設計書.md` | どう分けるか・なぜか（構造・技術選定） |
| `モジュール設計書.md` | どう動くか（インターフェース・内部フロー） |
