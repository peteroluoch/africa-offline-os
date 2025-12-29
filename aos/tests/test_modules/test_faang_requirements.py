"""
Test Suite: FAANG Cost Guardrail & Delivery Tracking
Verifies the three mandatory FAANG requirements:
1. Cost estimation with confirmation threshold
2. Dashboard status visibility
3. Event-driven delivery status updates
"""
import pytest
import sqlite3
from aos.bus.dispatcher import EventDispatcher
from aos.bus.events import Event
from aos.modules.community import CommunityModule
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS


@pytest.fixture
def db_conn():
    """Create in-memory database with all migrations."""
    conn = sqlite3.connect(":memory:")
    mgr = MigrationManager(conn)
    mgr.apply_migrations(MIGRATIONS)
    yield conn
    conn.close()


@pytest.fixture
def community_module(db_conn):
    """Create CommunityModule instance."""
    dispatcher = EventDispatcher()
    return CommunityModule(dispatcher, db_conn)


# ========== COST GUARDRAIL TESTS ==========

@pytest.mark.asyncio
async def test_cost_guardrail_blocks_expensive_broadcast(community_module):
    """
    🔒 FAANG REQUIREMENT: Cost guardrail must block sends above threshold without confirmation.
    """
    # Setup community with many members (expensive send)
    comm = await community_module.register_group(
        name="Large Community", tags=["church"], location="Nairobi", admin_id="admin-1"
    )
    
    # Add 200 members (200 * 0.80 = KES 160 > threshold of 100)
    for i in range(200):
        community_module.add_member_to_community(comm.id, f"user{i}", "sms")
    
    # Attempt to publish WITHOUT cost confirmation
    with pytest.raises(ValueError, match="COST_CONFIRMATION_REQUIRED"):
        await community_module.publish_announcement(
            group_id=comm.id,
            message="Expensive broadcast",
            actor_id="admin-1",
            cost_confirmed=False  # ❌ Not confirmed
        )


@pytest.mark.asyncio
async def test_cost_guardrail_allows_confirmed_broadcast(community_module):
    """
    ✅ FAANG REQUIREMENT: Cost guardrail allows sends when explicitly confirmed.
    """
    comm = await community_module.register_group(
        name="Large Community", tags=["church"], location="Nairobi", admin_id="admin-1"
    )
    
    # Add 200 members
    for i in range(200):
        community_module.add_member_to_community(comm.id, f"user{i}", "sms")
    
    # Publish WITH cost confirmation
    announcement = await community_module.publish_announcement(
        group_id=comm.id,
        message="Confirmed expensive broadcast",
        actor_id="admin-1",
        cost_confirmed=True  # ✅ Explicitly confirmed
    )
    
    assert announcement is not None
    assert announcement.message == "Confirmed expensive broadcast"


@pytest.mark.asyncio
async def test_cost_guardrail_allows_small_broadcasts(community_module):
    """
    ✅ FAANG REQUIREMENT: Small broadcasts below threshold proceed without confirmation.
    """
    comm = await community_module.register_group(
        name="Small Community", tags=["sacco"], location="Kisumu", admin_id="admin-2"
    )
    
    # Add only 10 members (10 * 0.80 = KES 8 < threshold of 100)
    for i in range(10):
        community_module.add_member_to_community(comm.id, f"user{i}", "sms")
    
    # Should proceed without confirmation
    announcement = await community_module.publish_announcement(
        group_id=comm.id,
        message="Small broadcast",
        actor_id="admin-2",
        cost_confirmed=False  # No confirmation needed
    )
    
    assert announcement is not None


@pytest.mark.asyncio
async def test_cost_calculation_accuracy(community_module):
    """
    📊 FAANG REQUIREMENT: Cost calculation must be accurate and transparent.
    """
    comm = await community_module.register_group(
        name="Test Community", tags=["test"], location="Test", admin_id="admin-3"
    )
    
    # Add exactly 126 members (126 * 0.80 = KES 100.80, just above threshold)
    for i in range(126):
        community_module.add_member_to_community(comm.id, f"user{i}", "sms")
    
    # Should trigger confirmation (> threshold)
    with pytest.raises(ValueError) as exc_info:
        await community_module.publish_announcement(
            group_id=comm.id,
            message="Test",
            actor_id="admin-3",
            cost_confirmed=False
        )
    
    error_msg = str(exc_info.value)
    assert "Estimated cost: KES 100.80" in error_msg
    assert "Recipients: 126" in error_msg
    assert "Channels: SMS, USSD" in error_msg


# ========== DELIVERY STATUS TRACKING TESTS ==========

@pytest.mark.asyncio
async def test_delivery_status_updates_on_success(community_module):
    """
    ✅ FAANG REQUIREMENT: Delivery status must update based on adapter confirmation.
    """
    comm = await community_module.register_group(
        name="Test Community", tags=["test"], location="Test", admin_id="admin-1"
    )
    community_module.add_member_to_community(comm.id, "user1", "sms")
    
    # Publish and process
    ann = await community_module.publish_announcement(
        group_id=comm.id,
        message="Test",
        actor_id="admin-1"
    )
    
    # Get broadcast ID
    brd_id = community_module._broadcasts._db.execute(
        "SELECT id FROM broadcasts WHERE idempotency_key = ?", (ann.id,)
    ).fetchone()[0]
    
    # Process broadcast
    await community_module._worker._process_broadcast(brd_id)
    
    # Get delivery ID
    delivery = community_module._broadcasts.fetch_pending_deliveries(brd_id, limit=1)
    if delivery:
        delivery_id = delivery[0]['id']
        
        # Simulate MESSAGE_SENT event from adapter
        await community_module._dispatcher.dispatch(Event(
            name="MESSAGE_SENT",
            payload={"correlation_id": delivery_id}
        ))
        
        # Allow event to process
        import asyncio
        await asyncio.sleep(0.1)
        
        # Verify status updated to 'sent'
        status = community_module._db.execute(
            "SELECT status FROM broadcast_deliveries WHERE id = ?", (delivery_id,)
        ).fetchone()[0]
        
        assert status == "sent"


@pytest.mark.asyncio
async def test_delivery_status_updates_on_failure(community_module):
    """
    ❌ FAANG REQUIREMENT: Failed deliveries must be tracked with error details.
    """
    comm = await community_module.register_group(
        name="Test Community", tags=["test"], location="Test", admin_id="admin-1"
    )
    community_module.add_member_to_community(comm.id, "user1", "sms")
    
    ann = await community_module.publish_announcement(
        group_id=comm.id,
        message="Test",
        actor_id="admin-1"
    )
    
    brd_id = community_module._broadcasts._db.execute(
        "SELECT id FROM broadcasts WHERE idempotency_key = ?", (ann.id,)
    ).fetchone()[0]
    
    await community_module._worker._process_broadcast(brd_id)
    
    delivery = community_module._broadcasts.fetch_pending_deliveries(brd_id, limit=1)
    if delivery:
        delivery_id = delivery[0]['id']
        
        # Simulate MESSAGE_FAILED event from adapter
        await community_module._dispatcher.dispatch(Event(
            name="MESSAGE_FAILED",
            payload={
                "correlation_id": delivery_id,
                "error": "Network timeout"
            }
        ))
        
        # Allow event to process
        import asyncio
        await asyncio.sleep(0.1)
        
        # Verify status and error
        res = community_module._db.execute(
            "SELECT status, error FROM broadcast_deliveries WHERE id = ?", (delivery_id,)
        ).fetchone()
        
        assert res[0] == "failed"
        assert "Network timeout" in res[1]
