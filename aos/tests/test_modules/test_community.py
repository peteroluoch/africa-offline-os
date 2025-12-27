import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from aos.modules.community import CommunityModule
from aos.modules.community_ussd import CommunityUSSDHandler
from aos.core.channels.ussd import USSDSession
from aos.bus.dispatcher import EventDispatcher

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    with open("aos/db/migrations/005_community.sql", "r") as f:
        conn.executescript(f.read())
    return conn

@pytest.fixture
def community_module(db_conn):
    dispatcher = MagicMock(spec=EventDispatcher)
    return CommunityModule(dispatcher, db_conn)

@pytest.mark.asyncio
async def test_community_registration_and_inquiry(community_module):
    # 1. Register a group
    group = await community_module.register_group(
        name="St Mark's", 
        group_type="church", 
        admin_id="admin-1"
    )
    assert group.name == "St Mark's"
    
    # 2. Add a cached inquiry
    await community_module.add_cached_inquiry(
        group_id=group.id,
        pattern="Sunday service",
        response="Sunday service is at 9:00 AM."
    )
    
    # 3. Test inquiry handling
    response = await community_module.handle_inquiry(group.id, "What time is the Sunday service?")
    assert response == "Sunday service is at 9:00 AM."

@pytest.mark.asyncio
async def test_community_ussd_flow(community_module):
    handler = CommunityUSSDHandler(community_module)
    session = USSDSession("sess-123", "254700000000")
    
    # 1. Start Menu
    resp = await handler.process(session, "")
    assert "Community" in resp.content
    assert "Find Group" in resp.content
    
    # 2. Register a group for discovery
    await community_module.register_group("Test Church", "church", "admin-1")
    
    # 3. Choose Find Group
    resp = await handler.process(session, "3")
    assert "Select Group" in resp.content
    assert "Test Church" in resp.content
    
    # 4. Select the group
    resp = await handler.process(session, "1")
    assert "[Test Church]" in resp.content
    assert "Services/Times" in resp.content
    
    # 5. Send Inquiry
    resp = await handler.process(session, "3")
    assert "Type your message" in resp.content
    
    # 6. Submit Inquiry (with cache hit)
    group_id = community_module.list_groups()[0].id
    await community_module.add_cached_inquiry(group_id, "hello", "Hi there!")
    resp = await handler.process(session, "hello")
    assert "Hi there!" in resp.content
