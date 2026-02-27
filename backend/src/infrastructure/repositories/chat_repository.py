"""PostgreSQL-backed chat repository."""

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from src.core import get_logger
from src.domain.models import (
    ChatMessage,
    ChatMessageFeedback,
    ChatMessageRole,
    ChatMessageSender,
    ChatMessageStatus,
    ChatFeedbackType,
    ChatSession,
    ChatSessionStatus,
)
from src.infrastructure.database import postgres_client

logger = get_logger(__name__)


class ChatRepository:
    """Repository for persistent chat sessions, messages, and feedback."""

    @staticmethod
    def _default_title(content: str) -> str:
        title = " ".join(content.strip().split())
        if not title:
            return "New Chat"
        return title[:77] + "..." if len(title) > 80 else title

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _row_to_session(self, row: dict[str, Any]) -> ChatSession:
        return ChatSession(
            id=row["id"],
            title=row["title"],
            status=ChatSessionStatus(row["status"]),
            selected_agent_id=row.get("selected_agent_id"),
            message_count=int(row.get("message_count", 0) or 0),
            last_message_at=row.get("last_message_at"),
            metadata=row.get("metadata", {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_feedback(self, row: Optional[dict[str, Any]]) -> Optional[ChatMessageFeedback]:
        if not row or not row.get("feedback_id"):
            return None

        return ChatMessageFeedback(
            id=row["feedback_id"],
            session_id=row["session_id"],
            message_id=row["id"],
            agent_id=row.get("feedback_agent_id"),
            feedback_type=ChatFeedbackType(row["feedback_type"]),
            rating=row.get("rating"),
            text_feedback=row.get("text_feedback"),
            user_id=row.get("user_id"),
            metadata=row.get("feedback_metadata", {}),
            created_at=row["feedback_created_at"],
            updated_at=row["feedback_updated_at"],
        )

    def _row_to_message(self, row: dict[str, Any]) -> ChatMessage:
        sender = row.get("sender") or (
            ChatMessageSender.AGENT.value
            if row.get("role") == ChatMessageRole.ASSISTANT.value
            else ChatMessageSender.USER.value
        )

        return ChatMessage(
            id=row["id"],
            session_id=row["session_id"],
            sequence_number=int(row["sequence_number"]),
            role=ChatMessageRole(row["role"]),
            sender=ChatMessageSender(sender),
            content=row["content"],
            status=ChatMessageStatus(row["status"]),
            agent_id=row.get("agent_id"),
            agent_name=row.get("agent_name"),
            error_message=row.get("error_message"),
            metadata=row.get("metadata", {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_session(
        self,
        title: Optional[str] = None,
        selected_agent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> ChatSession:
        now = self._now()
        resolved_session_id = session_id or str(uuid4())
        resolved_title = title.strip() if title and title.strip() else "New Chat"

        query = """
            INSERT INTO chat_sessions (
                id,
                title,
                status,
                selected_agent_id,
                metadata,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $6)
            RETURNING *
        """

        row = await postgres_client.fetchrow(
            query,
            resolved_session_id,
            resolved_title,
            ChatSessionStatus.ACTIVE.value,
            selected_agent_id,
            metadata or {},
            now,
        )
        if not row:
            raise RuntimeError("Failed to create chat session")

        return self._row_to_session(row)

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        row = await postgres_client.fetchrow(
            "SELECT * FROM chat_sessions WHERE id = $1",
            session_id,
        )
        return self._row_to_session(row) if row else None

    async def get_session_summary(self, session_id: str) -> Optional[dict[str, Any]]:
        query = """
            SELECT
                s.*,
                lm.content AS last_message,
                lm.agent_name AS last_agent_name
            FROM chat_sessions s
            LEFT JOIN LATERAL (
                SELECT content, agent_name
                FROM chat_messages
                WHERE session_id = s.id
                ORDER BY sequence_number DESC
                LIMIT 1
            ) lm ON TRUE
            WHERE s.id = $1
        """
        return await postgres_client.fetchrow(query, session_id)

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        status_filter = None if include_archived else ChatSessionStatus.ACTIVE.value
        query = """
            SELECT
                s.*,
                lm.content AS last_message,
                lm.agent_name AS last_agent_name
            FROM chat_sessions s
            LEFT JOIN LATERAL (
                SELECT content, agent_name
                FROM chat_messages
                WHERE session_id = s.id
                ORDER BY sequence_number DESC
                LIMIT 1
            ) lm ON TRUE
            WHERE ($1::text IS NULL OR s.status = $1)
            ORDER BY COALESCE(s.last_message_at, s.updated_at, s.created_at) DESC
            LIMIT $2 OFFSET $3
        """
        rows = await postgres_client.fetch(query, status_filter, limit, offset)
        return rows

    async def update_session(
        self,
        session_id: str,
        *,
        title: Optional[str] = None,
        status: Optional[ChatSessionStatus] = None,
        selected_agent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[ChatSession]:
        current = await self.get_session(session_id)
        if not current:
            return None

        now = self._now()
        query = """
            UPDATE chat_sessions
            SET
                title = $2,
                status = $3,
                selected_agent_id = $4,
                metadata = $5,
                updated_at = $6
            WHERE id = $1
            RETURNING *
        """

        row = await postgres_client.fetchrow(
            query,
            session_id,
            title.strip() if title and title.strip() else current.title,
            (status or current.status).value,
            selected_agent_id if selected_agent_id is not None else current.selected_agent_id,
            metadata if metadata is not None else current.metadata,
            now,
        )
        return self._row_to_session(row) if row else None

    async def delete_session(self, session_id: str) -> bool:
        result = await postgres_client.execute(
            "DELETE FROM chat_sessions WHERE id = $1",
            session_id,
        )
        return "DELETE 1" in result

    async def create_message(
        self,
        *,
        session_id: str,
        role: ChatMessageRole,
        content: str,
        sender: Optional[ChatMessageSender] = None,
        status: ChatMessageStatus = ChatMessageStatus.COMPLETED,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ) -> ChatMessage:
        resolved_sender = sender or (
            ChatMessageSender.AGENT if role == ChatMessageRole.ASSISTANT else ChatMessageSender.USER
        )
        now = self._now()
        resolved_message_id = message_id or str(uuid4())

        async with postgres_client.acquire() as conn:
            async with conn.transaction():
                session_row = await conn.fetchrow(
                    "SELECT * FROM chat_sessions WHERE id = $1 FOR UPDATE",
                    session_id,
                )
                if not session_row:
                    raise ValueError(f"Chat session not found: {session_id}")

                next_sequence = int(session_row["message_count"] or 0) + 1
                next_title = session_row["title"]
                if (
                    role == ChatMessageRole.USER
                    and int(session_row["message_count"] or 0) == 0
                    and next_title == "New Chat"
                ):
                    next_title = self._default_title(content)

                await conn.execute(
                    """
                    UPDATE chat_sessions
                    SET
                        title = $2,
                        selected_agent_id = COALESCE($3, selected_agent_id),
                        message_count = $4,
                        last_message_at = $5,
                        updated_at = $5
                    WHERE id = $1
                    """,
                    session_id,
                    next_title,
                    agent_id,
                    next_sequence,
                    now,
                )

                row = await conn.fetchrow(
                    """
                    INSERT INTO chat_messages (
                        id,
                        session_id,
                        sequence_number,
                        role,
                        sender,
                        content,
                        status,
                        agent_id,
                        agent_name,
                        error_message,
                        metadata,
                        created_at,
                        updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $12
                    )
                    RETURNING *
                    """,
                    resolved_message_id,
                    session_id,
                    next_sequence,
                    role.value,
                    resolved_sender.value,
                    content,
                    status.value,
                    agent_id,
                    agent_name,
                    error_message,
                    metadata or {},
                    now,
                )

        if not row:
            raise RuntimeError("Failed to create chat message")
        return self._row_to_message(dict(row))

    async def list_messages(
        self,
        session_id: str,
        limit: int = 100,
        before_sequence: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                m.*,
                f.id AS feedback_id,
                f.agent_id AS feedback_agent_id,
                f.feedback_type,
                f.rating,
                f.text_feedback,
                f.user_id,
                f.metadata AS feedback_metadata,
                f.created_at AS feedback_created_at,
                f.updated_at AS feedback_updated_at
            FROM (
                SELECT *
                FROM chat_messages
                WHERE session_id = $1
                    AND ($2::bigint IS NULL OR sequence_number < $2)
                ORDER BY sequence_number DESC
                LIMIT $3
            ) m
            LEFT JOIN chat_message_feedback f ON f.message_id = m.id
            ORDER BY m.sequence_number ASC
        """
        return await postgres_client.fetch(query, session_id, before_sequence, limit)

    async def get_message(self, message_id: str) -> Optional[dict[str, Any]]:
        query = """
            SELECT
                m.*,
                f.id AS feedback_id,
                f.agent_id AS feedback_agent_id,
                f.feedback_type,
                f.rating,
                f.text_feedback,
                f.user_id,
                f.metadata AS feedback_metadata,
                f.created_at AS feedback_created_at,
                f.updated_at AS feedback_updated_at
            FROM chat_messages m
            LEFT JOIN chat_message_feedback f ON f.message_id = m.id
            WHERE m.id = $1
        """
        return await postgres_client.fetchrow(query, message_id)

    async def update_message(
        self,
        message_id: str,
        *,
        content: Optional[str] = None,
        status: Optional[ChatMessageStatus] = None,
        error_message: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[ChatMessage]:
        existing = await self.get_message(message_id)
        if not existing:
            return None

        query = """
            UPDATE chat_messages
            SET
                content = $2,
                status = $3,
                error_message = $4,
                metadata = $5,
                updated_at = $6
            WHERE id = $1
            RETURNING *
        """
        now = self._now()
        row = await postgres_client.fetchrow(
            query,
            message_id,
            existing["content"] if content is None else content,
            existing["status"] if status is None else status.value,
            existing.get("error_message") if error_message is None else error_message,
            existing.get("metadata", {}) if metadata is None else metadata,
            now,
        )
        return self._row_to_message(row) if row else None

    async def upsert_feedback(
        self,
        *,
        session_id: str,
        message_id: str,
        feedback_type: ChatFeedbackType,
        agent_id: Optional[str] = None,
        rating: Optional[float] = None,
        text_feedback: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ChatMessageFeedback:
        now = self._now()
        feedback_id = str(uuid4())
        query = """
            INSERT INTO chat_message_feedback (
                id,
                session_id,
                message_id,
                agent_id,
                feedback_type,
                rating,
                text_feedback,
                user_id,
                metadata,
                created_at,
                updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10
            )
            ON CONFLICT (message_id)
            DO UPDATE SET
                agent_id = EXCLUDED.agent_id,
                feedback_type = EXCLUDED.feedback_type,
                rating = EXCLUDED.rating,
                text_feedback = EXCLUDED.text_feedback,
                user_id = EXCLUDED.user_id,
                metadata = EXCLUDED.metadata,
                updated_at = EXCLUDED.updated_at
            RETURNING
                id AS feedback_id,
                message_id,
                session_id,
                agent_id AS feedback_agent_id,
                feedback_type,
                rating,
                text_feedback,
                user_id,
                metadata AS feedback_metadata,
                created_at AS feedback_created_at,
                updated_at AS feedback_updated_at
        """
        row = await postgres_client.fetchrow(
            query,
            feedback_id,
            session_id,
            message_id,
            agent_id,
            feedback_type.value,
            rating,
            text_feedback,
            user_id,
            metadata or {},
            now,
        )
        if not row:
            raise RuntimeError("Failed to store chat feedback")

        return ChatMessageFeedback(
            id=row["feedback_id"],
            session_id=row["session_id"],
            message_id=row["message_id"],
            agent_id=row.get("feedback_agent_id"),
            feedback_type=ChatFeedbackType(row["feedback_type"]),
            rating=row.get("rating"),
            text_feedback=row.get("text_feedback"),
            user_id=row.get("user_id"),
            metadata=row.get("feedback_metadata", {}),
            created_at=row["feedback_created_at"],
            updated_at=row["feedback_updated_at"],
        )

    async def save_message(
        self,
        session_id: str,
        message_id: str,
        sender: str,
        content: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> bool:
        try:
            session = await self.get_session(session_id)
            if not session:
                await self.create_session(session_id=session_id, selected_agent_id=agent_id)

            role = ChatMessageRole.ASSISTANT if sender == ChatMessageSender.AGENT.value else ChatMessageRole.USER
            resolved_sender = ChatMessageSender(sender)
            await self.create_message(
                session_id=session_id,
                message_id=message_id,
                role=role,
                sender=resolved_sender,
                content=content,
                agent_id=agent_id,
                agent_name=agent_name,
            )
            return True
        except Exception as exc:
            logger.error("Failed to save chat message: %s", exc, exc_info=True)
            return False

    async def get_session_history(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self.list_messages(session_id=session_id, limit=limit)
        return [
            {
                "id": row["id"],
                "sender": row["sender"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["created_at"].isoformat(),
                "agent_id": row.get("agent_id"),
                "agent_name": row.get("agent_name"),
                "status": row["status"],
                "sequence_number": row["sequence_number"],
                "feedback_type": row.get("feedback_type"),
            }
            for row in rows
        ]

    async def clear_session(self, session_id: str) -> bool:
        return await self.delete_session(session_id)


chat_repository = ChatRepository()
