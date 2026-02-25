"""第3章: 会話履歴の永続化

サーバー再起動後も会話が途切れないよう、履歴を JSON ファイルに保存して
次のセッションのシステムプロンプトとして注入するパターン。

実行:
    python ch03/03_session_persistence.py user1 "Python の asyncio を教えて"
    python ch03/03_session_persistence.py user1 "もう少し詳しく"  # 前の文脈を引き継ぐ
"""
import json
import sys
import anyio
from pathlib import Path
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


def save_history(history: list[dict], user_id: str) -> None:
    path = SESSIONS_DIR / f"{user_id}.json"
    path.write_text(json.dumps(history, ensure_ascii=False), encoding="utf-8")


def load_history(user_id: str) -> list[dict]:
    path = SESSIONS_DIR / f"{user_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


async def chat_with_memory(user_id: str, message: str) -> str:
    history = load_history(user_id)

    # 過去の履歴をシステムプロンプトにコンテキストとして注入
    context = ""
    if history:
        lines = "\n".join(f"{h['role']}: {h['content']}" for h in history[-6:])
        context = f"これまでの会話（最新6件）:\n{lines}\n\n"

    options = ClaudeAgentOptions(
        system_prompt=context + "ユーザーの質問に答えてください。",
        max_turns=5,
    )

    result = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(message)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        result = block.text

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": result})
    save_history(history, user_id)
    return result


async def main() -> None:
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"
    message = sys.argv[2] if len(sys.argv) > 2 else "こんにちは"
    reply = await chat_with_memory(user_id, message)
    print(f"Claude: {reply}")


anyio.run(main)
