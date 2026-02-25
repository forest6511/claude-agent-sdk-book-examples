"""第4章: 非同期 HTTP ツール — GitHub リポジトリ情報取得

httpx を使った非同期ツールの実装パターン。
タイムアウト・HTTPエラーのハンドリングを含む。

依存: pip install httpx

実行:
    python ch04/02_github_tool.py
"""
import anyio
import httpx
from typing import Any
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)


@tool(
    "get_github_repo",
    "GitHub リポジトリの情報を取得する",
    {
        "owner": str,  # リポジトリオーナー名
        "repo": str,   # リポジトリ名
    },
)
async def get_github_repo(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        text = (
            f"名前: {data['full_name']}\n"
            f"説明: {data.get('description', '説明なし')}\n"
            f"スター: {data['stargazers_count']}\n"
            f"言語: {data.get('language', '不明')}"
        )
        return {"content": [{"type": "text", "text": text}]}
    except httpx.TimeoutException:
        msg = "エラー: GitHub API がタイムアウトしました（10秒）"
        return {"content": [{"type": "text", "text": msg}], "is_error": True}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            msg = f"エラー: {owner}/{repo} が見つかりません"
        else:
            msg = f"エラー: GitHub API エラー ({e.response.status_code})"
        return {"content": [{"type": "text", "text": msg}], "is_error": True}


async def main() -> None:
    server = create_sdk_mcp_server("github", tools=[get_github_repo])
    options = ClaudeAgentOptions(
        mcp_servers={"github": server},
        allowed_tools=["mcp__github__get_github_repo"],
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "anthropics/claude-agent-sdk-python リポジトリの情報を教えてください"
        )
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)


anyio.run(main)
