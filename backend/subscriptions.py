import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone

HEARTBEAT_INTERVAL_SECONDS = 15

_subscribers: dict[str, set[asyncio.Queue[tuple[str, dict]]]] = defaultdict(set)


def subscribe(sscc: str) -> asyncio.Queue[tuple[str, dict]]:
    queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue(maxsize=64)
    _subscribers[sscc].add(queue)
    return queue


def unsubscribe(sscc: str, queue: asyncio.Queue[tuple[str, dict]]) -> None:
    _subscribers[sscc].discard(queue)
    if not _subscribers[sscc]:
        del _subscribers[sscc]


async def publish(sscc: str, event_type: str, data: dict) -> None:
    message = (event_type, data)
    for queue in list(_subscribers.get(sscc, ())):
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass


def format_sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def format_heartbeat() -> str:
    return format_sse(
        "heartbeat",
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
        },
    )
