"""
Test Suite for Community Module (Staff-Engineer Standards).

Tests the strict interface compliance and infrastructure-first design.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from aos.bus.dispatcher import EventDispatcher
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.modules.community import CommunityModule


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite database with migrations applied."""
    conn = sqlite3.connect(":memory:")
    mgr = MigrationManager(conn)
    mgr.apply_migrations(MIGRATIONS)
    return conn


@pytest.fixture
def dispatcher():
    """Mock event dispatcher."""
    mock = AsyncMock(spec=EventDispatcher)
    return mock


@pytest.fixture
def community_module(db_conn, dispatcher):
    """Create a CommunityModule instance."""
    return CommunityModule(dispatcher, db_conn)


# --- Group Management Tests ---

@pytest.mark.asyncio
async def test_register_group(community_module, dispatcher):
    """Test group registration with tags and location."""
    group = await community_module.register_group(
        name="St Mark's Church",
        tags=["church", "sunday-service"],
        location="Kawangware, Nairobi",
        admin_id="OP-001",
        group_type="church",
        description="Community church"
    )
    
    assert group.id.startswith("GRP-")
    assert group.name == "St Mark's Church"
    assert json.loads(group.tags) == ["church", "sunday-service"]
    assert group.location == "Kawangware, Nairobi"
    assert group.active is True
    assert group.trust_level == "local"
    
    # Verify event was dispatched
    dispatcher.dispatch.assert_called_once()
    call_args = dispatcher.dispatch.call_args
    assert call_args[0][0] == "COMMUNITY_GROUP_REGISTERED"


@pytest.mark.asyncio
async def test_discover_groups_by_location(community_module):
    """Test location-based group discovery."""
    await community_module.register_group(
        name="Kawangware Church",
        tags=["church"],
        location="Kawangware, Nairobi",
        admin_id="OP-001"
    )
    await community_module.register_group(
        name="Kibera Mosque",
        tags=["mosque"],
        location="Kibera, Nairobi",
        admin_id="OP-002"
    )
    
    results = community_module.discover_groups(location="Kawangware")
    assert len(results) == 1
    assert results[0].name == "Kawangware Church"


@pytest.mark.asyncio
async def test_discover_groups_by_tags(community_module):
    """Test tag-based group discovery."""
    await community_module.register_group(
        name="St Mark's Church",
        tags=["church", "sunday-service"],
        location="Kawangware",
        admin_id="OP-001"
    )
    await community_module.register_group(
        name="Kibera Mosque",
        tags=["mosque", "friday-prayer"],
        location="Kibera",
        admin_id="OP-002"
    )
    
    results = community_module.discover_groups(tag_filter=["church"])
    assert len(results) == 1
    assert results[0].name == "St Mark's Church"


@pytest.mark.asyncio
async def test_discover_groups_inactive_filtered(community_module):
    """Test that inactive groups are excluded from discovery."""
    group = await community_module.register_group(
        name="Inactive Group",
        tags=["test"],
        location="Test Location",
        admin_id="OP-001"
    )
    
    # Manually deactivate
    group.active = False
    community_module._groups.save(group)
    
    results = community_module.discover_groups()
    assert len(results) == 0


# --- Event Management Tests ---

