"""第8章: 3層検証アーキテクチャ（Spotify Honk パターン）

Layer 1: 決定論的チェック（テスト実行）
Layer 2: LLM-as-Judge（Haiku によるコードレビュー）
Layer 3: Stop Hook（両層が PASS のときのみ終了）

実行:
    python ch08/01_three_layer_verification.py
"""
import anyio
import anthropic
import json
import re
import subprocess
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    TextBlock,
    query,
)
from claude_agent_sdk.types import HookContext, HookInput, HookJSONOutput

_judge_client = anthropic.Anthropic()


def run_deterministic_checks(test_command: str) -> dict:
    """Layer 1: テストを実行して pass/fail を返す。"""
    try:
        result = subprocess.run(
            test_command.split(),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "passed": result.returncode == 0,
            "output": (result.stdout + result.stderr)[:500],
        }
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return {"passed": False, "output": str(e)}


def run_llm_judge(content: str) -> dict:
    """Layer 2: Haiku でコードをレビューして passed/feedback を返す。"""
    if not content:
        return {"passed": True, "feedback": ""}
    response = _judge_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system="コードレビュアーとして問題点をJSONで返してください。",
        messages=[{
            "role": "user",
            "content": (
                f"以下のコードに重大な問題はありますか？\n{content[:1000]}\n\n"
                "{'passed': bool, 'feedback': 'string'} の形式で返してください。"
            ),
        }],
    )
    text = response.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"passed": True, "feedback": ""}


def make_three_layer_stop_hook(test_command: str):
    """3層検証 Stop Hook を生成するファクトリ関数。"""
    async def three_layer_stop(
        input_data: HookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> HookJSONOutput:
        # Layer 1: 決定論的チェック
        layer1 = run_deterministic_checks(test_command)
        if not layer1["passed"]:
            return {
                "continue_": True,
                "systemMessage": (
                    f"検証失敗（Layer 1 - テスト）:\n{layer1['output']}\n"
                    "問題を修正してから再度完了を報告してください。"
                ),
            }

        # Layer 2: LLM-as-Judge
        last_msg = input_data.get("last_assistant_message", "")
        layer2 = run_llm_judge(last_msg)
        if not layer2["passed"]:
            return {
                "continue_": True,
                "systemMessage": (
                    f"検証失敗（Layer 2 - LLM Judge）:\n{layer2['feedback']}\n"
                    "フィードバックを踏まえて修正してください。"
                ),
            }

        print("3層検証: すべて PASS → 完了")
        return {"continue_": False}

    return three_layer_stop


async def main() -> None:
    # output/ ディレクトリを作成
    import os
    os.makedirs("output", exist_ok=True)

    stop_hook = make_three_layer_stop_hook("python -m pytest tests/ -q --no-header 2>&1 || true")

    options = ClaudeAgentOptions(
        allowed_tools=["Write"],
        permission_mode="bypassPermissions",
        system_prompt=(
            "Pythonのフィボナッチ数列生成関数を output/fib.py に書いてください。\n"
            "型ヒント付き・docstring付きで実装してください。"
        ),
        max_turns=5,
        hooks={
            "Stop": [HookMatcher(matcher=None, hooks=[stop_hook])],
        },
    )

    async for message in query(
        prompt="フィボナッチ数列を生成する関数を output/fib.py に書いてください",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


anyio.run(main)
