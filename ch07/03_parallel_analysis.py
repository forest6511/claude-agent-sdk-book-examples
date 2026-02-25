"""第7章: 並列エージェントパターン

anyio.create_task_group() で複数のファイルを並列に分析し、
anyio.Semaphore() でレートリミットを考慮した同時実行数を制限する。

実行:
    python ch07/03_parallel_analysis.py
"""
import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)


async def analyze_file(file_path: str) -> dict:
    """単一ファイルを分析するエージェントを実行する。"""
    options = ClaudeAgentOptions(
        system_prompt="コードを分析して、複雑度・行数・主要関数を簡潔に報告してください。",
        allowed_tools=["Read"],
        model="claude-haiku-4-5-20251001",
        max_turns=3,
    )
    result = ""
    async for message in query(
        prompt=f"{file_path} を分析してください",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result = block.text
    return {"file": file_path, "analysis": result}


async def analyze_codebase_parallel(
    file_paths: list[str],
    max_concurrent: int = 3,
) -> list[dict]:
    """複数ファイルをセマフォ付き並列で分析する。"""
    semaphore = anyio.Semaphore(max_concurrent)
    results: list[dict] = []

    async def analyze_with_limit(path: str) -> None:
        async with semaphore:
            r = await analyze_file(path)
            results.append(r)
            print(f"  完了: {path}")

    async with anyio.create_task_group() as tg:
        for path in file_paths:
            tg.start_soon(analyze_with_limit, path)

    return results


async def main() -> None:
    # デモ用ファイルリスト（実在しなくても分析を試みる）
    files = [
        "src/auth.py",
        "src/models.py",
        "src/api.py",
        "tests/test_auth.py",
    ]

    print(f"{len(files)} ファイルを並列分析中（最大3同時）...\n")
    results = await analyze_codebase_parallel(files, max_concurrent=3)

    print("\n=== 分析結果 ===")
    for r in results:
        print(f"\n[{r['file']}]")
        print(r["analysis"][:200] + "..." if len(r["analysis"]) > 200 else r["analysis"])


anyio.run(main)
