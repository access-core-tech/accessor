import asyncio
import json
import uuid

from aiokafka import AIOKafkaProducer

USERS = ['bob.johnson@mail.com']


async def produce_one_message():
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
    )

    try:
        await producer.start()
        print('Продюсер запущен')

        message = {
            'request_id': str(uuid.uuid4()),
            'project_name': 'alpha',
            'resource_type': 'postgresql',
            'resource_name': 'postgresql-main',
            'requester_uuid': '614be86f-778e-474b-a5dd-d961bdd4fb60',
        }

        topic = 'revoke_access'
        await producer.send_and_wait(topic, value=message)

        print(f'Данные: {json.dumps(message, indent=2)}')

    except Exception as e:
        print(f'Ошибка при отправке: {e}')
        raise
    finally:
        await producer.stop()


if __name__ == '__main__':
    asyncio.run(produce_one_message())
