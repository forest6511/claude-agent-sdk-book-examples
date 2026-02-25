"""第5章: ロールベースアクセス制御 Hook

PreToolUse Hook でツールごとに必要なロールを定義し、
ユーザーのロールに基づいてツール実行を許可・拒否する。

実行:
    python ch05/02_rbac_hook.py
"""
import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    AssistantMessage,
    TextBlock,
)
from claude_agent_sdk.types import HookContext, HookInput, HookJSONOutput

# ツールごとに必要なロールを定義
TOOL_PERMISSIONS: dict[str, set[str]] = {
    "Read":  {"viewer", "editor", "admin"},
    "Write": {"editor", "admin"},
    "Bash":  {"admin"},
}

# ユーザーロール（実際はDBやセッション情報から取得）
USER_ROLES: dict[str, set[str]] = {
    "alice": {"editor", "analyst"},
    "bob":   {"viewer"},
    "admin_user": {"admin"},
}

# 現在のリクエストユーザーID（実際は認証トークンなどから取得）
CURRENT_USER_ID = "alice"


async def rbac_check(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """ロールベースアクセス制御を実装する PreToolUse Hook。"""
    tool_name = input_data.get("tool_name", "")
    required_roles = TOOL_PERMISSIONS.get(tool_name, set())

    if not required_roles:
        return {}  # 権限設定のないツールは許可

    user_roles = USER_ROLES.get(CURRENT_USER_ID, set())
    if required_roles & user_roles:  # 積集合が空でなければ許可
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"権限エラー: '{tool_name}' の実行には {required_roles} ロールが必要です。"
                f"現在のロール: {user_roles}"
            ),
        }
    }


options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[rbac_check]),
        ],
    },
)


async def main() -> None:
    # Alice は Read/Write は可能だが Bash は不可
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "ls -la を実行して、次に output.txt に結果を書いてください"
        )
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
    # → Bash がブロックされ、Claude は権限エラーを受け取る


anyio.run(main)
