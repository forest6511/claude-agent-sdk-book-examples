"""第10章: Agent Skills パターン — Slack 通知スキル

スキルの設計原則（単一責任・最小権限・設定可能性）を実装した
SlackNotifierSkill の例。

実行:
    SLACK_BOT_TOKEN=xoxb-... python ch10/01_slack_skill.py

注意:
    実際に Slack に送信するには SLACK_BOT_TOKEN 環境変数が必要。
    未設定の場合はデモモードで動作します。
"""
import anyio
import os
from dataclasses import dataclass
from typing import Optional
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    tool,
    create_sdk_mcp_server,
    query,
)


@dataclass
class SlackNotifierConfig:
    """Slack 通知スキルの設定。"""
    bot_token: str
    default_channel: str
    mention_on_failure: Optional[str] = None
    demo_mode: bool = False  # True のとき実際の送信をスキップ


class SlackNotifierSkill:
    """Slackにエージェントの作業状況を通知するスキル。

    設計原則:
    - 単一責任: Slack 通知のみ担当
    - 最小権限: send_slack_message ツールのみ
    - 設定可能性: SlackNotifierConfig で環境別に調整
    """

    def __init__(self, config: SlackNotifierConfig):
        self.config = config

    def get_mcp_server(self):
        """スキルのツールを SDK MCP サーバーとして返す。"""
        config = self.config

        @tool(
            "send_slack_message",
            "Slackにメッセージを送信する",
            {"message": str, "channel": str},
        )
        async def send_message(args: dict) -> dict:
            target = args.get("channel") or config.default_channel
            message = args["message"]

            if config.demo_mode:
                result = f"[DEMO] #{target} に送信: {message[:50]}"
                print(f"  Slack送信（デモ）: {result}")
                return {"content": [{"type": "text", "text": result}]}

            try:
                import httpx
                resp = httpx.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {config.bot_token}"},
                    json={"channel": target, "text": message},
                    timeout=10,
                )
                ok = resp.json().get("ok")
                text = "送信成功" if ok else f"送信失敗: {resp.text[:100]}"
            except Exception as e:
                text = f"エラー: {e}"

            return {"content": [{"type": "text", "text": text}]}

        return create_sdk_mcp_server("slack-notifier", tools=[send_message])


async def main() -> None:
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    demo_mode = not bool(bot_token)

    if demo_mode:
        print("SLACK_BOT_TOKEN が未設定のためデモモードで実行します\n")

    config = SlackNotifierConfig(
        bot_token=bot_token or "dummy",
        default_channel="#general",
        demo_mode=demo_mode,
    )
    skill = SlackNotifierSkill(config)
    mcp_server = skill.get_mcp_server()

    options = ClaudeAgentOptions(
        mcp_servers=[mcp_server],
        system_prompt=(
            "あなたは作業完了を Slack で報告するエージェントです。\n"
            "作業が完了したら send_slack_message で #general に報告してください。"
        ),
        max_turns=3,
    )

    async for message in query(
        prompt="デプロイ作業が完了しました。Slack に報告してください。",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


anyio.run(main)
