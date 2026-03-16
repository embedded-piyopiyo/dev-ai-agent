import re
from pathlib import Path

# ---------------------------------------------------------------
# Tool: Read
# ---------------------------------------------------------------
READ_SCHEMA = {
    "name": "read",
    "description": "ファイルを読み込んで内容を返す。offset/limit で範囲指定可能。",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "読み込むファイルのパス"},
            "offset":    {"type": "integer", "description": "読み始める行番号（0始まり）", "default": 0},
            "limit":     {"type": "integer", "description": "読む最大行数（0=全行）", "default": 0},
        },
        "required": ["file_path"],
    },
}

def read(file_path: str, offset: int = 0, limit: int = 0) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"エラー: ファイルが見つかりません: {file_path}"
    if not path.is_file():
        return f"エラー: ファイルではありません: {file_path}"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    if offset:
        lines = lines[offset:]
    if limit:
        lines = lines[:limit]
    numbered = [f"{offset + i + 1:4d}: {line}" for i, line in enumerate(lines)]
    return "".join(numbered) or "（空のファイル）"


# ---------------------------------------------------------------
# Tool: Write
# ---------------------------------------------------------------
WRITE_SCHEMA = {
    "name": "write",
    "description": "指定パスにファイルを書き込む（存在する場合は上書き）。親ディレクトリが無ければ自動作成する。",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "書き込むファイルのパス"},
            "content":   {"type": "string", "description": "書き込む内容"},
        },
        "required": ["file_path", "content"],
    },
}

def write(file_path: str, content: str) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"書き込み完了: {file_path} ({len(content)} bytes)"


# ---------------------------------------------------------------
# Tool: Edit
# ---------------------------------------------------------------
EDIT_SCHEMA = {
    "name": "edit",
    "description": "ファイル内の old_string を new_string に置換する（最初の1箇所のみ）。",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path":  {"type": "string", "description": "編集するファイルのパス"},
            "old_string": {"type": "string", "description": "置換前の文字列"},
            "new_string": {"type": "string", "description": "置換後の文字列"},
        },
        "required": ["file_path", "old_string", "new_string"],
    },
}

def edit(file_path: str, old_string: str, new_string: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"エラー: ファイルが見つかりません: {file_path}"
    content = path.read_text(encoding="utf-8", errors="replace")
    if old_string not in content:
        return f"エラー: 対象文字列がファイル内に見つかりません: {file_path}"
    path.write_text(content.replace(old_string, new_string, 1), encoding="utf-8")
    return f"編集完了: {file_path}"


# ---------------------------------------------------------------
# Tool: Glob
# ---------------------------------------------------------------
GLOB_SCHEMA = {
    "name": "glob",
    "description": "glob パターンに一致するファイルパスを返す（例: **/*.py）。",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "glob パターン（例: **/*.py）"},
            "path":    {"type": "string", "description": "検索起点ディレクトリ（デフォルト: .）", "default": "."},
        },
        "required": ["pattern"],
    },
}

def glob_tool(pattern: str, path: str = ".") -> str:
    matches = sorted(Path(path).glob(pattern))
    return "\n".join(str(m) for m in matches) if matches else f"一致するファイルが見つかりません: {pattern}"


# ---------------------------------------------------------------
# Tool: Grep
# ---------------------------------------------------------------
GREP_SCHEMA = {
    "name": "grep",
    "description": "path 以下の file_glob に一致するファイルを対象に、pattern（正規表現）を含む行を返す。",
    "input_schema": {
        "type": "object",
        "properties": {
            "pattern":   {"type": "string", "description": "検索する正規表現パターン"},
            "path":      {"type": "string", "description": "検索起点ディレクトリ（デフォルト: .）", "default": "."},
            "file_glob": {"type": "string", "description": "対象ファイルの glob パターン（デフォルト: **/*）", "default": "**/*"},
        },
        "required": ["pattern"],
    },
}

def grep(pattern: str, path: str = ".", file_glob: str = "**/*") -> str:
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"エラー: 無効な正規表現: {e}"
    hits = []
    for filepath in sorted(Path(path).glob(file_glob)):
        if not filepath.is_file():
            continue
        try:
            lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for lineno, line in enumerate(lines, 1):
            if regex.search(line):
                hits.append(f"{filepath}:{lineno}: {line}")
                if len(hits) >= 100:
                    hits.append("... （100件で打ち切り）")
                    break
        if len(hits) >= 100:
            break
    return "\n".join(hits) if hits else f"一致する行が見つかりません: {pattern}"
