"""

Sample bot that wraps StableDiffusionXL but generates 3 responses.

"""
from __future__ import annotations

from typing import AsyncIterable

import asyncio

from collections import defaultdict

from fastapi_poe import PoeBot
from fastapi_poe.client import MetaMessage, stream_request
from fastapi_poe.types import QueryRequest, SettingsResponse
from sse_starlette.sse import ServerSentEvent

import streamlib

class SDXLx3Bot(PoeBot):

    async def get_settings(self, setting: SettingsRequest) -> SettingsResponse:
        return SettingsResponse(
            server_bot_dependencies = {'StableDiffusionXL': 3}
        )

    async def get_response(self, query: QueryRequest) -> AsyncIterable[ServerSentEvent]:

        streams = [(i, stream_request(query, 'StableDiffusionXL', query.access_key)) for i in range(3)]

        async for event in streamlib.merge_stream_output(streams):
            yield event

