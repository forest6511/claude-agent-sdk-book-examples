"""第4章: カスタムツール — 住宅ローン計算ツール

@tool デコレーターで Python 関数をツールとして定義し、
create_sdk_mcp_server() で in-process MCP サーバーに登録する。

実行:
    python ch04/01_mortgage_calculator.py
"""
import json
import anyio
from typing import Any
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)


@tool(
    "calculate_mortgage",
    "月次ローン返済額を計算する",
    {
        "principal": float,   # 借入額（円）
        "annual_rate": float, # 年利率（例: 0.015 = 1.5%）
        "years": int,         # 返済期間（年）
    },
)
async def calculate_mortgage(args: dict[str, Any]) -> dict[str, Any]:
    principal = args["principal"]
    annual_rate = args["annual_rate"]
    years = args["years"]

    monthly_rate = annual_rate / 12
    n = years * 12
    if monthly_rate == 0:
        monthly = principal / n
    else:
        monthly = principal * monthly_rate / (1 - (1 + monthly_rate) ** -n)

    total = monthly * n
    result = {
        "monthly_payment": round(monthly),
        "total_payment": round(total),
        "total_interest": round(total - principal),
    }
    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}


async def main() -> None:
    server = create_sdk_mcp_server("finance", tools=[calculate_mortgage])
    options = ClaudeAgentOptions(
        mcp_servers={"finance": server},
        allowed_tools=["mcp__finance__calculate_mortgage"],
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "借入3000万円、年利1.5%、35年ローンの月次返済額を計算してください"
        )
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(message, ResultMessage):
                if message.total_cost_usd:
                    print(f"\n費用: ${message.total_cost_usd:.6f}")


anyio.run(main)
