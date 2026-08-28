"""
Example consumer, standing in for whatever downstream service would react
to these events in a real deployment — a notification service sending a
welcome email on `user.registered`, an analytics pipeline, a retention
workflow on `subscription.canceled`. Binds to every routing key ("#") on the
topic exchange and just logs; split into targeted consumers per concern
once there's more than one real subscriber.
"""

import asyncio
import json
import logging

import aio_pika

from app.config import settings

logger = logging.getLogger(__name__)


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body)
        logger.info("[%s] %s", message.routing_key, payload)
        # if message.routing_key == "user.registered": send_welcome_email(payload)
        # if message.routing_key == "subscription.canceled": notify_retention_team(payload)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            settings.outbox_exchange, aio_pika.ExchangeType.TOPIC, durable=True
        )
        queue = await channel.declare_queue("vitalsync.notifications", durable=True)
        await queue.bind(exchange, routing_key="#")

        logger.info("Consumer listening on vitalsync.notifications")
        await queue.consume(handle_message)
        await asyncio.Future()  # run until the process is killed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
