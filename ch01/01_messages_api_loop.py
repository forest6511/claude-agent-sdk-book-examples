"""第1章: Messages API でのエージェントループ（比較用）

Agent SDK を使わずに raw Messages API でエージェントループを実装した例。
Agent SDK との違いを理解するための比較用コードです。

実行:
    python ch01/01_messages_api_loop.py
"""
import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def list_files(path: str) -> str:
    import os as _os
    return json.dumps(_os.listdir(path))


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


TOOLS = [
    {
        "name": "list_files",
        "description": "指定ディレクトリのファイル一覧を返す",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": "ファイルの内容を返す",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def run_agent(user_message: str) -> str:
    """Messages API でエージェントループを手動実装する。"""
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "list_files":
                        result = list_files(**block.input)
                    elif block.name == "read_file":
                        result = read_file(**block.input)
                    else:
                        result = "Unknown tool"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    return ""


if __name__ == "__main__":
    # カレントディレクトリのファイル一覧を取得するエージェントを実行
    result = run_agent("カレントディレクトリのファイル一覧を教えて")
    print(result)
