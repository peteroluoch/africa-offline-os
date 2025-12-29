import asyncio

import pytest
import httpx
from httpx import AsyncClient

# We need to access the global dispatcher to inject events
import aos.api.app as app_module
from aos.api.app import create_app, reset_globals
from aos.bus.events import Event


@pytest.fixture
async def client():
    reset_globals()
    app = create_app()
    from aos.core.security.auth import auth_manager
    # Note: token issuance depends on identity_mgr which doesn't need lifespan, 
    # but we should be careful.
    token = auth_manager.issue_token({"sub": "admin", "role": "admin"})
    
    async with app.router.lifespan_context(app):
        import httpx
        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), 
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"}
        ) as ac:
            yield ac
    reset_globals()

@pytest.mark.asyncio
async def test_stream_connection(client):
    """Verify /stream endpoint accepts connections."""
    async with client.stream("GET", "/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

@pytest.mark.asyncio
async def test_stream_receives_events(client):
    """Verify events are pushed to the stream as HTML."""
    from aos.api.state import core_state
    dispatcher = core_state.event_dispatcher
    assert dispatcher is not None

    # Connect to stream using the authenticated fixture client
    async with client.stream("GET", "/stream") as response:
        assert response.status_code == 200

        # Dispatch event after a tiny delay to ensure listener is registered
        await asyncio.sleep(0.1)
        test_event = Event(name="test.event", payload={"status": "working"})
        await dispatcher.dispatch(test_event)

        # Read lines with timeout
        chunk_found = False
        try:
            async def read_stream():
                async for line in response.aiter_lines():
                    if "test.event" in line:
                        assert "working" in line
                        return True
                return False

            chunk_found = await asyncio.wait_for(read_stream(), timeout=2.0)
        except asyncio.TimeoutError:
            print("DEBUG: Timeout waiting for stream data")

        assert chunk_found, "Did not receive event in stream"
