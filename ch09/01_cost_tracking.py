"""第9章: コスト追跡とモデル使い分け

CostTracker でクエリごとの費用を記録し、
タスクの複雑さに応じて Haiku / Sonnet を自動選択する。

実行:
    python ch09/01_cost_tracking.py
"""
import anyio
from dataclasses import dataclass, field
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


@dataclass
class CostTracker:
    """クエリごとのコストを記録するトラッカー。"""
    total_usd: float = 0.0
    queries: list[dict] = field(default_factory=list)

    def record(self, model: str, prompt: str, cost_usd: float, turns: int) -> None:
        self.total_usd += cost_usd
        self.queries.append({
            "model": model,
            "prompt_preview": prompt[:50],
            "cost_usd": cost_usd,
            "turns": turns,
        })

    def report(self) -> None:
        print("\n=== コストレポート ===")
        for i, q in enumerate(self.queries, 1):
            print(
                f"  [{i}] {q['model']}: ${q['cost_usd']:.6f} "
                f"({q['turns']} turns) - {q['prompt_preview']}..."
            )
        jpy = self.total_usd * 150
        print(f"  合計: ${self.total_usd:.6f} (約¥{jpy:.1f})")


async def run_tracked(
    model: str, prompt: str, tracker: CostTracker
) -> str:
    """コストを記録しながらクエリを実行する。"""
    options = ClaudeAgentOptions(
        model=model,
        max_turns=3,
        system_prompt="簡潔に回答してください。",
    )
    texts: list[str] = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    texts.append(block.text)
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd or 0.0
            turns = message.num_turns or 0
            tracker.record(model, prompt, cost, turns)
    return " ".join(texts)


async def smart_route(task: str, tracker: CostTracker) -> str:
    """タスクの複雑さに応じてモデルを選択する。"""
    # シンプルなタスクは Haiku（Sonnet の約1/12のコスト）
    simple_keywords = ["分類", "抽出", "要約", "変換", "翻訳", "一覧"]
    if any(kw in task for kw in simple_keywords):
        model = "claude-haiku-4-5-20251001"
    else:
        model = "claude-sonnet-4-6"

    print(f"ルーティング: '{task[:30]}...' → {model}")
    return await run_tracked(model, task, tracker)


async def main() -> None:
    tracker = CostTracker()

    tasks = [
        "次の単語を英語に翻訳してください: 桜、富士山、侍",
        "Pythonでシングルトンパターンを実装する最も良い方法を教えてください",
        "東京・大阪・名古屋を人口順に並べ替えてください",
    ]

    for task in tasks:
        await smart_route(task, tracker)

    tracker.report()


anyio.run(main)
