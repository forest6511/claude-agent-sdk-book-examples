"""第5章: 構造化監査ログ Hook

PreToolUse / PostToolUse Hook でツール呼び出しの開始・完了を
JSON 形式で audit.log に記録する。

実行:
    python ch05/03_audit_log_hook.py
    cat audit.log  # ログを確認
"""
import json
import logging
import anyio
from datetime import datetime, UTC
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    AssistantMessage,
    TextBlock,
)
from claude_agent_sdk.types import HookContext, HookInput, HookJSONOutput

# 構造化ログの設定
audit_logger = logging.getLogger("agent.audit")
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler("audit.log")
handler.setFormatter(logging.Formatter("%(message)s"))
audit_logger.addHandler(handler)


async def audit_pre_tool(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """ツール実行前の監査ログを記録する PreToolUse Hook。"""
    audit_logger.info(json.dumps({
        "event": "tool_call_start",
        "timestamp": datetime.now(UTC).isoformat(),
        "tool_use_id": tool_use_id,
        "tool": input_data.get("tool_name"),
        "input": input_data.get("tool_input"),
    }, ensure_ascii=False))
    return {}


async def audit_post_tool(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """ツール実行後の監査ログを記録する PostToolUse Hook。"""
    result_preview = str(input_data.get("tool_response", ""))[:200]
    audit_logger.info(json.dumps({
        "event": "tool_call_end",
        "timestamp": datetime.now(UTC).isoformat(),
        "tool_use_id": tool_use_id,
        "tool": input_data.get("tool_name"),
        "result_preview": result_preview,
    }, ensure_ascii=False))
    return {}


options = ClaudeAgentOptions(
    allowed_tools=["Read"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[audit_pre_tool]),
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[audit_post_tool]),
        ],
    },
)


async def main() -> None:
    async with ClaudeSDKClient(options=options) as client:
        await client.query("requirements.txt を読んで要約してください")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

    print("\naudit.log を確認してください:")
    try:
        with open("audit.log") as f:
            print(f.read())
    except FileNotFoundError:
        print("(audit.log が生成されていません)")


anyio.run(main)
