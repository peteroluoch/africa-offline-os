"""
Tests for Community Module CRUD operations, pagination, and member management.
"""
import pytest
from aos.modules.community import CommunityModule
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.bus.dispatcher import EventDispatcher


@pytest.fixture
async def community_module(tmp_path):
    """Create a community module with test database."""
    db_path = tmp_path / "test_community.db"
    conn = connect(str(db_path))
    
    # Run migrations
    migrator = MigrationManager(conn)
    migrator.apply_migrations(MIGRATIONS)
    
    dispatcher = EventDispatcher()
    module = CommunityModule(dispatcher, conn)
    
    yield module
    
    conn.close()


@pytest.mark.asyncio
async def test_list_groups_pagination(community_module):
    """Test that list_groups returns paginated results."""
    # Create 25 test groups
    for i in range(25):
        await community_module.register_group(
            name=f"Group {i}",
            tags=["test"],
            location="Nairobi",
            admin_id="admin123"
        )
    
    # Test first page
    result = community_module.list_groups(page=1, per_page=10)
    assert result["page"] == 1
    assert result["per_page"] == 10
    assert result["total"] == 25
    assert result["total_pages"] == 3
    assert len(result["groups"]) == 10
    assert result["groups"][0].name == "Group 0"
    
    # Test second page
    result = community_module.list_groups(page=2, per_page=10)
    assert result["page"] == 2
    assert len(result["groups"]) == 10
    assert result["groups"][0].name == "Group 10"
    
    # Test last page
    result = community_module.list_groups(page=3, per_page=10)
    assert result["page"] == 3
    assert len(result["groups"]) == 5
    assert result["groups"][0].name == "Group 20"


@pytest.mark.asyncio
async def test_pagination_edge_cases(community_module):
    """Test pagination with edge cases."""
    # Create 5 groups
    for i in range(5):
        await community_module.register_group(
            name=f"Group {i}",
            tags=["test"],
            location="Nairobi",
            admin_id="admin123"
        )
    
    # Test page 0 (should default to page 1)
    result = community_module.list_groups(page=0, per_page=10)
    assert result["page"] == 1
    
    # Test page beyond total (should clamp to last page)
    result = community_module.list_groups(page=999, per_page=10)
    assert result["page"] == 1  # Only 1 page exists
    
    # Test empty database
    module2 = CommunityModule(EventDispatcher(), community_module._conn)
    result = module2.list_groups(page=1, per_page=10)
    assert result["total"] == 0
    assert result["total_pages"] == 0
    assert len(result["groups"]) == 0


@pytest.mark.asyncio
async def test_member_crud_operations(community_module):
    """Test adding and removing members from a group."""
    # Create a group
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Nairobi",
        admin_id="admin123"
    )
    
    # Add members
    await community_module.add_member_to_community(
        community_id=group.id,
        user_id="+254712345678",
        channel="sms"
    )
    
    await community_module.add_member_to_community(
        community_id=group.id,
        user_id="@testuser",
        channel="telegram"
    )
    
    # List members
    members = community_module.get_community_members(group.id)
    assert len(members) == 2
    assert any(m.user_id == "+254712345678" for m in members)
    assert any(m.user_id == "@testuser" for m in members)
    
    # Remove a member
    success = await community_module.remove_member_from_community(
        community_id=group.id,
        user_id="+254712345678",
        channel="sms"
    )
    assert success is True
    
    # Verify removal
    members = community_module.get_community_members(group.id)
    assert len(members) == 1
    assert members[0].user_id == "@testuser"


@pytest.mark.asyncio
async def test_group_deactivation(community_module):
    """Test soft-deleting a group."""
    # Create a group
    group = await community_module.register_group(
        name="Test Group",
        tags=["test"],
        location="Nairobi",
        admin_id="admin123"
    )
    
    # Deactivate it
    success = await community_module.deactivate_group(
        group_id=group.id,
        admin_id="admin123"
    )
    assert success is True
    
    # Verify it's no longer in active list
    result = community_module.list_groups(page=1, per_page=10)
    assert len(result["groups"]) == 0


@pytest.mark.asyncio
async def test_member_isolation(community_module):
    """Test that members are isolated to their communities."""
    # Create two groups
    group_a = await community_module.register_group(
        name="Group A",
        tags=["test"],
        location="Nairobi",
        admin_id="admin123"
    )
    
    group_b = await community_module.register_group(
        name="Group B",
        tags=["test"],
        location="Mombasa",
        admin_id="admin456"
    )
    
    # Add members to each group
    await community_module.add_member_to_community(
        community_id=group_a.id,
        user_id="+254711111111",
        channel="sms"
    )
    
    await community_module.add_member_to_community(
        community_id=group_b.id,
        user_id="+254722222222",
        channel="sms"
    )
    
    # Verify isolation
    members_a = community_module.get_community_members(group_a.id)
    members_b = community_module.get_community_members(group_b.id)
    
    assert len(members_a) == 1
    assert len(members_b) == 1
    assert members_a[0].user_id == "+254711111111"
    assert members_b[0].user_id == "+254722222222"
