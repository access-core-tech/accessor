import uuid

from sqlalchemy import Column, String, UUID, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()


class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )

    access_requests = relationship("AccessRequest", back_populates="resource")
    access_accounts = relationship("AccessAccount", back_populates="resource")


class AccessRequest(Base):
    __tablename__ = "access_requests"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID, ForeignKey("resources.id"), nullable=False, index=True)

    requester_uuid = Column(UUID, nullable=False, index=True)
    request_name = Column(String(200), nullable=False)
    ttl_minutes = Column(Integer, nullable=True)

    status = Column(String(20), default='pending', nullable=False)  # pending, approved, denied
    reviewer_uuid = Column(UUID, nullable=True, index=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )

    resource = relationship("Resource", back_populates="access_requests")


class AccessAccount(Base):
    __tablename__ = "access_accounts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID, ForeignKey("resources.id"), nullable=False, index=True)

    user_uuid = Column(UUID, nullable=False, index=True)
    access_level = Column(String(20), nullable=False)  # read, write, admin
    granted_by = Column(UUID, nullable=False, index=True)
    granted_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))

    expires_at = Column(DateTime(timezone=True), nullable=True)
    access_request_id = Column(UUID, ForeignKey("access_requests.id"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )

    resource = relationship("Resource", back_populates="access_accounts")


class RevokeRequest(Base):
    __tablename__ = "revoke_requests"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    access_account_id = Column(UUID, nullable=False, index=True)

    requester_uuid = Column(UUID, nullable=False, index=True)
    reason = Column(Text, nullable=False)

    status = Column(String(20), default='pending', nullable=False)  # pending, completed, failed
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.now(datetime.UTC),
        onupdate=datetime.datetime.now(datetime.UTC),
    )


class EventOutbox(Base):
    __tablename__ = "event_outbox"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(datetime.UTC))
