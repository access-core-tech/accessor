import logging

from services.secret_service import SecretStoreClient
from server.views.store_admin.models import (
    SealResponse,
    UnsealRequest,
    UnsealResponse,
    IsSealResponse,
    InitStorageRequest,
    InitStorageResponse,
    Empty,
    ServiceStatusResponse,
)

logger = logging.getLogger(__name__)


class SecretStoreAdminView:
    def __init__(self):
        pass

    async def seal(
        self,
        _: Empty,
    ) -> SealResponse:
        secret_client = SecretStoreClient()

        try:
            async with secret_client as client:
                await client.seal()

                return SealResponse(success=True, message="Хранилище успешно запечатано")

        except Exception as e:
            logger.error(f"Failed to seal storage: {str(e)}")
            return SealResponse(success=False, message=f"Ошибка при запечатывании: {str(e)}")

    async def unseal(self, request: UnsealRequest) -> UnsealResponse:
        secret_client = SecretStoreClient()

        try:
            async with secret_client as client:
                is_sealed = await client.is_seal()

                if not is_sealed:
                    return UnsealResponse(success=False, message="Хранилище уже распечатано")

                await client.unseal(shares=request.shares)

                return UnsealResponse(success=True, message="Хранилище успешно распечатано")

        except Exception as e:
            logger.error(f"Failed to unseal storage: {str(e)}")
            return UnsealResponse(success=False, message=f"Ошибка при распечатывании: {str(e)}")

    async def is_seal(self, _: Empty) -> IsSealResponse:
        secret_client = SecretStoreClient()

        try:
            async with secret_client as client:
                is_sealed = await client.is_seal()

                return IsSealResponse(is_sealed=is_sealed)

        except Exception as e:
            logger.error(f"Failed to check seal status: {str(e)}")
            return IsSealResponse(is_sealed=True)

    async def init_storage(self, request: InitStorageRequest) -> InitStorageResponse:
        secret_client = SecretStoreClient()

        try:
            async with secret_client as client:
                is_initialized = await client.is_init()

                if is_initialized:
                    return InitStorageResponse(success=False, message="Хранилище уже инициализировано", shares=[])

                response = await client.init_storage(
                    shares=request.shares,
                    threshold=request.threshold,
                )

                return InitStorageResponse(
                    success=True,
                    message=f"Хранилище успешно инициализировано.",
                    shares=response.shares,
                )

        except ValueError as e:
            logger.error(f"Invalid initialization parameters: {str(e)}")
            return InitStorageResponse(
                success=False, message=f"Некорректные параметры инициализации: {str(e)}", shares=[]
            )
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            return InitStorageResponse(success=False, message=f"Ошибка при инициализации: {str(e)}", shares=[])

    async def get_service_status(self, _: Empty) -> ServiceStatusResponse:
        secret_client = SecretStoreClient()

        try:
            async with secret_client as client:
                is_initialized = await client.is_init()
                is_sealed = await client.is_seal()

                return ServiceStatusResponse(
                    is_healthy=is_initialized and is_sealed,
                    is_initialized=is_initialized,
                    is_sealed=is_sealed,
                )

        except Exception as e:
            logger.error(f"Failed to get service status: {str(e)}")
            return ServiceStatusResponse(
                is_healthy=False,
                is_initialized=False,
                is_sealed=None,
            )


secret_store_admin_view = SecretStoreAdminView()
