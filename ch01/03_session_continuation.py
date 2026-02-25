"""第1章: ClaudeSDKClient によるマルチターン会話

ClaudeSDKClient は async with ブロック内で会話履歴を自動維持する。
前の質問の文脈を引き継いで次の質問ができる。

実行:
    python ch01/03_session_continuation.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        allowed_tools=["Read"],
        max_turns=10,
    )

    async with ClaudeSDKClient(options=options) as client:
        # 1回目の質問
        await client.query("東京の人口を教えて")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # 前の会話を引き継いで続ける
        await client.query("大阪はどうですか？")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


anyio.run(main)
