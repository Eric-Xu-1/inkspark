"""SSE stream for conversation events."""

import asyncio
import json
import os
import sys

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from redis_store import RedisStore

router = APIRouter(prefix="/api/conversations", tags=["stream"])
store = RedisStore()


@router.get("/{conv_id}/stream")
async def stream_events(conv_id: str):
    if not store.get_conversation(conv_id):
        raise HTTPException(404, "Conversation not found")

    async def event_generator():
        r = aioredis.Redis(host="localhost", port=6379, decode_responses=True)
        pubsub = r.pubsub()
        channel = f"conversation:{conv_id}:events"
        await pubsub.subscribe(channel)

        # Send existing state first so reconnects restore UI after refresh
        conv = store.get_conversation(conv_id) or {}
        steps = store.get_steps(conv_id)
        yield {
            "event": "init",
            "data": json.dumps(
                {"steps": steps, "status": conv.get("status", "created")},
                ensure_ascii=False,
            ),
        }

        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield {"event": "message", "data": message["data"]}
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(channel)
            await r.close()

    return EventSourceResponse(event_generator())
