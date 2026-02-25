"""第3章: ClaudeSDKClient によるマルチターン会話

ClaudeSDKClient は async with ブロック内で会話履歴を自動維持する。
2回目の質問で「大阪はどうですか？」という曖昧な問いが成立するのは、
前の「東京の人口」という文脈が引き継がれているから。

実行:
    python ch03/02_multi_turn_conversation.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)


async def conversation() -> None:
    options = ClaudeAgentOptions(
        system_prompt="あなたは地理に詳しいアシスタントです。",
        max_turns=5,
    )
    async with ClaudeSDKClient(options=options) as client:
        # ターン1
        await client.query("東京の人口を教えて")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

        # ターン2（「東京」の文脈を引き継ぐ）
        await client.query("大阪と比べてどうですか？")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


anyio.run(conversation)
