from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from fastapi import FastAPI


def register_lifecycle(app: FastAPI, startup: Callable[[], None], shutdown: Callable[[], None]) -> None:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        startup()
        try:
            yield
        finally:
            shutdown()

    app.router.lifespan_context = lifespan
