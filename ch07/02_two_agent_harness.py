"""第7章: 2エージェント・ハーネスパターン（Spotify Honk）

Initializer（Haiku）がタスクを分析して計画を立て、
Coding Agent（Sonnet）が計画に従い実装する。
Honk プロジェクトが採用した構成。

実行:
    python ch07/02_two_agent_harness.py
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


async def run_harness(task: str) -> None:
    """2エージェント・ハーネスでタスクを実行する。"""
    options = ClaudeAgentOptions(
        agents={
            "initializer": AgentDefinition(
                description="タスク分析と実行計画の立案",
                prompt=(
                    "あなたはソフトウェアタスクの計画立案者です。\n"
                    "タスクを分析し、対象ファイル・実施内容・受け入れ基準を\n"
                    "箇条書きで整理してください。実装は行わないでください。"
                ),
                tools=["Glob", "Read"],
                model="haiku",
            ),
            "coding-agent": AgentDefinition(
                description="計画に基づくコード実装と報告",
                prompt=(
                    "あなたはコーディングエージェントです。\n"
                    "initializer の計画に従い、実装・テスト・完了報告を行います。\n"
                    "受け入れ基準をすべて満たしてから完了を報告してください。"
                ),
                tools=["Read", "Write", "Edit", "Bash"],
                model="sonnet",
            ),
        },
    )

    async for message in query(
        prompt=(
            f"initializer エージェントで計画を立て、\n"
            f"coding-agent エージェントで実装してください。\n"
            f"タスク: {task}"
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
    # デモ: 実際のファイル変更は行わない（計画立案のみ）
    await run_harness(
        "output/ ディレクトリに hello.txt を作成し、"
        "'Hello from two-agent harness!' と書き込む"
    )


anyio.run(main)
