"""
agent.py - Agenticループの実装

[学習ポイント]
1. stop_reason == "tool_use"  → Claude がツールを呼びたい → 実行してループ継続
2. stop_reason == "end_turn"  → Claude が回答完了 → テキストを返してループ終了
3. messages リストを参照渡しで蓄積することで、呼び出し元（main.py）が
   会話履歴をそのまま保持できる
"""
from pathlib import Path

from tools import TOOLS, execute_tool

# システムプロンプトをファイルから読み込む
# → コードを変えずにプロンプトをチューニングできる
SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "default.md").read_text(encoding="utf-8")


def run_agent_loop(client, messages: list) -> str:
    """
    Claude API を呼び出し、tool_use がなくなるまでループする。

    Args:
        client  : anthropic.Anthropic インスタンス
        messages: 会話履歴リスト（この関数内で直接追記される）

    Returns:
        Claude の最終テキスト回答
    """
    while True:
        # --- (1) Claude API 呼び出し ---
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # --- (2) assistant の返答を履歴に追加 ---
        # response.content はブロックのリスト（TextBlock / ToolUseBlock）
        messages.append({"role": "assistant", "content": response.content})

        # --- (3) stop_reason を判定 ---
        if response.stop_reason != "tool_use":
            # ツール呼び出しなし → テキストブロックを返してループ終了
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        # --- (4) tool_use ブロックをすべて処理 ---
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                # tool_result は user ロールで返す（Anthropic プロトコル）
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # --- (5) ツール結果を履歴に追加してループ継続 ---
        messages.append({"role": "user", "content": tool_results})
