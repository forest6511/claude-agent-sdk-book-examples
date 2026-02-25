"""第8章: コンテキストエンジニアリング（Honk のアプローチ）

リポジトリ固有のコンテキスト（CLAUDE.md・コーディング規約・
最近のコミット）をシステムプロンプトに注入して品質を高める。

実行:
    python ch08/02_context_engineering.py
"""
import anyio
import subprocess
from pathlib import Path
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)


def build_repo_context(repo_path: str = ".") -> str:
    """リポジトリ固有のコンテキストを構築する。"""
    context_parts = []
    root = Path(repo_path)

    # CLAUDE.md があれば読み込む
    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8")[:1000]
        context_parts.append(f"=== リポジトリガイド ===\n{content}")

    # スタイルガイドがあれば読み込む
    style_guide = root / ".style.md"
    if style_guide.exists():
        content = style_guide.read_text(encoding="utf-8")[:500]
        context_parts.append(f"=== コーディング規約 ===\n{content}")

    # 最近のコミット履歴（コミットスタイルの参考に）
    try:
        recent = subprocess.run(
            ["git", "log", "--oneline", "-5"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if recent:
            context_parts.append(f"=== 最近のコミット例 ===\n{recent}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return "\n\n".join(context_parts) if context_parts else "(コンテキストなし)"


async def run_with_context(task: str, repo_path: str = ".") -> None:
    """リポジトリコンテキスト付きでエージェントを実行する。"""
    context = build_repo_context(repo_path)
    print(f"コンテキスト長: {len(context)} 文字\n")

    options = ClaudeAgentOptions(
        system_prompt=(
            "あなたはコーディングエージェントです。\n\n"
            f"【リポジトリ情報】\n{context}"
        ),
        allowed_tools=["Read", "Glob"],
        max_turns=3,
    )

    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def main() -> None:
    await run_with_context(
        "このリポジトリのコーディングスタイルと最近の変更傾向を教えてください"
    )


anyio.run(main)
