"""第2章: ファイル操作エージェント

組み込みツール（Read/Write/Glob）を使ってファイル操作を行うエージェント。
permission_mode="bypassPermissions" で確認なしに実行する。

実行:
    python ch02/02_file_agent.py
"""
import anyio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Glob"],
        permission_mode="bypassPermissions",
        system_prompt=(
            "あなたはファイル操作を行うエージェントです。"
            "指示に従い、Read・Write・Glob ツールを使って作業してください。"
        ),
        max_turns=5,
    )
    task = (
        "カレントディレクトリのPythonファイル一覧を確認して、"
        "'output/summary.txt' に一覧を書き込んでください。"
    )
    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"  [ツール] {block.name}")
                elif isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd:
                print(f"費用: ${message.total_cost_usd:.6f}")


anyio.run(main)
