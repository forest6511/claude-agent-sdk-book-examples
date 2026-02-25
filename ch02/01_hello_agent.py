"""第2章: 最初のエージェント

カスタムツール（echo）を定義して ClaudeSDKClient で実行する完全な例。
SDK の基本フローを確認するための Hello World。

実行:
    python ch02/01_hello_agent.py
"""
import anyio
from typing import Any
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
)


@tool("echo", "メッセージをそのまま返す", {"message": str})
async def echo(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Echo: {args['message']}"}]}


async def main() -> None:
    server = create_sdk_mcp_server("demo", tools=[echo])
    options = ClaudeAgentOptions(
        mcp_servers={"demo": server},
        allowed_tools=["mcp__demo__echo"],
        system_prompt=(
            "あなたは echo ツールを使ってメッセージを確認するエージェントです。"
        ),
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("「Hello, Agent SDK!」をエコーしてください")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        print(f"[ツール] {block.name}({block.input})")
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    print(f"費用: ${message.total_cost_usd:.6f}")


anyio.run(main)
