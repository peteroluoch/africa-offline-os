import pytest
import asyncio
from aos.api.app import create_app, reset_globals

@pytest.mark.asyncio
async def test_lifespan():
    reset_globals()
    app = create_app()
    print("DEBUG: Entering lifespan context")
    async with app.router.lifespan_context(app):
        print("DEBUG: Inside lifespan context")
        await asyncio.sleep(0.5)
    print("DEBUG: Exited lifespan context")
    reset_globals()
