"""第7章: 階層型エージェント（Supervisor パターン）

Supervisor が全体目標を管理し、
Frontend / Backend / Testing の専門エージェントに委任する。

実行:
    python ch07/04_hierarchical_agents.py
"""
import anyio
from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def run_supervisor(task: str) -> None:
    """階層型エージェントでタスクを実行する。"""
    options = ClaudeAgentOptions(
        agents={
            "frontend-agent": AgentDefinition(
                description="UIコンポーネントとHTMLの生成",
                prompt=(
                    "あなたはフロントエンドエンジニアです。\n"
                    "HTML・CSS・JavaScriptを使ったUIを設計してください。"
                ),
                tools=["Read", "Write"],
                model="sonnet",
            ),
            "backend-agent": AgentDefinition(
                description="APIエンドポイントとビジネスロジックの設計",
                prompt=(
                    "あなたはバックエンドエンジニアです。\n"
                    "FastAPI または Flask でAPIを設計してください。"
                ),
                tools=["Read", "Write"],
                model="sonnet",
            ),
            "testing-agent": AgentDefinition(
                description="テストケースの生成と品質検証",
                prompt=(
                    "あなたはQAエンジニアです。\n"
                    "Pytest でテストケースを生成してください。"
                ),
                tools=["Read", "Write"],
                model="haiku",
            ),
        },
    )

    async for message in query(
        prompt=(
            f"以下のタスクを担当エージェントに振り分けて実行してください:\n"
            f"{task}\n\n"
            "frontend-agent でUI設計、backend-agent でAPI設計、"
            "testing-agent でテスト戦略を立案してください。"
        ),
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd or 0.0
            print(f"\n完了 | {message.num_turns} ターン | 費用: ${cost:.6f}")


async def main() -> None:
    await run_supervisor(
        "シンプルなTodoリストアプリの設計（フロントエンド・バックエンド・テスト）"
    )


anyio.run(main)
