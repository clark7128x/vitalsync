"""
Outbox relay worker.

Runs as its own process (see the `outbox-relay` service in docker-compose),
separate from the API. Polls for outbox rows nobody has published yet,
publishes each to RabbitMQ, then marks it published — all after the fact,
never inside the request/response cycle. This is what makes the pattern
"transactional": the API only ever has to get one database commit right.

Polling is used instead of Postgres LISTEN/NOTIFY for simplicity and to keep
the demo boring to run. LISTEN/NOTIFY (or a CDC tool like Debezium) would
cut delivery latency from ~POLL_INTERVAL_SECONDS to near-zero, at the cost
of another moving part — a reasonable upgrade once this needs to be fast,
not just correct.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

import aio_pika
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.outbox import OutboxEvent

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 2
BATCH_SIZE = 50


async def relay_once(channel: aio_pika.abc.AbstractChannel) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.created_at)
            .limit(BATCH_SIZE)
        )
        events = result.scalars().all()
        if not events:
            return 0

        exchange = await channel.declare_exchange(
            settings.outbox_exchange, aio_pika.ExchangeType.TOPIC, durable=True
        )

        for event in events:
            message = aio_pika.Message(
                body=json.dumps(event.payload).encode(),
                content_type="application/json",
                message_id=event.id,
            )
            await exchange.publish(message, routing_key=event.event_type)

        now = datetime.now(timezone.utc)
        for event in events:
            event.published_at = now
        await db.commit()
        return len(events)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        logger.info("Outbox relay started, polling every %ss", POLL_INTERVAL_SECONDS)
        while True:
            published = await relay_once(channel)
            if published:
                logger.info("Relayed %d outbox event(s)", published)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