@pytest.mark.asyncio
async def test_publish_event(community_module, dispatcher):
    """Test event publishing with language support."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    start_time = datetime.utcnow() + timedelta(days=1)
    event = await community_module.publish_event(
        group_id=group.id,
        title="Sunday Service",
        event_type="service",
        start_time=start_time,
        language="sw"
    )
    
    assert event.id.startswith("EVT-")
    assert event.title == "Sunday Service"
    assert event.language == "sw"
    assert event.visibility == "public"
    
    # Verify event was dispatched
    assert dispatcher.dispatch.call_count == 2  # 1 for group, 1 for event


@pytest.mark.asyncio
async def test_list_events_by_location(community_module):
    """Test event listing filtered by location."""
    group1 = await community_module.register_group(
        name="Group 1",
        tags=["test"],
        location="Kawangware",
        admin_id="OP-001"
    )
    group2 = await community_module.register_group(
        name="Group 2",
        tags=["test"],
        location="Kibera",
        admin_id="OP-002"
    )
    
    start_time = datetime.utcnow()
    await community_module.publish_event(
        group_id=group1.id,
        title="Event 1",
        event_type="meeting",
        start_time=start_time
    )
    await community_module.publish_event(
        group_id=group2.id,
        title="Event 2",
        event_type="meeting",
        start_time=start_time
    )
    
    results = community_module.list_events(location="Kawangware")
    assert len(results) == 1
    assert results[0].title == "Event 1"


# --- Announcement Tests ---

@pytest.mark.asyncio
async def test_publish_announcement(community_module, dispatcher):
    """Test announcement publishing with expiry."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    expires_at = datetime.utcnow() + timedelta(days=7)
    announcement = await community_module.publish_announcement(
        group_id=group.id,
        message="Important announcement",
        urgency="urgent",
        expires_at=expires_at,
        target_audience="members"
    )
    
    assert announcement.id.startswith("ANN-")
    assert announcement.urgency == "urgent"
    assert announcement.expires_at == expires_at
    assert announcement.target_audience == "members"


# --- Inquiry Handling Tests ---

@pytest.mark.asyncio
async def test_handle_inquiry_cache_hit(community_module):
    """Test inquiry handling with cache hit."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    # Add cached inquiry
    await community_module.add_cached_inquiry(
        group_id=group.id,
        normalized_question="service",
        answer="Sunday service is at 9:00 AM"
    )
    
    # Test inquiry
    answer, inquiry_id = await community_module.handle_inquiry(
        group_id=group.id,
        question="What time is the service?"
    )
    
    assert answer == "Sunday service is at 9:00 AM"
    assert inquiry_id is not None
    
    # Verify hit count incremented
    inquiry = community_module._inquiries.get_by_id(inquiry_id)
    assert inquiry.hit_count == 1


@pytest.mark.asyncio
async def test_handle_inquiry_cache_miss(community_module):
    """Test inquiry handling with cache miss."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    answer, inquiry_id = await community_module.handle_inquiry(
        group_id=group.id,
        question="Unknown question"
    )
    
    assert answer is None
    assert inquiry_id is None


@pytest.mark.asyncio
async def test_reply_to_inquiry(community_module):
    """Test replying to an inquiry updates the cache."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    inquiry = await community_module.add_cached_inquiry(
        group_id=group.id,
        normalized_question="test question",
        answer="old answer"
    )
    
    await community_module.reply_to_inquiry(
        inquiry_id=inquiry.id,
        response="new answer"
    )
    
    updated = community_module._inquiries.get_by_id(inquiry.id)
    assert updated.answer == "new answer"


@pytest.mark.asyncio
async def test_inquiry_hit_count_increments(community_module):
    """Test that inquiry hit count increments on each cache hit."""
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Test",
        admin_id="OP-001"
    )
    
    await community_module.add_cached_inquiry(
        group_id=group.id,
        normalized_question="service time",
        answer="9:00 AM"
    )
    
    # Hit the cache multiple times
    for _ in range(3):
        answer, inquiry_id = await community_module.handle_inquiry(
            group_id=group.id,
            question="service time"
        )
    
    inquiry = community_module._inquiries.get_by_id(inquiry_id)
    assert inquiry.hit_count == 3


# --- Interface Compliance Tests ---

def test_no_individual_accounts(community_module):
    """Verify that no individual user account logic exists."""
    # This is a design validation test
    # The module should only have group-level operations
    assert hasattr(community_module, "register_group")
    assert not hasattr(community_module, "register_user")
    assert not hasattr(community_module, "create_member")


def test_no_religion_specific_logic(community_module):
    """Verify no hardcoded religion-specific conditionals."""
    # Tags should be free-text, not enum-based
    # This test ensures the design allows any tag
    import inspect
    source = inspect.getsource(CommunityModule)
    
    # Check for hardcoded religion terms in conditionals
    forbidden_patterns = [
        'if.*"church"',
        'if.*"mosque"',
        'elif.*"church"',
        'elif.*"mosque"'
    ]
    
    import re
    for pattern in forbidden_patterns:
        assert not re.search(pattern, source, re.IGNORECASE), \
            f"Found hardcoded religion logic: {pattern}"
