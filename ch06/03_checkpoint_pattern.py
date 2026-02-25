"""第6章: チェックポイントパターン

長時間タスクで中間状態を JSON ファイルに保存し、
中断・再実行時にコストをかけずに再開できるパターン。

実行:
    python ch06/03_checkpoint_pattern.py design-email-system
    python ch06/03_checkpoint_pattern.py design-email-system  # 再実行: チェックポイントから再開
"""
import anyio
import json
import sys
from pathlib import Path
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

CHECKPOINT_DIR = Path("checkpoints")
CHECKPOINT_DIR.mkdir(exist_ok=True)


async def run_with_checkpoints(
    task_id: str,
    initial_message: str,
    system_prompt: str = "あなたは役立つアシスタントです。",
) -> str:
    """チェックポイント付きでエージェントを実行する。"""
    checkpoint_path = CHECKPOINT_DIR / f"{task_id}.json"

    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        progress_summary = checkpoint.get("progress_summary", "")
        print(f"チェックポイントから再開: {task_id}")
        resume_prompt = (
            f"前回の作業の続きです。\n\n"
            f"【前回の進捗】\n{progress_summary}\n\n"
            "続きの作業を行ってください。"
        )
    else:
        resume_prompt = initial_message

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        max_turns=10,
    )

    result = ""
    total_turns = 0
    async with ClaudeSDKClient(options=options) as client:
        await client.query(resume_prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result = block.text
            elif isinstance(message, ResultMessage):
                total_turns = message.num_turns

    # 完了後にチェックポイントを保存
    checkpoint_data = {
        "task_id": task_id,
        "total_turns": total_turns,
        "progress_summary": result[:500],
        "status": "completed",
    }
    checkpoint_path.write_text(
        json.dumps(checkpoint_data, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"完了: {total_turns} ターン / チェックポイント保存済み")
    return result


async def main() -> None:
    task_id = sys.argv[1] if len(sys.argv) > 1 else "demo-task"
    result = await run_with_checkpoints(
        task_id=task_id,
        initial_message="Pythonでメール送信システムを設計してコードを示してください",
    )
    print(f"\n結果:\n{result[:400]}...")


anyio.run(main)
