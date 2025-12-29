import asyncio
import sqlite3
import pytest
from unittest.mock import patch
import httpx

from aos.api.app import create_app, reset_globals
from aos.testing.fault_injection import simulate_disk_death, simulate_power_loss
from aos.db.engine import connect

@pytest.fixture(autouse=True)
def cleanup():
    reset_globals()
    yield
    reset_globals()

@pytest.mark.asyncio
async def test_resilience_disk_death(tmp_path):
    """
    Verify that the system handles a "Disk I/O Error" gracefully.
    Wait, 'gracefully' means it doesn't crash the entire async loop,
    but it should report 'unavailable' in health check.
    """
    db_path = tmp_path / "resilience.db"
    env = {
        "AOS_SQLITE_PATH": str(db_path),
        "AOS_RESOURCE_CHECK_INTERVAL": "0"
    }
    
    with patch.dict("os.environ", env):
        app = create_app()
        async with app.router.lifespan_context(app):
            # 1. Verify healthy initially
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/health")
                assert resp.json()["db_status"] == "healthy"

                # 2. Inject Disk Death directly into the app's connection
                from aos.api.app import get_db
                import aos.api.app
                real_db = get_db()
                
                from unittest.mock import MagicMock
                broken_db = MagicMock(wraps=real_db)
                def raise_io_error(*args, **kwargs):
                    raise sqlite3.OperationalError("disk I/O error")
                broken_db.execute.side_effect = raise_io_error
                
                # Replace global connection with the broken mock
                from aos.api.state import core_state
                with patch.object(core_state, "db_conn", broken_db):
                    # 3. Verify health endpoint reports 'unavailable' instead of crashing
                    resp = await client.get("/health")
                    assert resp.status_code == 200
                    assert resp.json()["db_status"] == "unavailable"

@pytest.mark.asyncio
async def test_resilience_power_loss_event_recovery(tmp_path):
    """
    Verify that events persisted to DB are recovered after a simulated power loss.
    """
    db_path = tmp_path / "power_loss.db"
    env = {
        "AOS_SQLITE_PATH": str(db_path),
    }
    
    with patch.dict("os.environ", env):
        # 1. Session 1: Create an event but don't process it yet?
        # Actually EventStore marks events as processed.
        # Let's say we have a pending event.
        from aos.bus.event_store import EventStore
        from aos.bus.events import Event
        
        store = EventStore(str(db_path))
        await store.initialize()
        
        event = Event(name="important.event", payload={"key": "value"})
        await store.enqueue(event) # This saves it with status='pending'
        
        # Simulating power loss (closing connection abruptly)
        simulate_power_loss(store)
        
        # 2. Session 2: Recovery
        # Re-initialize store
        store2 = EventStore(str(db_path))
        await store2.initialize()
        
        pending = await store2.get_pending_events()
        assert len(pending) == 1
        assert pending[0].name == "important.event"
        
        await store2.shutdown()
