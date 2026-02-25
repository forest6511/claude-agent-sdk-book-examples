"""第3章: セッションの並列分岐

同じ前提から複数のアプローチを並列探索する。
anyio.create_task_group() で2つの ClaudeSDKClient を同時に実行。

実行:
    python ch03/04_session_branching.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

# 共通の前提コンテキスト
SHARED_CONTEXT = "Pythonで並列処理を実装したい。選択肢を比較してほしい。"


async def explore_threading() -> None:
    options = ClaudeAgentOptions(
        system_prompt=f"前提: {SHARED_CONTEXT}",
        max_turns=3,
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("threading モジュールを使う方法は？")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"[threading] {block.text[:300]}...")


async def explore_asyncio() -> None:
    options = ClaudeAgentOptions(
        system_prompt=f"前提: {SHARED_CONTEXT}",
        max_turns=3,
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("asyncio を使う方法は？")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"[asyncio] {block.text[:300]}...")


async def main() -> None:
    print("2つのアプローチを並列探索中...\n")
    async with anyio.create_task_group() as tg:
        tg.start_soon(explore_threading)
        tg.start_soon(explore_asyncio)


anyio.run(main)
