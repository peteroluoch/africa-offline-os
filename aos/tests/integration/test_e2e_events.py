import asyncio

import pytest

from aos.api.app import reset_globals
from aos.bus.dispatcher import EventDispatcher
from aos.bus.event_store import EventStore
from aos.bus.events import Event
from aos.core.security.identity import NodeIdentityManager
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS


class MockHandler:
    def __init__(self):
        self.received_events = []

    async def handle(self, event: Event):
        self.received_events.append(event)

@pytest.fixture(autouse=True)
def cleanup():
    reset_globals()
    yield
    reset_globals()

@pytest.mark.asyncio
async def test_e2e_verified_event_flow(tmp_path):
    """
    Verify the "Universal Socket" flow:
    1. Event emitted by business logic.
    2. Event signed by NodeIdentity (Phase 2).
    3. Event persisted to SQLite (Phase 3).
    4. Event dispatched to subscribers (Phase 1).
    """
    # 1. Setup Infrastructure
    db_path = tmp_path / "e2e.db"
    conn = connect(str(db_path))
    MigrationManager(conn).apply_migrations(MIGRATIONS)
    conn.close() # Close connection, EventStore will open its own

    # Setup Identity
    keys_dir = tmp_path / "keys"
    identity = NodeIdentityManager(keys_dir)
    identity.ensure_identity()

    # Setup Bus
    store = EventStore(str(db_path))
    await store.initialize()
    dispatcher = EventDispatcher(store)

    # 2. Register Subscriber
    handler = MockHandler()
    dispatcher.subscribe("payment.processed", handler.handle)

    # 3. Create & Emit Event
    payload = {"amount": 500, "currency": "KES"}

    # Ideally, events should be signed at emission.
    # For now, we simulate the signed payload structure.
    # In a full module, the Module base class would auto-sign.
    signature = identity.sign(str(payload).encode())

    event = Event(
        name="payment.processed",
        payload=payload,
        metadata={"signature": signature.hex(), "pub_key": identity.get_public_key().hex()}
    )

    await dispatcher.dispatch(event)

    # Allow background task to process
    await asyncio.sleep(0.5)

    # 4. Verification

    # A. Verify Persistence (Offline Safety)
    # The dispatcher should have autosaved it.
    stored_events = await store.get_pending_events(limit=10)
    assert len(stored_events) == 0 # Should be marked processed instantly if successful

    # B. Verify Delivery
    assert len(handler.received_events) == 1
    received = handler.received_events[0]
    assert received.payload["amount"] == 500

    # C. Verify Signature Integrity
    # The receiver validates the signature (simulated here)
    assert identity.verify(
        str(received.payload).encode(),
        bytes.fromhex(received.metadata["signature"]),
        bytes.fromhex(received.metadata["pub_key"])
    ) is True

    conn.close()
