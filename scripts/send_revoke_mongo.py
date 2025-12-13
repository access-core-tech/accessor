import asyncio
import json
import uuid
import random
from aiokafka import AIOKafkaProducer

USERS = ["bob.johnson@mail.com"]


async def produce_one_message():
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',
    )

    try:
        await producer.start()

        message = {
            "request_id": str(uuid.uuid4()),
            "project_name": 'alpha',
            "resource_type": 'mongodb',
            "resource_name": 'mongo-main',
            "requester_uuid": "7dda7829-6323-4955-b446-f48f4161917f",
        }

        topic = 'revoke_access'
        await producer.send_and_wait(topic, value=message)

        print(f"Данные: {json.dumps(message, indent=2)}")

    except Exception as e:
        print(f"Ошибка при отправке: {e}")
        raise
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(produce_one_message())
