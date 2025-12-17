# services/secret_service/client.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import grpc
from grpc import aio
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from services.secret_service.models import (
    GetSecretResponse,
    InitStorageResponse,
    PutSecretRequest,
)
from services.secret_service.protobuf import secret_service_pb2, secret_service_pb2_grpc

logger = logging.getLogger(__name__)


class SecretStoreClient:
    """Асинхронный клиент для SecretStore gRPC сервиса"""

    def __init__(self, host: str = 'localhost', port: int = 6668, timeout: int = 30):
        """
        Args:
            host: Хост сервера gRPC
            port: Порт сервера
            timeout: Таймаут по умолчанию в секундах
        """
        self.server_address = f'{host}:{port}'
        self.timeout = timeout
        self._channel: Optional[aio.Channel] = None
        self._stub: Optional[secret_service_pb2_grpc.SecretStoreStub] = None

    async def connect(self):
        """Установка соединения с сервером"""
        try:
            self._channel = aio.insecure_channel(self.server_address)
            self._stub = secret_service_pb2_grpc.SecretStoreStub(self._channel)
            logger.info(f'Connection established to {self.server_address}')
        except Exception as e:
            logger.error(f'Failed to connect to {self.server_address}: {e}')
            raise

    async def disconnect(self):
        """Закрытие соединения"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info('Connection closed')

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def init_storage(self, shares: int, threshold: int, timeout: Optional[int] = None) -> InitStorageResponse:
        """
        Инициализация хранилища секретов

        Args:
            shares: Количество частей ключа
            threshold: Пороговое значение для восстановления
            timeout: Таймаут операции в секундах

        Returns:
            InitStorageResponse с частями ключа

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC
            ValueError: При невалидных аргументах
        """
        if shares <= 0 or threshold <= 0:
            raise ValueError('shares and threshold must be positive integers')
        if threshold > shares:
            raise ValueError('threshold cannot be greater than shares')

        request = secret_service_pb2.InitStorageRequest(shares=shares, threshold=threshold)

        logger.info(f'Init storage request: shares={shares}, threshold={threshold}')

        try:
            response = await self._stub.InitStorage(request, timeout=timeout or self.timeout)

            result = InitStorageResponse(shares=list(response.shares))
            logger.info(f'Storage initialized successfully, shares count: {len(result.shares)}')

            return result

        except grpc.aio.AioRpcError as e:
            logger.error(f'Init storage failed: {e.code().name}: {e.details()}')
            raise

    async def unseal(self, shares: List[str], timeout: Optional[int] = None):
        """
        Распечатывание хранилища

        Args:
            shares: Список частей ключа
            timeout: Таймаут операции в секундах

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC
            ValueError: При невалидных аргументах
        """
        if not shares:
            raise ValueError('shares list cannot be empty')

        request = secret_service_pb2.UnsealRequest(shares=shares)

        logger.info(f'Unseal request: shares count={len(shares)}')

        try:
            await self._stub.Unseal(request, timeout=timeout or self.timeout)
            logger.info('Storage unsealed successfully')

        except grpc.aio.AioRpcError as e:
            logger.error(f'Unseal failed: {e.code().name}: {e.details()}')
            raise

    async def seal(self, timeout: Optional[int] = None):
        """
        Запечатывание хранилища

        Args:
            timeout: Таймаут операции в секундах

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC
        """
        request = secret_service_pb2.SealRequest()

        logger.info('Seal request')

        try:
            await self._stub.Seal(request, timeout=timeout or self.timeout)
            logger.info('Storage sealed successfully')

        except grpc.aio.AioRpcError as e:
            logger.error(f'Seal failed: {e.code().name}: {e.details()}')
            raise

    async def is_seal(self, timeout: Optional[int] = None) -> bool:
        """
        Проверяет, запечатано ли хранилище

        Returns:
            True если хранилище запечатано, False в противном случае
        """
        try:
            request = google_dot_protobuf_dot_empty__pb2.Empty()
            response = await self._stub.IsSeal(request, timeout=timeout or self.timeout)

            # Согласно протоколу, поле называется is_seal (в единственном числе)
            return response.is_seal

        except grpc.aio.AioRpcError as e:
            logger.error(f"Failed to check seal status: {e.code().name}: {e.details()}")
            # Если сервис недоступен, считаем что запечатано
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                return True
            raise
        except Exception as e:
            logger.error(f"Failed to check seal status: {str(e)}")
            raise

    async def is_init(self, timeout: Optional[int] = None) -> bool:
        """
        Проверяет, инициализировано ли хранилище

        Returns:
            True если хранилище инициализировано, False в противном случае
        """
        try:
            request = google_dot_protobuf_dot_empty__pb2.Empty()
            response = await self._stub.IsInit(request, timeout=timeout or self.timeout)

            # Согласно протоколу, поле называется is_init
            return response.is_init

        except grpc.aio.AioRpcError as e:
            logger.error(f"Failed to check init status: {e.code().name}: {e.details()}")
            # Если сервис недоступен, считаем что не инициализировано
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                return False
            raise
        except Exception as e:
            logger.error(f"Failed to check init status: {str(e)}")
            raise

    async def put_secret(
        self,
        path: List[str],
        value: Any,
        expires_at: Optional[datetime] = None,
        if_version: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ):
        """
        Добавление или обновление секрета

        Args:
            path: Путь к секрету
            value: Значение секрета (будет сериализовано в JSON)
            expires_at: Время истечения срока действия
            if_version: Версия для оптимистичной блокировки
            metadata: Метаданные секрета
            timeout: Таймаут операции в секундах

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC
            ValueError: При невалидных аргументах
        """
        if not path:
            raise ValueError('path cannot be empty')

        # Создаем модель запроса
        request_model = PutSecretRequest(
            path=path, json_value=value, expires_at=expires_at, if_version=if_version, metadata=metadata or {}
        )

        # Конвертируем в protobuf формат
        proto_data = request_model.to_proto_dict()
        request = secret_service_pb2.PutSecretRequest(**proto_data)

        logger.info(f'Put secret request: path={path}, has_metadata={bool(metadata)}')

        try:
            await self._stub.PutSecret(request, timeout=timeout or self.timeout)
            logger.info(f'Secret saved successfully: path={path}')

        except grpc.aio.AioRpcError as e:
            logger.error(f'Put secret failed for path={path}: {e.code().name}: {e.details()}')
            raise

    async def get_secret(self, path: List[str], timeout: Optional[int] = None) -> Optional[GetSecretResponse]:
        """
        Получение секрета

        Args:
            path: Путь к секрету
            timeout: Таймаут операции в секундах

        Returns:
            GetSecretResponse или None если секрет не найден

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC (кроме NOT_FOUND)
            ValueError: При невалидных аргументах
        """
        if not path:
            raise ValueError('path cannot be empty')

        request = secret_service_pb2.GetSecretRequest(path=path)

        logger.info(f'Get secret request: path={path}')

        try:
            response = await self._stub.GetSecret(request, timeout=timeout or self.timeout)
            result = GetSecretResponse.from_proto(response)

            logger.info(f'Secret retrieved successfully: path={path}, version={result.version}')

            return result

        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                logger.warning(f'Secret not found: path={path}')
                return None
            else:
                logger.error(f'Get secret failed for path={path}: {e.code().name}: {e.details()}')
                raise

    async def delete_secret(self, path: List[str], if_version: Optional[int] = None, timeout: Optional[int] = None):
        """
        Удаление секрета

        Args:
            path: Путь к секрету
            if_version: Версия для условного удаления
            timeout: Таймаут операции в секундах

        Raises:
            grpc.aio.AioRpcError: При ошибке gRPC (кроме NOT_FOUND)
            ValueError: При невалидных аргументах
        """
        if not path:
            raise ValueError('path cannot be empty')

        request = secret_service_pb2.DeleteSecretRequest(
            path=path, if_version=if_version if if_version is not None else 0
        )

        logger.info(f'Delete secret request: path={path}, if_version={if_version}')

        try:
            await self._stub.DeleteSecret(request, timeout=timeout or self.timeout)
            logger.info(f'Secret deleted successfully: path={path}')

        except grpc.aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                logger.warning(f'Secret not found for deletion: path={path}')
            else:
                logger.error(f'Delete secret failed for path={path}: {e.code().name}: {e.details()}')
                raise

    async def health_check(self, timeout: int = 5) -> bool:
        """
        Проверка доступности сервера

        Args:
            timeout: Таймаут проверки в секундах

        Returns:
            True если сервер доступен, False в противном случае
        """
        try:
            # Пробуем вызвать простой метод
            await self._stub.Seal(secret_service_pb2.SealRequest(), timeout=timeout)
            return True
        except grpc.aio.AioRpcError as e:
            # Если ошибка не связана с недоступностью сервера, считаем что он жив
            if e.code() not in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                return True
            return False
        except Exception:
            return False
