import json
from datetime import datetime, UTC, timedelta

from aiokafka import AIOKafkaProducer

from server.config import settings
from server.database import get_db
from server.repositories.resources import ResourceRepo
from server.repositories.access_account import AccessAccountRepo
from server.repositories.access_request import AccessRequestRepo

from server.views.access_requests.models import (
    AccessRequestsListRequest,
    AccessRequestsListResponse,
    AccessRequestItemRequest,
    AccessRequestItemSingleResponse,
    AccessRequestCreateRequest,
    AccessRequestStatusUpdateRequest,
    AccessRequestStatusUpdateResponse,
    AccessRequestItemResponse,
)


class AccessRequestView:
    async def get_access_request(self, request: AccessRequestItemRequest) -> AccessRequestItemSingleResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_request_repo = AccessRequestRepo(session)

            access_request = await access_request_repo.get_by_id(request.id)

            if not access_request:
                return AccessRequestItemSingleResponse(access_request=None)

            resource = await resource_repo.get_by_id(access_request.resource_id)

            response = AccessRequestItemResponse(
                id=access_request.id,
                resource_id=access_request.resource_id,
                resource_type=resource.resource_type if resource else "unknown",
                resource_name=resource.name if resource else "unknown",
                requester_uuid=access_request.requester_uuid,
                request_name=access_request.request_name,
                status=access_request.status,
                ttl_minutes=access_request.ttl_minutes,
                created_at=access_request.created_at,
            )

            return AccessRequestItemSingleResponse(access_request=response)

    async def get_accesses_request(self, request: AccessRequestsListRequest) -> AccessRequestsListResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_request_repo = AccessRequestRepo(session)

            access_requests = await access_request_repo.list_by_project(request.project_id)

            responses = []
            for req in access_requests:
                resource = await resource_repo.get_by_id(req.resource_id)

                response = AccessRequestItemResponse(
                    id=req.id,
                    resource_id=req.resource_id,
                    resource_type=resource.resource_type if resource else "unknown",
                    resource_name=resource.name if resource else "unknown",
                    requester_uuid=req.requester_uuid,
                    request_name=req.request_name,
                    status=req.status,
                    ttl_minutes=req.ttl_minutes,
                    created_at=req.created_at,
                )
                responses.append(response)

            return AccessRequestsListResponse(access_requests=responses)

    async def create_access_request(self, request: AccessRequestCreateRequest) -> AccessRequestItemSingleResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_request_repo = AccessRequestRepo(session)
            access_account_repo = AccessAccountRepo(session)

            resource = await resource_repo.get_by_id(request.resource_id)
            if not resource:
                raise ValueError(f"Resource with id {request.resource_id} not found")

            existing_access = await access_account_repo.get_by_resource_and_user(
                request.resource_id, request.requester_uuid
            )
            if existing_access and existing_access.is_active:
                raise ValueError(f"User already has active access to this resource")

            access_request = await access_request_repo.create(
                resource_id=request.resource_id,
                requester_uuid=request.requester_uuid,
                request_name=request.request_name,
                ttl_minutes=request.ttl_minutes,
            )

            response = AccessRequestItemResponse(
                id=access_request.id,
                resource_id=access_request.resource_id,
                resource_type=resource.resource_type,
                resource_name=resource.name,
                requester_uuid=access_request.requester_uuid,
                request_name=access_request.request_name,
                status=access_request.status,
                ttl_minutes=access_request.ttl_minutes,
                created_at=access_request.created_at,
            )

            return AccessRequestItemSingleResponse(access_request=response)

    async def approve_access(self, request: AccessRequestStatusUpdateRequest) -> AccessRequestStatusUpdateResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_request_repo = AccessRequestRepo(session)
            access_account_repo = AccessAccountRepo(session)

            access_request = await access_request_repo.get_by_id(request.id)
            if not access_request:
                raise ValueError(f"Access request with id {request.id} not found")

            if access_request.status != 'pending':
                raise ValueError(f"Access request is not pending (status: {access_request.status})")

            resource = await resource_repo.get_by_id(access_request.resource_id)
            if not resource:
                raise ValueError(f"Resource with id {access_request.resource_id} not found")

            updated_request = await access_request_repo.approve(
                request_id=request.id,
                reviewer_uuid=request.reviewer_uuid,
                comment=request.comment,
            )

            expires_at = None
            if access_request.ttl_minutes:
                expires_at = datetime.now(UTC) + timedelta(minutes=access_request.ttl_minutes)

            # TODO: Надо наверно интграцию бахнуть что запрашивать где то почту
            requester_login_email = f"user_{access_request.requester_uuid}@example.com"

            kafka_message = {
                'request_id': str(access_request.id),
                'project_name': str(resource.project_id),
                'resource_type': resource.resource_type,
                'resource_name': resource.name,
                'accesses': ['read'],
                'requester_uuid': str(access_request.requester_uuid),
                'requester_login_email': requester_login_email,
                'ttl_minutes': access_request.ttl_minutes,
            }

            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
            )
            await kafka_producer.start()
            await kafka_producer.send('create_access', value=kafka_message)
            await kafka_producer.stop()

            await access_account_repo.create(
                resource_id=access_request.resource_id,
                user_uuid=access_request.requester_uuid,
                access_level="read",
                granted_by=request.reviewer_uuid,
                access_request_id=request.id,
                expires_at=expires_at,
            )

            response = AccessRequestItemResponse(
                id=updated_request.id,
                resource_id=updated_request.resource_id,
                resource_type=resource.resource_type,
                resource_name=resource.name,
                requester_uuid=updated_request.requester_uuid,
                request_name=updated_request.request_name,
                status=updated_request.status,
                ttl_minutes=updated_request.ttl_minutes,
                created_at=updated_request.created_at,
            )

            return AccessRequestStatusUpdateResponse(access_request=response)

    async def deny_access(self, request: AccessRequestStatusUpdateRequest) -> AccessRequestStatusUpdateResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_request_repo = AccessRequestRepo(session)

            access_request = await access_request_repo.get_by_id(request.id)
            if not access_request:
                raise ValueError(f"Access request with id {request.id} not found")

            if access_request.status != 'pending':
                raise ValueError(f"Access request is not pending (status: {access_request.status})")

            resource = await resource_repo.get_by_id(access_request.resource_id)
            if not resource:
                raise ValueError(f"Resource with id {access_request.resource_id} not found")

            updated_request = await access_request_repo.deny(
                request_id=request.id, reviewer_uuid=request.reviewer_uuid, comment=request.comment
            )

            response = AccessRequestItemResponse(
                id=updated_request.id,
                resource_id=updated_request.resource_id,
                resource_type=resource.resource_type,
                resource_name=resource.name,
                requester_uuid=updated_request.requester_uuid,
                request_name=updated_request.request_name,
                status=updated_request.status,
                ttl_minutes=updated_request.ttl_minutes,
                created_at=updated_request.created_at,
            )

            return AccessRequestStatusUpdateResponse(access_request=response)


access_request_view = AccessRequestView()
