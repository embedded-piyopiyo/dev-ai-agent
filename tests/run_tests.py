"""
run_tests.py — テスト実行 & レポート表示

実行方法:
    uv run python tests/run_tests.py              # 全テスト（実API含む）
    uv run python tests/run_tests.py --unit-only  # ユニットテストのみ（API不要）
"""
import io
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Windows の stdout を UTF-8 に設定（cp932 での文字化け対策）
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import test_tools
import test_agent

_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_CYAN   = "\033[36m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"

# テスト ID → 説明のマッピング
TC_DESCRIPTIONS = {
    "test_TC_U_01_read_normal":               "TC-U-01: read — 正常ファイルを行番号付きで読み込む",
    "test_TC_U_02_read_not_found":            "TC-U-02: read — 存在しないファイルはエラーメッセージを返す",
    "test_TC_U_03_read_offset_limit":         "TC-U-03: read — offset/limit で範囲指定できる",
    "test_TC_U_04_write_new_file":            "TC-U-04: write — 新規ファイルを作成・書き込む",
    "test_TC_U_05_write_creates_parent_dirs": "TC-U-05: write — 親ディレクトリが無ければ自動作成する",
    "test_TC_U_06_edit_replace":              "TC-U-06: edit — 文字列を正しく置換する",
    "test_TC_U_07_edit_string_not_found":     "TC-U-07: edit — 対象文字列なしのときエラーメッセージを返す",
    "test_TC_U_08_glob_match":                "TC-U-08: glob — パターンに一致するファイルを列挙する",
    "test_TC_U_09_glob_no_match":             "TC-U-09: glob — 一致なしのときメッセージを返す",
    "test_TC_U_10_grep_match":                "TC-U-10: grep — 正規表現に一致する行を返す",
    "test_TC_U_11_grep_invalid_regex":        "TC-U-11: grep — 無効な正規表現はエラーメッセージを返す",
    "test_TC_U_12_bash_command":              "TC-U-12: bash — コマンドを実行して stdout を返す",
    "test_TC_U_13_bash_timeout":              "TC-U-13: bash — タイムアウト時はエラーメッセージを返す",
    "test_TC_I_01_end_turn_returns_text":     "TC-I-01: Agentic Loop — end_turn でテキストを返す",
    "test_TC_I_02_correct_model_used":        "TC-I-02: Agentic Loop — 正しいモデルが API に渡される",
    "test_TC_I_03_tool_use_loop_continues":   "TC-I-03: Agentic Loop — tool_use 後にループが継続する",
    "test_TC_I_04_messages_accumulated":      "TC-I-04: Agentic Loop — messages が正しく蓄積される",
    "test_TC_I_05_system_prompt_sent":        "TC-I-05: Agentic Loop — system プロンプトが送信される",
    "test_TC_I_06_real_tool_call":            "TC-I-06: 実API — glob ツールを実行して結果を返答に含める",
    "test_TC_I_07_multi_turn_context":        "TC-I-07: 実API — マルチターンで会話文脈が保持される",
}


# ---------------------------------------------------------------
# テスト結果をイベントとして収集するカスタム TestResult
# ---------------------------------------------------------------
class TrackingResult(unittest.TestResult):
    """各テストの合否をリストに記録する"""

    def __init__(self):
        super().__init__()
        self.records = []   # [(method_name, status, detail)]

    def _method(self, test) -> str:
        return test.id().split(".")[-1]

    def addSuccess(self, test):
        self.records.append((self._method(test), "pass", ""))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append((self._method(test), "fail", self._exc_info_to_str(err, test)))

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append((self._method(test), "error", self._exc_info_to_str(err, test)))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append((self._method(test), "skip", reason))


# ---------------------------------------------------------------
# セクション表示
# ---------------------------------------------------------------
def _print_records(records, prefix: str) -> None:
    matched = [(m, s, d) for m, s, d in records if m.startswith(f"test_{prefix}")]
    if not matched:
        print(f"  {_YELLOW}（対象テストなし）{_RESET}")
        return
    for method, status, detail in matched:
        label = TC_DESCRIPTIONS.get(method, method)
        if status == "pass":
            print(f"  {_GREEN}✅{_RESET}  {label}")
        elif status == "skip":
            print(f"  {_YELLOW}⚠️ {_RESET}  {label}")
            print(f"       {_YELLOW}→ {detail}{_RESET}")
        else:
            icon = "❌"
            print(f"  {_RED}{icon}{_RESET}  {label}")


# ---------------------------------------------------------------
# メイン
# ---------------------------------------------------------------
def run() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(test_tools))
    suite.addTests(loader.loadTestsFromModule(test_agent))

    result = TrackingResult()
    suite.run(result)

    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total   = result.testsRun
    failed  = len(result.failures)
    errors  = len(result.errors)
    skipped = len(result.skipped)
    passed  = total - failed - errors - skipped

    # ── ヘッダー ───────────────────────────────────────────
    print(f"\n{_BOLD}{'=' * 62}{_RESET}")
    print(f"{_BOLD}  テスト実行レポート{_RESET}")
    print(f"{'=' * 62}")
    print(f"  実行日時  : {executed_at}")
    print(f"  実行数    : {total}  "
          f"({_GREEN}合格 {passed}{_RESET} / "
          f"{_RED}失敗 {failed}{_RESET} / "
          f"{_RED}エラー {errors}{_RESET} / "
          f"{_YELLOW}スキップ {skipped}{_RESET})")
    print(f"{'=' * 62}\n")

    # ── ユニットテスト ───────────────────────────────────────
    print(f"{_CYAN}{_BOLD}【ユニットテスト — ツール単体 (API不要)】{_RESET}")
    _print_records(result.records, "TC_U")

    # ── 統合テスト（モック）─────────────────────────────────
    print(f"\n{_CYAN}{_BOLD}【統合テスト — Agentic Loop (モック使用)】{_RESET}")
    _print_records(result.records, "TC_I_0")   # TC_I_01〜05 and TC_I_06〜07 both start with TC_I_0

    # ── 失敗・エラー詳細 ─────────────────────────────────────
    problems = [(m, s, d) for m, s, d in result.records if s in ("fail", "error")]
    if problems:
        print(f"\n{_RED}{_BOLD}【失敗・エラー詳細】{_RESET}")
        for method, status, detail in problems:
            label = TC_DESCRIPTIONS.get(method, method)
            tag = "FAIL" if status == "fail" else "ERROR"
            print(f"\n  {_RED}[{tag}]{_RESET} {label}")
            for line in detail.splitlines()[-5:]:
                print(f"    {line}")

    # ── フッター ───────────────────────────────────────────
    print(f"\n{'=' * 62}")
    if result.wasSuccessful():
        print(f"  {_GREEN}{_BOLD}✅  全テスト合格{_RESET}")
    else:
        print(f"  {_RED}{_BOLD}❌  テスト失敗あり（上記の詳細を確認してください）{_RESET}")
    print(f"{'=' * 62}\n")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run())
