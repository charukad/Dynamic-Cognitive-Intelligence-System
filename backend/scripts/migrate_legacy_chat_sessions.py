"""Migrate legacy file-based chat sessions into PostgreSQL chat tables."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.domain.models import ChatMessageRole, ChatMessageSender, ChatMessageStatus
from src.infrastructure.database.postgres_client import postgres_client
from src.infrastructure.repositories.chat_repository import chat_repository


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _detect_role(sender: str) -> ChatMessageRole:
    normalized = (sender or "").strip().lower()
    if normalized == "agent":
        return ChatMessageRole.ASSISTANT
    if normalized == "system":
        return ChatMessageRole.SYSTEM
    return ChatMessageRole.USER


def _detect_sender(sender: str) -> ChatMessageSender:
    normalized = (sender or "").strip().lower()
    if normalized == "agent":
        return ChatMessageSender.AGENT
    if normalized == "system":
        return ChatMessageSender.SYSTEM
    return ChatMessageSender.USER


async def _session_exists(session_id: str) -> bool:
    row = await chat_repository.get_session_summary(session_id)
    return row is not None


async def _import_single_session(
    *,
    payload: dict[str, Any],
    dry_run: bool,
    skip_existing: bool,
) -> tuple[bool, int]:
    session_id = str(payload.get("session_id", "")).strip()
    if not session_id:
        return False, 0

    if not dry_run and await _session_exists(session_id):
        if skip_existing:
            return False, 0
        raise ValueError(f"Session already exists in PostgreSQL: {session_id}")

    created_at = _parse_datetime(payload.get("created_at")) or datetime.now(timezone.utc)
    updated_at = _parse_datetime(payload.get("updated_at")) or created_at
    raw_messages = payload.get("messages") or []
    if not isinstance(raw_messages, list):
        raise ValueError(f"Session {session_id} contains invalid message payload")

    sorted_messages = sorted(
        [message for message in raw_messages if isinstance(message, dict)],
        key=lambda item: item.get("timestamp") or "",
    )

    if dry_run:
        return True, len(sorted_messages)

    await chat_repository.create_session(
        title="Migrated Session",
        selected_agent_id=None,
        metadata={
            "legacy_source": "file_store",
            "legacy_created_at": payload.get("created_at"),
            "legacy_updated_at": payload.get("updated_at"),
        },
        session_id=session_id,
    )

    imported_messages = 0
    for message in sorted_messages:
        message_id = str(message.get("id", "")).strip() or None
        content = str(message.get("content", "")).strip()
        sender = str(message.get("sender", "")).strip().lower() or "user"
        timestamp = _parse_datetime(message.get("timestamp")) or created_at

        if not content:
            continue

        created = await chat_repository.create_message(
            session_id=session_id,
            message_id=message_id,
            role=_detect_role(sender),
            sender=_detect_sender(sender),
            content=content,
            status=ChatMessageStatus.COMPLETED,
            agent_id=(str(message.get("agent_id", "")).strip() or None),
            agent_name=(str(message.get("agent_name", "")).strip() or None),
            metadata={
                "legacy_timestamp": message.get("timestamp"),
                "legacy_sender": sender,
            },
        )
        await postgres_client.execute(
            """
            UPDATE chat_messages
            SET created_at = $2, updated_at = $2
            WHERE id = $1
            """,
            str(created.id),
            timestamp,
        )
        imported_messages += 1

    await postgres_client.execute(
        """
        UPDATE chat_sessions
        SET created_at = $2, updated_at = $3, last_message_at = $3
        WHERE id = $1
        """,
        session_id,
        created_at,
        updated_at,
    )

    return True, imported_messages


async def run_migration(*, data_dir: Path, dry_run: bool, skip_existing: bool) -> None:
    files = sorted(data_dir.glob("*.json"))
    if not files:
        print(f"No legacy session files found in {data_dir}")
        return

    if not dry_run:
        await postgres_client.connect()

    imported_sessions = 0
    imported_messages = 0
    skipped_sessions = 0
    failed_sessions = 0

    try:
        for path in files:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                imported, count = await _import_single_session(
                    payload=payload,
                    dry_run=dry_run,
                    skip_existing=skip_existing,
                )
                if imported:
                    imported_sessions += 1
                    imported_messages += count
                    print(f"[OK] {path.name}: imported {count} messages")
                else:
                    skipped_sessions += 1
                    print(f"[SKIP] {path.name}: already imported")
            except Exception as exc:
                failed_sessions += 1
                print(f"[FAIL] {path.name}: {exc}")
    finally:
        if not dry_run:
            await postgres_client.disconnect()

    print(
        "\nMigration summary:"
        f"\n  Sessions imported: {imported_sessions}"
        f"\n  Sessions skipped:  {skipped_sessions}"
        f"\n  Sessions failed:   {failed_sessions}"
        f"\n  Messages imported: {imported_messages}"
        f"\n  Dry run:           {dry_run}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy JSON chat sessions to PostgreSQL tables.",
    )
    parser.add_argument(
        "--data-dir",
        default="backend/data/chat_sessions",
        help="Directory containing legacy JSON session files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and count import records without writing to PostgreSQL.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip sessions that already exist in PostgreSQL.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    asyncio.run(
        run_migration(
            data_dir=Path(arguments.data_dir),
            dry_run=arguments.dry_run,
            skip_existing=arguments.skip_existing,
        )
    )
