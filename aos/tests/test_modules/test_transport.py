import pytest
import sqlite3
from datetime import datetime, timedelta
from aos.bus.dispatcher import EventDispatcher
from aos.modules.transport import TransportModule
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    # Run migrations
    mgr = MigrationManager(conn)
    mgr.apply_migrations(MIGRATIONS)
    return conn

@pytest.fixture
def transport_module(db_conn):
    dispatcher = EventDispatcher()
    module = TransportModule(dispatcher, db_conn)
    return module

@pytest.mark.asyncio
async def test_register_zone(transport_module):
    zone_id = transport_module.register_zone("Waiyaki Way", "road", "Westlands-CBD")
    assert zone_id is not None
    
    zones = transport_module.discover_zones(location_scope="Westlands")
    assert len(zones) == 1
    assert zones[0].name == "Waiyaki Way"

@pytest.mark.asyncio
async def test_traffic_signal_reporting(transport_module):
    zone_id = transport_module.register_zone("Thika Road", "road")
    
    # Report traffic
    success = transport_module.report_traffic_signal(zone_id, "blocked", "agent_1")
    assert success is True
    
    intel = transport_module.get_zone_intelligence(zone_id)
    assert intel["current_state"] == "blocked"
    assert intel["confidence"] == 1.0

@pytest.mark.asyncio
async def test_signal_aggregation_consensus(transport_module):
    zone_id = transport_module.register_zone("CBD", "area")
    
    # Conflicting reports
    transport_module.report_traffic_signal(zone_id, "flowing", "user_1")
    transport_module.report_traffic_signal(zone_id, "flowing", "user_2")
    transport_module.report_traffic_signal(zone_id, "slow", "user_3")
    
    intel = transport_module.get_zone_intelligence(zone_id)
    assert intel["current_state"] == "flowing"
    assert intel["confidence"] == 2.0

@pytest.mark.asyncio
async def test_signal_expiry(transport_module):
    zone_id = transport_module.register_zone("Rongai Stage", "stage")
    
    # Report with immediate expiry (simulated via -1 mins)
    transport_module.report_traffic_signal(zone_id, "slow", "user_1", expires_in_minutes=-1)
    
    intel = transport_module.get_zone_intelligence(zone_id)
    assert intel["current_state"] == "unknown"

@pytest.mark.asyncio
async def test_availability_reporting(transport_module):
    zone_id = transport_module.register_zone("Machakos Country Bus", "stage")
    
    # Report availability
    transport_module.report_availability(zone_id, "Mombasa", "available", "driver_1")
    transport_module.report_availability(zone_id, "Kisumu", "limited", "agent_1")
    
    intel = transport_module.get_zone_intelligence(zone_id)
    assert len(intel["availability"]) == 2
    
    # Check shim compatibility
    status = transport_module.get_route_status(zone_id)
    assert len(status["vehicles"]) == 2
    assert "To: Mombasa" in status["vehicles"][0]["plate"]

@pytest.mark.asyncio
async def test_legacy_migration(db_conn):
    # Migration 008 handles the migration. 
    # Let's verify Migration 008 data transformation.
    cursor = db_conn.cursor()
    # Note: Migration 004 already created 'routes', so we just insert data if it exists
    # If it doesn't exist, we create it just for this test
    try:
        cursor.execute("INSERT INTO routes (id, name, start_point, end_point, base_price) VALUES (?, ?, ?, ?, ?)", 
                      ('r_test', 'Nairobi-Nakuru', 'Nairobi', 'Nakuru', 500.0))
    except sqlite3.OperationalError:
        cursor.execute("CREATE TABLE routes (id TEXT PRIMARY KEY, name TEXT, start_point TEXT, end_point TEXT, base_price REAL)")
        cursor.execute("INSERT INTO routes VALUES ('r_test', 'Nairobi-Nakuru', 'Nairobi', 'Nakuru', 500.0)")
    
    db_conn.commit()
    
    # Re-run migration 008 (simulated)
    from aos.db.migrations import _008_transport_v2_schema
    _008_transport_v2_schema.migrate(db_conn)
    
    dispatcher = EventDispatcher()
    module = TransportModule(dispatcher, db_conn)
    
    zones = module.discover_zones(type_filter="road")
    assert any(z.name == "Nairobi-Nakuru" for z in zones)

@pytest.mark.asyncio
async def test_avoidance_summary(transport_module):
    """Test get_avoidance_summary returns zones to avoid."""
    # Register zones
    waiyaki_id = transport_module.register_zone("Waiyaki Way", "road", "Westlands")
    thika_id = transport_module.register_zone("Thika Road", "road", "Thika")
    cbd_id = transport_module.register_zone("CBD", "area", "Nairobi")
    
    # Report traffic (blocked and slow)
    transport_module.report_traffic_signal(waiyaki_id, "blocked", "user_1")
    transport_module.report_traffic_signal(thika_id, "slow", "user_2")
    transport_module.report_traffic_signal(cbd_id, "flowing", "user_3")
    
    # Get avoidance summary
    summary = transport_module.get_avoidance_summary()
    
    # Should return 2 zones (blocked and slow, not flowing)
    assert len(summary) == 2
    
    # Blocked should be first (higher severity)
    assert summary[0]["zone_name"] == "Waiyaki Way"
    assert summary[0]["reason"] == "blocked"
    assert summary[0]["confidence"] == 1.0
    
    # Slow should be second
    assert summary[1]["zone_name"] == "Thika Road"
    assert summary[1]["reason"] == "slow"
    assert summary[1]["confidence"] == 1.0

@pytest.mark.asyncio
async def test_avoidance_summary_with_location_scope(transport_module):
    """Test get_avoidance_summary filters by location_scope."""
    # Register zones in different locations
    westlands_id = transport_module.register_zone("Waiyaki Way", "road", "Westlands")
    thika_id = transport_module.register_zone("Thika Road", "road", "Thika")
    
    # Report traffic
    transport_module.report_traffic_signal(westlands_id, "blocked", "user_1")
    transport_module.report_traffic_signal(thika_id, "blocked", "user_2")
    
    # Get avoidance summary for Westlands only
    summary = transport_module.get_avoidance_summary(location_scope="Westlands")
    
    # Should return only Westlands zone
    assert len(summary) == 1
    assert summary[0]["zone_name"] == "Waiyaki Way"

@pytest.mark.asyncio
async def test_avoidance_summary_empty_when_all_flowing(transport_module):
    """Test get_avoidance_summary returns empty list when all zones flowing."""
    zone_id = transport_module.register_zone("Mombasa Road", "road")
    
    # Report flowing traffic
    transport_module.report_traffic_signal(zone_id, "flowing", "user_1")
    
    # Get avoidance summary
    summary = transport_module.get_avoidance_summary()
    
    # Should be empty (no zones to avoid)
    assert len(summary) == 0
