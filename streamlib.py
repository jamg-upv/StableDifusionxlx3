from __future__ import annotations

from typing import AsyncIterable

import asyncio

from collections import defaultdict

from fastapi_poe import PoeBot
from fastapi_poe.client import MetaMessage, stream_request
from fastapi_poe.types import QueryRequest, SettingsResponse
from sse_starlette.sse import ServerSentEvent


async def advance_stream(
    label: str, gen: AsyncIterator[BotMessage]
) -> tuple[str, BotMessage | Exception | None]:
    try:
        return label, await gen.__anext__()
    except StopAsyncIteration:
        return label, None
    except Exception as e:
        return label, e


async def combine_streams(
    streams: Sequence[tuple[str, AsyncIterator[BotMessage]]]
) -> AsyncIterator[tuple[str, BotMessage | Exception]]:
    active_streams = dict(streams)
    while active_streams:
        for coro in asyncio.as_completed(
            [advance_stream(label, gen) for label, gen in active_streams.items()]
        ):
            label, msg = await coro
            if msg is None:
                del active_streams[label]
            else:
                if isinstance(msg, Exception):
                    del active_streams[label]
                yield label, msg

async def merge_stream_output(streams):
    label_to_responses: dict[int, list[str]] = defaultdict(list)
    async for label, msg in combine_streams(streams):
        if isinstance(msg, MetaMessage):
            continue
        elif isinstance(msg, Exception):
            label_to_responses[label] = [f"{label} ran into an error:" + ('%r'%msg)]
        elif msg.is_suggested_reply:
            yield PoeBot.suggested_reply_event(msg.text)
            continue
        elif msg.is_replace_response:
            label_to_responses[label] = [msg.text]
        else:
            label_to_responses[label].append(msg.text)
        text = "\n\n".join(
            f"\n{''.join(label_to_responses[item[0]])}"
            for item in streams
        )
        yield PoeBot.replace_response_event(text)
