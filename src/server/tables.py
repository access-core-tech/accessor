from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    Enum as SQLEnum,
    Interval,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
import uuid

Base = declarative_base()


# ==================== ENUMS ====================


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELED = "canceled"
    EXPIRED = "expired"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    DEPROVISIONING = "deprovisioning"
    DISABLED = "disabled"
    EXPIRED = "expired"
    ERROR = "error"


class AccessMode(str, enum.Enum):
    READ = "read"
    WRITE = "write"


# ==================== MODELS ====================


class Project(Base):
    """Проекты внутри организаций"""

    __tablename__ = 'project'
    __table_args__ = ({'schema': 'provisioning_service'},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="project")
    access_requests = relationship("AccessRequest", back_populates="project")
    provisioned_accounts = relationship("ProvisionedAccount", back_populates="project")


class ProjectMember(Base):
    """Участники проектов"""

    __tablename__ = 'project_member'
    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_member_project_user'),
        Index('idx_project_member_project_id', 'project_id'),
        Index('idx_project_member_user_id', 'user_id'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey('provisioning_service.project.id', ondelete='CASCADE'), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), nullable=False)
    role_id = Column(UUID(as_uuid=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")


class Resource(Base):
    """Ресурсы (серверы, БД, сервисы)"""

    __tablename__ = 'resource'
    __table_args__ = (
        UniqueConstraint('kind', 'external_ref', name='uq_resource_kind_ref'),
        Index('idx_resource_project_id', 'project_id'),
        Index('idx_resource_kind', 'kind'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('provisioning_service.project.id', ondelete='SET NULL'))
    kind = Column(String, nullable=False)  # e.g., "postgres", "redis", "s3"
    name = Column(String, nullable=False)
    external_ref = Column(String)  # External system reference
    resource_metadata = Column(JSON, default=dict, nullable=False, name='metadata')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="resources")
    access_requests = relationship("AccessRequest", back_populates="resource")
    provisioned_accounts = relationship("ProvisionedAccount", back_populates="resource")


class AccessRequest(Base):
    """Запросы на доступ к ресурсам"""

    __tablename__ = 'access_request'
    __table_args__ = (
        Index('idx_access_request_project_id', 'project_id'),
        Index('idx_access_request_resource_id', 'resource_id'),
        Index('idx_access_request_requester_user_id', 'requester_user_id'),
        Index('idx_access_request_approver_user_id', 'approver_user_id'),
        Index('idx_access_request_status', 'status'),
        Index('idx_access_request_expires_at', 'expires_at'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('provisioning_service.project.id', ondelete='SET NULL'))
    resource_id = Column(
        UUID(as_uuid=True), ForeignKey('provisioning_service.resource.id', ondelete='CASCADE'), nullable=False
    )
    requester_user_id = Column(UUID(as_uuid=True), nullable=False)
    access_mode = Column(SQLEnum(AccessMode, name='access_mode', schema='provisioning_service'), nullable=False)
    reason = Column(Text)
    status = Column(SQLEnum(RequestStatus, name='request_status', schema='provisioning_service'), nullable=False)
    requested_ttl = Column(Interval)  # Requested time-to-live
    approver_user_id = Column(UUID(as_uuid=True))
    decided_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="access_requests")
    resource = relationship("Resource", back_populates="access_requests")
    provisioning_job = relationship(
        "ProvisioningJob", back_populates="access_request", uselist=False, cascade="all, delete-orphan"
    )
    provisioned_accounts = relationship("ProvisionedAccount", back_populates="access_request")

    @property
    def is_approved(self):
        return self.status == RequestStatus.APPROVED

    @property
    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class ProvisioningJob(Base):
    """Задачи на создание аккаунтов"""

    __tablename__ = 'provisioning_job'
    __table_args__ = (
        UniqueConstraint('access_request_id', name='uq_provisioning_job_access_request'),
        Index('idx_provisioning_job_access_request_id', 'access_request_id'),
        Index('idx_provisioning_job_status', 'status'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_request_id = Column(
        UUID(as_uuid=True), ForeignKey('provisioning_service.access_request.id', ondelete='CASCADE'), nullable=False
    )
    status = Column(SQLEnum(JobStatus, name='job_status', schema='provisioning_service'), nullable=False)
    retries = Column(Integer, default=0, nullable=False)
    last_error = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    access_request = relationship("AccessRequest", back_populates="provisioning_job")

    @property
    def duration(self):
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class ProvisionedAccount(Base):
    """Созданные аккаунты"""

    __tablename__ = 'provisioned_account'
    __table_args__ = (
        UniqueConstraint('resource_id', 'external_account_id', name='uq_provisioned_account_resource_external'),
        Index('idx_provisioned_account_project_id', 'project_id'),
        Index('idx_provisioned_account_resource_id', 'resource_id'),
        Index('idx_provisioned_account_owner_user_id', 'owner_user_id'),
        Index('idx_provisioned_account_access_request_id', 'access_request_id'),
        Index('idx_provisioned_account_status', 'status'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey('provisioning_service.project.id', ondelete='SET NULL'))
    resource_id = Column(
        UUID(as_uuid=True), ForeignKey('provisioning_service.resource.id', ondelete='CASCADE'), nullable=False
    )
    external_account_id = Column(String, nullable=False)  # ID in external system
    owner_user_id = Column(UUID(as_uuid=True), nullable=False)
    access_request_id = Column(
        UUID(as_uuid=True), ForeignKey('provisioning_service.access_request.id', ondelete='CASCADE'), nullable=False
    )
    status = Column(SQLEnum(AccountStatus, name='account_status', schema='provisioning_service'), nullable=False)
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="provisioned_accounts")
    resource = relationship("Resource", back_populates="provisioned_accounts")
    access_request = relationship("AccessRequest", back_populates="provisioned_accounts")
    deprovision_job = relationship(
        "DeprovisionJob", back_populates="provisioned_account", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def is_active(self):
        return self.status == AccountStatus.ACTIVE

    @property
    def is_expired(self):
        if self.valid_until:
            return datetime.utcnow() > self.valid_until
        return False


class DeprovisionJob(Base):
    """Задачи на удаление аккаунтов"""

    __tablename__ = 'deprovision_job'
    __table_args__ = (
        UniqueConstraint('provisioned_account_id', name='uq_deprovision_job_account'),
        Index('idx_deprovision_job_status', 'status'),
        {'schema': 'provisioning_service'},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provisioned_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey('provisioning_service.provisioned_account.id', ondelete='CASCADE'),
        nullable=False,
    )
    status = Column(SQLEnum(JobStatus, name='job_status', schema='provisioning_service'), nullable=False)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    last_error = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    provisioned_account = relationship("ProvisionedAccount", back_populates="deprovision_job")
