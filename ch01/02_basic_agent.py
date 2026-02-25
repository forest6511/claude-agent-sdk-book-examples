"""第1章: Agent SDK の基本的な使い方

Messages API との比較: Agent SDK を使うと
エージェントループを数行で記述できる。

実行:
    python ch01/02_basic_agent.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    query,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob"],
        system_prompt="ファイルシステムの調査をしてください。",
    )

    async for message in query(
        prompt="カレントディレクトリのファイル概要を教えて",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            if message.total_cost_usd:
                print(f"\n費用: ${message.total_cost_usd:.6f}")


anyio.run(main)
