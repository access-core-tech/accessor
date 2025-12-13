from connector_worker.models.access_requests import AccessRequest
from connector_worker.providers.select_provider import select_provider
from connector_worker.config import logger


async def create_access_handler(access_request: AccessRequest):
    logger.info('Receive access handler')
    logger.debug('kwargs', **access_request.model_dump())

    provider_class = select_provider(access_request.resource_type)

    await provider_class.create_user(access_request)
