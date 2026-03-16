"""
test_tools.py — ツール単体テスト（TC-U-01 〜 TC-U-13）

Claude API 不要。tempfile を使って副作用のないテストを行う。
実行: uv run python tests/run_tests.py
"""
import sys
import unittest
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.file_tools import read, write, edit, glob_tool, grep
from tools.bash_tool import bash


# ---------------------------------------------------------------
# TC-U-01 〜 TC-U-03: read
# ---------------------------------------------------------------
class TestRead(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = Path(self.tmpdir) / "sample.txt"
        self.tmpfile.write_text("line1\nline2\nline3\nline4\nline5\n", encoding="utf-8")

    def test_TC_U_01_read_normal(self):
        """TC-U-01: 正常なファイルを読み込み、行番号付きで返す"""
        result = read(str(self.tmpfile))
        self.assertIn("line1", result)
        self.assertIn(": ", result)            # 行番号フォーマット確認
        self.assertIn("   1: ", result)      # 先頭行

    def test_TC_U_02_read_not_found(self):
        """TC-U-02: 存在しないファイルはエラーメッセージを返す（例外を送出しない）"""
        result = read("/nonexistent/path/no_file.txt")
        self.assertIn("エラー", result)
        self.assertIn("見つかりません", result)

    def test_TC_U_03_read_offset_limit(self):
        """TC-U-03: offset=1, limit=2 で 2〜3行目のみ返す"""
        result = read(str(self.tmpfile), offset=1, limit=2)
        self.assertIn("line2", result)
        self.assertIn("line3", result)
        self.assertNotIn("line1", result)    # offset 前の行は含まれない
        self.assertNotIn("line4", result)    # limit 後の行は含まれない


# ---------------------------------------------------------------
# TC-U-04 〜 TC-U-05: write
# ---------------------------------------------------------------
class TestWrite(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_TC_U_04_write_new_file(self):
        """TC-U-04: 新規ファイルを作成し、内容を正しく書き込む"""
        filepath = str(Path(self.tmpdir) / "new.txt")
        result = write(filepath, "hello world")
        self.assertIn("書き込み完了", result)
        self.assertTrue(Path(filepath).exists())
        self.assertEqual(Path(filepath).read_text(encoding="utf-8"), "hello world")

    def test_TC_U_05_write_creates_parent_dirs(self):
        """TC-U-05: 親ディレクトリが存在しない場合は自動作成する"""
        filepath = str(Path(self.tmpdir) / "sub" / "deep" / "file.txt")
        result = write(filepath, "nested content")
        self.assertIn("書き込み完了", result)
        self.assertTrue(Path(filepath).exists())


# ---------------------------------------------------------------
# TC-U-06 〜 TC-U-07: edit
# ---------------------------------------------------------------
class TestEdit(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = Path(self.tmpdir) / "edit.txt"
        self.tmpfile.write_text("Hello World\nFoo Bar\n", encoding="utf-8")

    def test_TC_U_06_edit_replace(self):
        """TC-U-06: old_string を new_string に置換する（最初の1箇所）"""
        result = edit(str(self.tmpfile), "Hello", "Hi")
        self.assertIn("編集完了", result)
        content = self.tmpfile.read_text(encoding="utf-8")
        self.assertIn("Hi World", content)
        self.assertNotIn("Hello World", content)

    def test_TC_U_07_edit_string_not_found(self):
        """TC-U-07: 対象文字列がない場合はエラーメッセージを返す"""
        result = edit(str(self.tmpfile), "NonExistent", "replacement")
        self.assertIn("エラー", result)
        # ファイルは変更されていないこと
        content = self.tmpfile.read_text(encoding="utf-8")
        self.assertIn("Hello World", content)


# ---------------------------------------------------------------
# TC-U-08 〜 TC-U-09: glob
# ---------------------------------------------------------------
class TestGlob(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        (Path(self.tmpdir) / "alpha.py").write_text("", encoding="utf-8")
        (Path(self.tmpdir) / "beta.py").write_text("", encoding="utf-8")
        (Path(self.tmpdir) / "gamma.txt").write_text("", encoding="utf-8")

    def test_TC_U_08_glob_match(self):
        """TC-U-08: *.py パターンで .py ファイルのみ列挙する"""
        result = glob_tool("*.py", path=self.tmpdir)
        self.assertIn("alpha.py", result)
        self.assertIn("beta.py", result)
        self.assertNotIn("gamma.txt", result)

    def test_TC_U_09_glob_no_match(self):
        """TC-U-09: 一致するファイルがない場合はメッセージを返す"""
        result = glob_tool("*.xyz", path=self.tmpdir)
        self.assertIn("一致するファイルが見つかりません", result)


# ---------------------------------------------------------------
# TC-U-10 〜 TC-U-11: grep
# ---------------------------------------------------------------
class TestGrep(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        (Path(self.tmpdir) / "fruits.txt").write_text(
            "apple\nbanana\ncherry\n", encoding="utf-8"
        )

    def test_TC_U_10_grep_match(self):
        """TC-U-10: 正規表現に一致する行を返す"""
        result = grep("ban.*", path=self.tmpdir, file_glob="*.txt")
        self.assertIn("banana", result)
        self.assertNotIn("apple", result)
        self.assertNotIn("cherry", result)

    def test_TC_U_11_grep_invalid_regex(self):
        """TC-U-11: 無効な正規表現はエラーメッセージを返す（例外を送出しない）"""
        result = grep("[invalid_regex", path=self.tmpdir)
        self.assertIn("エラー", result)
        self.assertIn("正規表現", result)


# ---------------------------------------------------------------
# TC-U-12 〜 TC-U-13: bash
# ---------------------------------------------------------------
class TestBash(unittest.TestCase):

    def test_TC_U_12_bash_command(self):
        """TC-U-12: コマンドを実行して stdout を返す"""
        result = bash("echo hello_test")
        self.assertIn("hello_test", result)

    def test_TC_U_13_bash_timeout(self):
        """TC-U-13: タイムアウト時はエラーメッセージを返す（例外を送出しない）"""
        result = bash('python -c "import time; time.sleep(10)"', timeout=1)
        self.assertIn("エラー", result)
        self.assertIn("タイムアウト", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
