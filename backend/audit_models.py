from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Index,
)

from backend.database import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    __table_args__ = (
        # Faster filtering by user
        Index(
            "ix_audit_logs_user_id",
            "user_id"
        ),

        # Faster filtering by entity type
        Index(
            "ix_audit_logs_entity",
            "entity"
        ),

        # Faster lookup of actions for a specific entity
        Index(
            "ix_audit_logs_entity_id",
            "entity_id"
        ),

        # Faster chronological audit-log queries
        Index(
            "ix_audit_logs_created_at",
            "created_at"
        ),

        # Useful for entity history queries
        Index(
            "ix_audit_logs_entity_entity_id",
            "entity",
            "entity_id"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        nullable=True
    )

    username = Column(
        String(100),
        nullable=True
    )

    action = Column(
        String(100),
        nullable=False
    )

    entity = Column(
        String(100),
        nullable=False
    )

    entity_id = Column(
        Integer,
        nullable=True
    )

    details = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )