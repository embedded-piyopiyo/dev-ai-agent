"""
main.py - CLIエントリポイント

責務: 「どう使うか」
- 環境変数の読み込み・クライアント生成
- REPLループ（入力受付・表示）
- 会話履歴の保持

ツールループのロジックは agent.py に委譲する。
"""
import os

import anthropic
from dotenv import load_dotenv

from agent import run_agent_loop

load_dotenv()


def main() -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("CLI AI エージェント起動（終了: exit / quit / Ctrl+C）")
    print("=" * 50)

    # 会話履歴: run_agent_loop 内で直接追記されていく
    message_history: list = []

    while True:
        try:
            user_input = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n終了します。")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("終了します。")
            break

        # ユーザーメッセージを履歴に追加
        message_history.append({"role": "user", "content": user_input})

        try:
            print()
            reply = run_agent_loop(client, message_history)
            print(reply)
        except Exception as e:
            print(f"\nエラー: {e}")
            # 失敗したメッセージを取り除き、履歴を壊さない
            message_history.pop()


if __name__ == "__main__":
    main()
