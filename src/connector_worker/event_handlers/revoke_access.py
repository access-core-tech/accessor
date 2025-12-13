from connector_worker.models.access_requests import DeprovisionRequest
from connector_worker.providers.select_provider import select_provider
from connector_worker.config import logger


async def revoke_access_handler(deprovision_request: DeprovisionRequest):
    logger.info('Receive revocke handler')
    logger.debug('kwargs', **deprovision_request.model_dump())

    provider_class = select_provider(deprovision_request.resource_type)

    await provider_class.revoke_access(deprovision_request)
