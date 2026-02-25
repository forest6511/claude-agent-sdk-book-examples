"""第6章: セッション外部管理パターン

SessionState データクラスで会話の要約・決定事項・コストを管理し、
ファイルシステムに保存して次のセッションに引き継ぐ。

実行:
    python ch06/01_session_state.py
"""
import anyio
import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


@dataclass
class SessionState:
    """アプリケーションが管理するセッション状態。"""
    session_id: str
    user_id: str
    summary: str = ""
    key_decisions: list[str] = field(default_factory=list)
    turn_count: int = 0
    total_cost_usd: float = 0.0


def save_state(state: SessionState) -> None:
    path = SESSIONS_DIR / f"{state.session_id}.json"
    path.write_text(json.dumps(asdict(state), ensure_ascii=False), encoding="utf-8")


def load_state(session_id: str) -> SessionState | None:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return SessionState(**data)


def new_state(user_id: str) -> SessionState:
    return SessionState(session_id=str(uuid.uuid4()), user_id=user_id)


async def run_turn(state: SessionState, user_message: str) -> tuple[str, SessionState]:
    """1ターン実行して応答と更新済み状態を返す。"""
    # 過去の要約・決定事項をシステムプロンプトに注入
    context = ""
    if state.summary:
        context += f"\n\n【過去の会話の要約】\n{state.summary}"
    if state.key_decisions:
        decisions_text = "\n".join(f"- {d}" for d in state.key_decisions)
        context += f"\n\n【確定した決定事項】\n{decisions_text}"

    options = ClaudeAgentOptions(
        system_prompt=f"あなたは役立つアシスタントです。{context}",
        max_turns=3,
    )

    reply = ""
    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_message)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        reply = block.text
            elif isinstance(message, ResultMessage):
                state.turn_count += message.num_turns
                state.total_cost_usd += message.total_cost_usd or 0.0

    return reply, state


async def main() -> None:
    # セッション1
    state = new_state("demo_user")
    reply1, state = await run_turn(state, "Pythonのデータパイプライン設計を相談したい")
    print(f"[セッション1] Claude: {reply1[:300]}...\n")
    state.summary = f"Pythonデータパイプライン設計を相談した。回答概要: {reply1[:200]}"
    save_state(state)

    # セッション2（前回の要約を引き継ぐ）
    reply2, state = await run_turn(state, "前回の設計でテストはどう書くべきか？")
    print(f"[セッション2] Claude: {reply2[:300]}...")
    print(f"\n累積コスト: ${state.total_cost_usd:.6f}")


anyio.run(main)
