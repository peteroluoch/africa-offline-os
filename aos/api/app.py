from __future__ import annotations

from fastapi import FastAPI

from aos.core.health import HealthStatus


def create_app() -> FastAPI:
    app = FastAPI(title="A-OS", version="0.0.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": HealthStatus().status}

    return app
