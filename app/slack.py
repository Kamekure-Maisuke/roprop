import os
from uuid import UUID

import httpx

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK", "")


async def notify_slack(blocks: list[dict]) -> None:
    if not SLACK_WEBHOOK_URL:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(SLACK_WEBHOOK_URL, json={"blocks": blocks})
    except Exception:
        pass


def format_pc_created(
    pc_name: str, pc_id: UUID, model: str, serial: str, assigned_to: str | None
) -> list[dict]:
    """PC作成時のメッセージ"""
    fields = [
        {"type": "mrkdwn", "text": f"*PC名:*\n{pc_name}"},
        {"type": "mrkdwn", "text": f"*モデル:*\n{model}"},
        {"type": "mrkdwn", "text": f"*シリアル番号:*\n{serial}"},
        {
            "type": "mrkdwn",
            "text": f"*割当先:*\n{assigned_to if assigned_to else '未割当'}",
        },
    ]
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "✅ PC作成"},
        },
        {"type": "section", "fields": fields},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"ID: `{pc_id}`"}],
        },
    ]


def format_pc_updated(
    pc_name: str, pc_id: UUID, model: str, serial: str, assigned_to: str | None
) -> list[dict]:
    """PC更新時のメッセージ"""
    fields = [
        {"type": "mrkdwn", "text": f"*PC名:*\n{pc_name}"},
        {"type": "mrkdwn", "text": f"*モデル:*\n{model}"},
        {"type": "mrkdwn", "text": f"*シリアル番号:*\n{serial}"},
        {
            "type": "mrkdwn",
            "text": f"*割当先:*\n{assigned_to if assigned_to else '未割当'}",
        },
    ]
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔄 PC更新"},
        },
        {"type": "section", "fields": fields},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"ID: `{pc_id}`"}],
        },
    ]


def format_pc_deleted(pc_name: str, pc_id: UUID, model: str, serial: str) -> list[dict]:
    """PC削除時のメッセージ"""
    fields = [
        {"type": "mrkdwn", "text": f"*PC名:*\n{pc_name}"},
        {"type": "mrkdwn", "text": f"*モデル:*\n{model}"},
        {"type": "mrkdwn", "text": f"*シリアル番号:*\n{serial}"},
    ]
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🗑️ PC削除"},
        },
        {"type": "section", "fields": fields},
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"ID: `{pc_id}`"}],
        },
    ]
