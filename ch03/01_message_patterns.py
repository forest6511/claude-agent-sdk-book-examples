"""第3章: メッセージハンドリングの3パターン

パターン1: 最終回答のみ取得（Q&A、ツール過程を隠す）
パターン2: ツール実行ログを記録（監査用）
パターン3: 完了条件チェック付き（本番システム向け）

実行:
    python ch03/01_message_patterns.py
"""
import anyio
import logging
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ── パターン1: 最終回答のみ取得 ──────────────────────────────────────
async def ask(question: str) -> str:
    """最後の AssistantMessage のテキストだけを返す。"""
    result = ""
    options = ClaudeAgentOptions(max_turns=5)
    async for message in query(prompt=question, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result = block.text
    return result


# ── パターン2: ツール実行ログを記録 ─────────────────────────────────
async def run_with_logging(task: str) -> str:
    """ツール呼び出しを INFO ログに記録しながら実行する。"""
    result = ""
    options = ClaudeAgentOptions(max_turns=10)
    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    logger.info("tool_call: %s(%s)", block.name, block.input)
                elif isinstance(block, TextBlock):
                    result = block.text
        elif isinstance(message, ResultMessage):
            logger.info(
                "query_complete: turns=%d cost=$%.6f stop=%s",
                message.num_turns,
                message.total_cost_usd or 0.0,
                message.stop_reason,
            )
    return result


# ── パターン3: 完了条件チェック付き ─────────────────────────────────
async def run_safely(task: str) -> tuple[str, bool]:
    """(回答テキスト, 成功フラグ) のタプルを返す。
    stop_reason が "max_turns" の場合は失敗扱い。
    """
    result = ""
    success = True
    options = ClaudeAgentOptions(max_turns=10)
    async for message in query(prompt=task, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result = block.text
        elif isinstance(message, ResultMessage):
            if message.stop_reason == "max_turns":
                success = False
    return result, success


async def main() -> None:
    # パターン1
    print("=== パターン1: 最終回答のみ ===")
    answer = await ask("Pythonの asyncio と anyio の違いを1行で説明して")
    print(answer)

    # パターン3
    print("\n=== パターン3: 完了条件チェック ===")
    reply, ok = await run_safely("「こんにちは」と返してください")
    print(f"成功: {ok}, 回答: {reply}")


anyio.run(main)
