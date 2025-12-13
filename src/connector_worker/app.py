from faststream import FastStream
from faststream.kafka import KafkaBroker

from connector_worker.config import settings
from connector_worker.event_handlers.create_access import create_access_handler
from connector_worker.event_handlers.revoke_access import revoke_access_handler

broker = KafkaBroker(settings.KAFKA_URL)

app = FastStream(broker)


# Обработка события создания доступа
broker.subscriber(settings.CREATE_ACCESS_TOPIC_NAME)(create_access_handler)
# Обработка события отзыва доступа
broker.subscriber(settings.REVOKE_ACCESS_TOPIC_NAME)(revoke_access_handler)
