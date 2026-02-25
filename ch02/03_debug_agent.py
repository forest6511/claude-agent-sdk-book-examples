"""第2章: デバッグ付きエージェント

ToolUseBlock を検知してツール呼び出しの詳細を表示する。
エージェントの動作を追跡したいときのパターン。

実行:
    python ch02/03_debug_agent.py
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
        allowed_tools=["Read"],
        permission_mode="bypassPermissions",
        system_prompt="ファイル操作エージェントです。",
        max_turns=5,
    )
    task = "requirements.txt の内容を読んで要約してください"
    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[DEBUG] 呼び出し: {block.name}")
                    print(f"[DEBUG] 引数: {block.input}")
                elif isinstance(block, TextBlock):
                    print(f"[回答] {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"費用: ${message.total_cost_usd:.6f}")


anyio.run(main)
