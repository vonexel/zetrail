import json
import hmac
import asyncio
from uuid import uuid4
from hashlib import sha256
from typing import Any, Annotated
from contextlib import asynccontextmanager
from pydantic import Field, ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware


Key = str


class IngestDocument(Document):
    library_id: int = Field(ge = 1)
    item_key: Key
    title: str = Field(default = "", max_length = 4000)
    collections: list[Key] = Field(default_factory = list, max_length = 1000)
    tags: list[str] = Field(default_factory = list, max_length = 1000)
    year: int | None = Field(default = None, ge = 1, le = 9999)

class IngestMetadata(Model):
    document: IngestDocument
    attachment_key: Key

class BodyLimit:
    def __init__(self, app: Any, limit: int):
        self.app, self.limit = app, limit

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        size = 0

        async def bounded_receive() -> Any:
            nonlocal size
            message = await receive()
            size += len(message.get("body", b""))
            if size > self.limit:
                raise HTTPException(413, "Upload exceeds the configured limit")
            return message

        await self.app(scope, bounded_receive(), send)