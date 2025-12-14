import json
from uuid import UUID
from datetime import datetime, UTC

from aiokafka import AIOKafkaProducer

from server.config import settings
from server.database import get_db
from server.repositories.resources import ResourceRepo
from server.repositories.access_account import AccessAccountRepo
from server.repositories.revoke_requests import RevokeRequestRepo

from server.views.revoke_access.models import (
    RevokeRequestsListRequest,
    RevokeRequestsListResponse,
    RevokeRequestItemRequest,
    RevokeRequestItemResponse,
    RevokeAccessRequest,
    RevokeRequestResponse,
)


class RevokeRequestsView:
    async def get_revoke(self, request: RevokeRequestItemRequest) -> RevokeRequestItemResponse:
        async with get_db() as session:
            revoke_request_repo = RevokeRequestRepo(session)

            revoke_request = await revoke_request_repo.get_by_id(request.id)

            if not revoke_request:
                return RevokeRequestItemResponse(revoke_request=None)

            response = RevokeRequestResponse(
                id=revoke_request.id,
                access_account_id=revoke_request.access_account_id,
                requester_uuid=revoke_request.requester_uuid,
                reason=revoke_request.reason,
                status=revoke_request.status,
                completed_at=revoke_request.completed_at,
                error_message=revoke_request.error_message,
                created_at=revoke_request.created_at,
            )

            return RevokeRequestItemResponse(revoke_request=response)

    async def get_revokes(self, request: RevokeRequestsListRequest) -> RevokeRequestsListResponse:
        async with get_db() as session:
            revoke_request_repo = RevokeRequestRepo(session)

            if request.project_id:
                revoke_requests = await revoke_request_repo.list_by_project(request.project_id)
            else:
                revoke_requests = await revoke_request_repo.list_all()

            responses = []
            for req in revoke_requests:
                response = RevokeRequestResponse(
                    id=req.id,
                    access_account_id=req.access_account_id,
                    requester_uuid=req.requester_uuid,
                    reason=req.reason,
                    status=req.status,
                    completed_at=req.completed_at,
                    error_message=req.error_message,
                    created_at=req.created_at,
                )
                responses.append(response)

            return RevokeRequestsListResponse(revoke_requests=responses)

    async def revoke_access(self, request: RevokeAccessRequest) -> RevokeRequestItemResponse:
        async with get_db() as session:
            resource_repo = ResourceRepo(session)
            access_account_repo = AccessAccountRepo(session)
            revoke_request_repo = RevokeRequestRepo(session)

            access_account = await access_account_repo.get_by_id(request.access_account_id)
            if not access_account:
                raise ValueError(f"Access account with id {request.access_account_id} not found")

            if not access_account.is_active:
                raise ValueError(f"Access account is already inactive")

            resource = await resource_repo.get_by_id(access_account.resource_id)
            if not resource:
                raise ValueError(f"Resource with id {access_account.resource_id} not found")

            revoke_request = await revoke_request_repo.create(
                access_account_id=request.access_account_id,
                requester_uuid=request.requester_uuid,
                reason=request.reason,
            )

            await access_account_repo.deactivate(request.access_account_id)

            kafka_message = {
                'request_id': str(revoke_request.id),
                'project_name': str(resource.project_id),
                'resource_type': resource.resource_type,
                'resource_name': resource.name,
                'requester_uuid': str(request.requester_uuid),
                'access_account_id': str(request.access_account_id),
                'user_uuid': str(access_account.user_uuid),
            }

            kafka_producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
            )
            await kafka_producer.start()
            await kafka_producer.send('revoke_access', value=kafka_message)
            await kafka_producer.stop()

            completed_request = await revoke_request_repo.complete(revoke_request.id)

            response = RevokeRequestResponse(
                id=completed_request.id,
                access_account_id=completed_request.access_account_id,
                requester_uuid=completed_request.requester_uuid,
                reason=completed_request.reason,
                status=completed_request.status,
                completed_at=completed_request.completed_at,
                error_message=completed_request.error_message,
                created_at=completed_request.created_at,
            )

            return RevokeRequestItemResponse(revoke_request=response)


revoke_requests_view = RevokeRequestsView()
