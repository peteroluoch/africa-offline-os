import pytest
import asyncio
from httpx import AsyncClient
from aos.api.app import create_app, reset_globals
from aos.bus.events import Event
# We need to access the global dispatcher to inject events
import aos.api.app as app_module

@pytest.fixture
async def client():
    reset_globals()
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
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
    app = create_app()
    async with app.router.lifespan_context(app):
        
        print("DEBUG: Client connecting...")
        # Connect to stream
        async with AsyncClient(app=app, base_url="http://test").stream("GET", "/stream") as response:
            assert response.status_code == 200
            print("DEBUG: Stream connected.")
            
            # Inject event into global dispatcher
            dispatcher = app_module._event_dispatcher
            assert dispatcher is not None
            print("DEBUG: Dispatcher found.")
            
            test_event = Event(name="test.event", payload={"status": "working"})
            await dispatcher.dispatch(test_event)
            print("DEBUG: Event dispatched.")
            
            # Read lines with timeout
            chunk_found = False
            try:
                # Wrap iteration in timeout
                async def read_stream():
                    async for line in response.aiter_lines():
                        print(f"DEBUG: Received line: {line}")
                        if "test.event" in line:
                            assert "<tr>" in line
                            assert "working" in line
                            return True
                    return False

                chunk_found = await asyncio.wait_for(read_stream(), timeout=2.0)
            except asyncio.TimeoutError:
                print("DEBUG: Timeout waiting for stream data")
                
            # Note: Since the generator is infinite, we must break or timeout.
            # aiter_lines doesn't inherently timeout, the test runner does.
            # We rely on 'break' happening quickly.

            assert chunk_found, "Did not receive event in stream"
