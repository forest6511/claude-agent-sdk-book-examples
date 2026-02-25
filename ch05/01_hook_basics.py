"""第5章: Hook の基本構造

PreToolUse / PostToolUse / Stop の3種類の Hook を登録する基本パターン。
HookMatcher の matcher 引数でツール名を絞り込む方法も示す。

実行:
    python ch05/01_hook_basics.py
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


async def my_pre_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """PreToolUse: ツール実行直前に呼ばれる。
    {} を返すと実行を許可。
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    print(f"[PreToolUse] ツール: {tool_name}, 入力: {tool_input}")
    return {}  # 許可


async def my_post_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """PostToolUse: ツール実行成功後に呼ばれる。"""
    result_preview = str(input_data.get("tool_response", ""))[:100]
    print(f"[PostToolUse] 結果: {result_preview}")
    return {}


async def my_stop_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Stop: エージェントループ終了時に呼ばれる。
    {"continue_": False} で終了を許可。
    {"continue_": True, "systemMessage": "..."} でループを継続。
    """
    print("[Stop] エージェントループ終了")
    return {"continue_": False}


options = ClaudeAgentOptions(
    allowed_tools=["Read"],
    permission_mode="bypassPermissions",
    hooks={
        "PreToolUse": [
            HookMatcher(matcher=None, hooks=[my_pre_hook]),  # 全ツールに適用
        ],
        "PostToolUse": [
            HookMatcher(matcher=None, hooks=[my_post_hook]),
        ],
        "Stop": [
            HookMatcher(matcher=None, hooks=[my_stop_hook]),
        ],
    },
)


async def main() -> None:
    async with ClaudeSDKClient(options=options) as client:
        await client.query("requirements.txt を読んで内容を要約してください")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


anyio.run(main)
