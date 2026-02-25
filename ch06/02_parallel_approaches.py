"""第6章: 並列アプローチ比較（Best-of-N パターン）

同じ前提条件から複数の実装アプローチを anyio.create_task_group() で
並列に試し、最も詳細な回答を選ぶ。

注意: 並列 API リクエストを発行するためコストがかかります。

実行:
    python ch06/02_parallel_approaches.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
)

BASE_CONTEXT = (
    "Pythonでメール送信システムを設計する。"
    "制約: Python 3.11以上、外部ライブラリは requirements.txt に記載のもののみ。"
)


async def try_approach(approach_prompt: str) -> str:
    """単一のアプローチを試して応答テキストを返す。"""
    options = ClaudeAgentOptions(
        system_prompt=f"あなたはPythonエキスパートです。\n\n【設計前提】\n{BASE_CONTEXT}",
        max_turns=3,
    )
    result = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(approach_prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result = block.text
    return result


async def best_of_n(approaches: list[str]) -> str:
    """複数のアプローチを並列実行して最も長い回答を返す（詳細さの代理指標）。"""
    results: list[str] = [""] * len(approaches)

    async def _run(idx: int, prompt: str) -> None:
        results[idx] = await try_approach(prompt)

    async with anyio.create_task_group() as tg:
        for idx, approach in enumerate(approaches):
            tg.start_soon(_run, idx, approach)

    return max(results, key=len)


async def main() -> None:
    print("3つのアプローチを並列探索中...")
    best = await best_of_n([
        "smtplib を使った実装コードを示してください",
        "SendGrid API を使った実装コードを示してください",
        "最もシンプルな実装コードを示してください",
    ])
    print(f"\n最も詳細な回答:\n{best[:500]}...")


anyio.run(main)
