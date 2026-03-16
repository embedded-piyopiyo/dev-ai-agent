import subprocess

# ---------------------------------------------------------------
# Tool: Bash
# ---------------------------------------------------------------
BASH_SCHEMA = {
    "name": "bash",
    "description": "シェルコマンドを実行し、stdout + stderr を返す。",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "実行するシェルコマンド"},
            "timeout": {"type": "integer", "description": "タイムアウト秒数（デフォルト: 30）", "default": 30},
        },
        "required": ["command"],
    },
}

def bash(command: str, timeout: int = 30) -> str:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[stderr]\n{proc.stderr}"
        if proc.returncode != 0:
            output += f"\n[終了コード: {proc.returncode}]"
        return output.strip() or "（出力なし）"
    except subprocess.TimeoutExpired:
        return f"エラー: タイムアウト ({timeout}秒)"
    except Exception as e:
        return f"エラー: {e}"
