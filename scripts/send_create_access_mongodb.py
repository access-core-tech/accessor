import asyncio
import json
import random
import uuid

from aiokafka import AIOKafkaProducer

USERS = ['john.doe@mail.com', 'jane.smith@mail.com', 'bob.johnson@mail.com']


async def produce_mongodb_access_message():
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
    )

    try:
        await producer.start()

        message = {
            'request_id': str(uuid.uuid4()),
            'project_name': 'alpha',
            'resource_type': 'mongodb',  # Изменили на mongodb
            'resource_name': 'mongo-main',  # MongoDB ресурс
            'accesses': ['read'],
            'requester_uuid': str(uuid.uuid4()),
            'requester_login_email': random.choice(USERS),
            'ttl_minutes': random.randint(30, 1440),
        }

        topic = 'create_access'
        await producer.send_and_wait(topic, value=message)

        print(f'Данные: {json.dumps(message, indent=2)}')

    except Exception as e:
        print(f'Ошибка при отправке: {e}')
        raise
    finally:
        await producer.stop()


asyncio.run(produce_mongodb_access_message())
