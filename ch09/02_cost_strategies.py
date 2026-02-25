"""第9章: コスト削減戦略（ツール出力制限・バッチ処理）

戦略3: カスタムツールでファイル読み取り行数を制限する
戦略5: Messages Batch API で大量処理をコスト50%削減

実行:
    python ch09/02_cost_strategies.py
"""
import anyio
import re
import time
from pathlib import Path
import anthropic
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    tool,
    create_sdk_mcp_server,
    query,
)


# ── 戦略3: ツール出力の制限 ──────────────────────────────────

@tool(
    "read_file_chunked",
    "ファイルを指定行数に制限して読み取る（トークン節約）",
    {
        "path": str,
        "start_line": int,
        "max_lines": int,
    },
)
async def read_file_chunked(args: dict) -> dict:
    """ファイルを分割して読み取るツール。全体読み取りによるトークン爆発を防ぐ。"""
    path = args["path"]
    start = args.get("start_line", 1)
    max_lines = args.get("max_lines", 50)

    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {"content": [{"type": "text", "text": f"ファイルが見つかりません: {path}"}]}

    total = len(lines)
    selected = lines[start - 1: start - 1 + max_lines]
    footer = f"\n--- {start}〜{start + len(selected) - 1}行 / 全{total}行 ---"
    text = "\n".join(selected) + footer
    return {"content": [{"type": "text", "text": text}]}


@tool(
    "search_in_file",
    "ファイル内でパターンに一致する行を検索する（最大20件）",
    {"path": str, "pattern": str},
)
async def search_in_file(args: dict) -> dict:
    """正規表現でファイル内を検索するツール。無関係な行のトークン消費を防ぐ。"""
    path = args["path"]
    pattern = args["pattern"]

    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {"content": [{"type": "text", "text": f"ファイルが見つかりません: {path}"}]}

    matches = []
    for i, line in enumerate(lines, 1):
        if re.search(pattern, line):
            matches.append(f"{i}: {line}")
            if len(matches) >= 20:
                matches.append("... (20件で打ち切り)")
                break
    result = "\n".join(matches) if matches else "一致なし"
    return {"content": [{"type": "text", "text": result}]}


async def run_with_chunked_tools(target_file: str) -> None:
    """チャンク読み取りツールでトークン消費を抑えたエージェントを実行。"""
    mcp_server = create_sdk_mcp_server(
        "chunked-reader",
        tools=[read_file_chunked, search_in_file],
    )
    options = ClaudeAgentOptions(
        mcp_servers=[mcp_server],
        system_prompt=(
            "ファイルを read_file_chunked で50行ずつ読み取ってください。\n"
            "特定のパターンを探す場合は search_in_file を使ってください。"
        ),
        max_turns=5,
    )
    print(f"チャンク読み取りモードで {target_file} を分析...")
    async for message in query(
        prompt=f"{target_file} の構造を分析してください（先頭50行から始めてください）",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text[:400])


# ── 戦略5: Messages Batch API ──────────────────────────────────

def process_with_batch_api(prompts: list[str]) -> list[str]:
    """Messages Batch API で大量のプロンプトをまとめて処理する（50%コスト削減）。"""
    client = anthropic.Anthropic()

    requests = [
        {
            "custom_id": f"req_{i}",
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 256,
                "messages": [{"role": "user", "content": prompt}],
            },
        }
        for i, prompt in enumerate(prompts)
    ]

    print(f"バッチ送信: {len(requests)} 件...")
    batch = client.messages.batches.create(requests=requests)
    print(f"バッチID: {batch.id}")

    # 完了を待機（デモのためタイムアウトを短めに設定）
    max_wait = 300  # 5分
    waited = 0
    while waited < max_wait:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        print(f"処理中... ({waited}s)")
        time.sleep(15)
        waited += 15

    results = [""] * len(prompts)
    for result in client.messages.batches.results(batch.id):
        idx = int(result.custom_id.split("_")[1])
        if result.result.type == "succeeded":
            results[idx] = result.result.message.content[0].text

    return results


async def main() -> None:
    print("=== 戦略3: チャンク読み取りツール ===")
    await run_with_chunked_tools("requirements.txt")

    print("\n=== 戦略5: Batch API（コスト50%削減）===")
    print("注意: 実際の Batch API 呼び出しはコメントアウトしています。")
    print("本番では process_with_batch_api() を直接呼び出してください。")
    # 実際に実行する場合はコメントを解除:
    # sample_prompts = [
    #     "Pythonの利点を1文で教えてください",
    #     "TypeScriptの利点を1文で教えてください",
    #     "Goの利点を1文で教えてください",
    # ]
    # results = process_with_batch_api(sample_prompts)
    # for i, r in enumerate(results):
    #     print(f"[{i}] {r[:100]}")


anyio.run(main)
