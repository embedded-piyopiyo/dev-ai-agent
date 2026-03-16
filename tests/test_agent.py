"""
test_agent.py — Agenticループ統合テスト（TC-I-01 〜 TC-I-07）

TC-I-01〜05: unittest.mock を使用（API キー不要）
TC-I-06〜07: 実際の Claude API を使用（ANTHROPIC_API_KEY が必要）

実行: uv run python tests/run_tests.py
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


# ---------------------------------------------------------------
# モックヘルパー
# ---------------------------------------------------------------
def _text_response(text: str) -> MagicMock:
    """stop_reason=end_turn のテキスト返答モックを生成する"""
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    resp.stop_reason = "end_turn"
    return resp


def _tool_response(name: str, tool_input: dict, tool_id: str = "toolu_test01") -> MagicMock:
    """stop_reason=tool_use のツール呼び出しモックを生成する"""
    block = MagicMock()
    block.type = "tool_use"
    block.name = name
    block.input = tool_input
    block.id = tool_id
    resp = MagicMock()
    resp.content = [block]
    resp.stop_reason = "tool_use"
    return resp


# ---------------------------------------------------------------
# TC-I-01〜05: モックを使った Agentic Loop テスト（API 不要）
# ---------------------------------------------------------------
class TestAgentLoopMocked(unittest.TestCase):

    def setUp(self):
        from agent import run_agent_loop
        self.run = run_agent_loop

    def test_TC_I_01_end_turn_returns_text(self):
        """TC-I-01: stop_reason=end_turn のとき Claude のテキストを返す"""
        client = MagicMock()
        client.messages.create.return_value = _text_response("こんにちは！")

        messages = [{"role": "user", "content": "こんにちは"}]
        result = self.run(client, messages)

        self.assertEqual(result, "こんにちは！")
        self.assertEqual(client.messages.create.call_count, 1)

    def test_TC_I_02_correct_model_used(self):
        """TC-I-02: API 呼び出しに claude-haiku-4-5-20251001 モデルが使われる"""
        client = MagicMock()
        client.messages.create.return_value = _text_response("ok")

        self.run(client, [{"role": "user", "content": "test"}])

        kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "claude-haiku-4-5-20251001")

    def test_TC_I_03_tool_use_loop_continues(self):
        """TC-I-03: tool_use のあとループが継続し、end_turn で終了する"""
        client = MagicMock()
        client.messages.create.side_effect = [
            _tool_response("bash", {"command": "echo hi"}),  # 1回目: tool_use
            _text_response("実行しました"),                    # 2回目: end_turn
        ]

        result = self.run(client, [{"role": "user", "content": "echo hi を実行して"}])

        self.assertEqual(result, "実行しました")
        self.assertEqual(client.messages.create.call_count, 2)

    def test_TC_I_04_messages_accumulated(self):
        """TC-I-04: messages に assistant/tool_result/assistant が順に蓄積される"""
        client = MagicMock()
        client.messages.create.side_effect = [
            _tool_response("bash", {"command": "echo hi"}),
            _text_response("完了"),
        ]

        messages = [{"role": "user", "content": "test"}]
        self.run(client, messages)

        # user(1) + assistant(tool_use) + user(tool_result) + assistant(end_turn)
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[1]["role"], "assistant")  # tool_use ブロック
        self.assertEqual(messages[2]["role"], "user")       # tool_result ブロック
        self.assertEqual(messages[3]["role"], "assistant")  # 最終テキスト

    def test_TC_I_05_system_prompt_sent(self):
        """TC-I-05: API 呼び出しに system プロンプトが含まれ、内容が空でない"""
        client = MagicMock()
        client.messages.create.return_value = _text_response("ok")

        self.run(client, [{"role": "user", "content": "test"}])

        kwargs = client.messages.create.call_args.kwargs
        self.assertIn("system", kwargs)
        self.assertGreater(len(kwargs["system"]), 0)


# ---------------------------------------------------------------
# TC-I-06〜07: 実 Claude API を使った統合テスト
# ---------------------------------------------------------------
@unittest.skipUnless(
    os.environ.get("ANTHROPIC_API_KEY"),
    "スキップ: ANTHROPIC_API_KEY が未設定（.env を確認してください）"
)
class TestAgentLoopReal(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import anthropic
        from agent import run_agent_loop
        cls.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        # staticmethod にしないとインスタンス経由で self が第1引数に束縛されてしまう
        # ※ cls.run は unittest.TestCase.run と衝突するため使用不可
        cls.agent_run = staticmethod(run_agent_loop)

    def test_TC_I_06_real_tool_call(self):
        """TC-I-06: glob ツールを実際に呼び出し、結果を返答に含める"""
        messages = [{"role": "user", "content": "glob ツールで *.py ファイルを検索してください。"}]
        result = self.agent_run(self.client, messages)

        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        # agent.py か main.py が返答に含まれることを確認
        self.assertTrue(
            "agent.py" in result or "main.py" in result,
            f"返答にファイル名が含まれていない: {result[:200]}"
        )

    def test_TC_I_07_multi_turn_context(self):
        """TC-I-07: マルチターン会話で前のターンの文脈が保持される"""
        history = []

        # ターン1: ファイル名を伝える
        history.append({"role": "user", "content": "「agent.py」というファイル名を覚えておいてください。"})
        self.agent_run(self.client, history)

        # ターン2: 前のターンの情報を引き出す
        history.append({"role": "user", "content": "さきほど覚えたファイル名を教えてください。"})
        reply = self.agent_run(self.client, history)

        self.assertIn("agent.py", reply, f"会話文脈が保持されていない: {reply[:200]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
