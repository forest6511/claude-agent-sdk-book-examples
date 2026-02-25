"""第5章: LLM-as-Judge Stop Hook（Spotify Honk パターン）

Stop Hook で別の Claude（Haiku）を呼び出してコード品質を検証し、
問題があれば {"continue_": True} でループを継続させる。
Spotify の Honk プロジェクトが採用した3層検証のLayer 2。

実行:
    python ch05/04_llm_judge_stop_hook.py
"""
import json
import re
import anyio
import anthropic
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    AssistantMessage,
    TextBlock,
)
from claude_agent_sdk.types import HookContext, HookInput, HookJSONOutput

_judge_client = anthropic.Anthropic()
_last_written_code: dict[str, str] = {}


async def capture_written_code(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """PostToolUse Hook: Write ツールで書き込まれた .py コードを保存。"""
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if file_path.endswith(".py"):
        _last_written_code["latest"] = tool_input.get("content", "")
    return {}


def _judge_code_quality(code: str) -> dict:
    """Haiku でコードをレビューして {"passed": bool, "issues": str} を返す。"""
    response = _judge_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system="コードレビュアーとして、問題点があればJSONで返してください。",
        messages=[{
            "role": "user",
            "content": (
                f"以下のコードをレビューしてください:\n{code}\n\n"
                '{"passed": true/false, "issues": "問題点"} の形式で返答してください。'
            ),
        }],
    )
    match = re.search(r"\{.*\}", response.content[0].text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"passed": True, "issues": ""}


async def llm_judge_stop(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> HookJSONOutput:
    """Stop Hook: LLM-as-Judge でコード品質を検証する。"""
    generated_code = _last_written_code.get("latest")
    if not generated_code:
        return {"continue_": False}

    verdict = _judge_code_quality(generated_code)
    if verdict["passed"]:
        return {"continue_": False}  # 品質 OK → 終了

    return {
        "continue_": True,
        "systemMessage": (
            f"コード品質チェックで問題が見つかりました:\n"
            f"{verdict['issues']}\n"
            "修正してから再度報告してください。"
        ),
    }


options = ClaudeAgentOptions(
    allowed_tools=["Write"],
    permission_mode="bypassPermissions",
    system_prompt="Pythonコードを output/result.py に書いてください。",
    max_turns=5,
    hooks={
        "PostToolUse": [
            HookMatcher(matcher="Write", hooks=[capture_written_code]),
        ],
        "Stop": [
            HookMatcher(matcher=None, hooks=[llm_judge_stop]),
        ],
    },
)


async def main() -> None:
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "フィボナッチ数列を生成する関数を output/result.py に書いてください"
        )
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")


anyio.run(main)
