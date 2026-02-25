"""第7章: AgentDefinition によるサブエージェント

コードレビュー + テスト生成という2つの専門エージェントを
AgentDefinition で定義し、オーケストレーターが順番に呼び出す。

実行:
    python ch07/01_agent_definition.py src/auth.py
"""
import anyio
import sys
from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

options = ClaudeAgentOptions(
    agents={
        "code-reviewer": AgentDefinition(
            description="Pythonコードのレビューと品質チェック",
            prompt=(
                "あなたは経験豊富なPythonエンジニアです。\n"
                "セキュリティ・パフォーマンス・可読性の観点でレビューしてください。\n"
                "問題点は重要度（High/Medium/Low）付きで列挙してください。"
            ),
            tools=["Read", "Grep", "Glob"],
            model="sonnet",
        ),
        "test-generator": AgentDefinition(
            description="Pytestのテストコード生成",
            prompt=(
                "あなたはPytestのテストコード生成専門家です。\n"
                "正常系・異常系・境界値のケースを網羅してください。"
            ),
            tools=["Read", "Write"],
            model="sonnet",
        ),
    },
)


async def run_code_quality_pipeline(target_path: str) -> None:
    """コードレビューとテスト生成を順に実行する。"""
    print(f"対象: {target_path}")
    print("Step 1: コードレビュー中...")
    print("Step 2: テストコード生成中...\n")

    async for message in query(
        prompt=(
            f"code-reviewer エージェントを使って {target_path} をレビューし、"
            "次に test-generator エージェントでテストコードの雛形を生成してください。"
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
    target = sys.argv[1] if len(sys.argv) > 1 else "src/auth.py"
    await run_code_quality_pipeline(target)


anyio.run(main)
