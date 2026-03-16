"""
tools パッケージ
- TOOLS      : Anthropic API に渡すツールスキーマのリスト
- execute_tool: ツール名と引数を受け取り、実装関数を呼び出す
"""
from .file_tools import (
    READ_SCHEMA,  read,
    WRITE_SCHEMA, write,
    EDIT_SCHEMA,  edit,
    GLOB_SCHEMA,  glob_tool,
    GREP_SCHEMA,  grep,
)
from .bash_tool import BASH_SCHEMA, bash

# Anthropic API に渡すスキーマ一覧
TOOLS = [READ_SCHEMA, WRITE_SCHEMA, EDIT_SCHEMA, GLOB_SCHEMA, GREP_SCHEMA, BASH_SCHEMA]

# ツール名 → 実装関数のマッピング
_DISPATCH = {
    "read":  read,
    "write": write,
    "edit":  edit,
    "glob":  glob_tool,
    "grep":  grep,
    "bash":  bash,
}

_CYAN  = "\033[36m"
_GRAY  = "\033[90m"
_RESET = "\033[0m"


def execute_tool(name: str, tool_input: dict) -> str:
    """
    ツールを実行してコンソールに経過を表示する。

    [学習ポイント]
    - tool_input は Claude が生成した JSON オブジェクト（block.input）
    - 戻り値の文字列が tool_result の content としてそのまま Claude に返る
    """
    args_str = ", ".join(f"{k}={v!r}" for k, v in tool_input.items())
    print(f"\n{_CYAN}[Tool] {name}({args_str}){_RESET}", flush=True)

    result = _DISPATCH[name](**tool_input)

    preview = result if len(result) <= 120 else result[:120] + "..."
    print(f"{_GRAY}  >> {preview}{_RESET}", flush=True)

    return result
