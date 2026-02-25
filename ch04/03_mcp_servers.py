"""第4章: 外部 MCP サーバーへの接続

McpServerConfig を使って stdio 型・sse 型の外部 MCP サーバーに接続する。
filesystem MCP サーバーと git MCP サーバーの接続例。

前提: Node.js と npx が必要
  npm install -g @modelcontextprotocol/server-filesystem
  npm install -g @modelcontextprotocol/server-git

実行:
    python ch04/03_mcp_servers.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    McpServerConfig,
    AssistantMessage,
    TextBlock,
)


async def main() -> None:
    # stdio 型: 子プロセスを起動して stdio で通信
    options = ClaudeAgentOptions(
        mcp_servers={
            "filesystem": McpServerConfig(
                type="stdio",
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    ".",   # カレントディレクトリをワークスペースとして公開
                ],
            ),
        },
        allowed_tools=[
            "mcp__filesystem__read_file",
            "mcp__filesystem__list_directory",
        ],
        max_turns=5,
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("カレントディレクトリの構成を教えてください")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


anyio.run(main)
