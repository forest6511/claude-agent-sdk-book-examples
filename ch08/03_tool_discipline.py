"""第8章: ツール制限の美学（最小権限の原則）

「幅より深さ」— タスクに必要な最小限のツールだけを与える。
ツールを絞ることでトークン節約・誤選択防止・テスト容易性が向上する。

実行:
    python ch08/03_tool_discipline.py
"""
import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


# 悪い例: 不必要に広いツールセット
BLOATED_OPTIONS = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Edit", "Bash", "Task", "Glob", "Grep"],
    permission_mode="bypassPermissions",
    system_prompt="コードをレビューしてください。",
)

# 良い例: コードレビューに必要な最小限のツール
REVIEW_OPTIONS = ClaudeAgentOptions(
    allowed_tools=["Read", "Grep", "Glob"],
    permission_mode="bypassPermissions",
    system_prompt=(
        "あなたはコードレビュー専門エージェントです。\n"
        "Readでファイルを読み取り専用で確認し、問題点を報告してください。\n"
        "ファイルの変更は一切行わないでください。"
    ),
    max_turns=5,
)

# 良い例: コード生成に必要な最小限のツール
WRITE_OPTIONS = ClaudeAgentOptions(
    allowed_tools=["Write"],
    permission_mode="bypassPermissions",
    system_prompt="指定されたPythonコードを output/ ディレクトリに書いてください。",
    max_turns=3,
)


async def run_minimal(task: str, options: ClaudeAgentOptions) -> None:
    """最小権限オプションでエージェントを実行する。"""
    tool_count = len(options.allowed_tools or [])
    print(f"ツール数: {tool_count} 個 → {options.allowed_tools}")

    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text[:300])
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd or 0.0
            print(f"\n費用: ${cost:.6f} | {message.num_turns} ターン")


async def main() -> None:
    import os
    os.makedirs("output", exist_ok=True)

    print("=== レビュー専用エージェント（Read/Grep/Glob のみ）===")
    await run_minimal(
        "このディレクトリのPythonファイルを確認して概要を教えてください",
        REVIEW_OPTIONS,
    )

    print("\n=== 書き込み専用エージェント（Write のみ）===")
    await run_minimal(
        "output/greeting.py に 'print(\"Hello, World!\")' を書いてください",
        WRITE_OPTIONS,
    )


anyio.run(main)
