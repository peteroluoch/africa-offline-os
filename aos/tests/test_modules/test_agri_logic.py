import pytest
import sqlite3
import uuid
from datetime import datetime, timezone
from aos.modules.agri import AgriModule
from aos.bus.dispatcher import EventDispatcher
from aos.db.models import FarmerDTO, HarvestDTO
from aos.db.migrations import _003_create_agri_tables

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    _003_create_agri_tables.up(conn)
    return conn

@pytest.fixture
def dispatcher():
    return EventDispatcher()

@pytest.fixture
def agri_module(dispatcher, db_conn):
    return AgriModule(dispatcher, db_conn)

@pytest.mark.asyncio
async def test_register_farmer(agri_module, dispatcher):
    # Track dispatched events
    dispatched_events = []
    async def track_event(event):
        dispatched_events.append(event)
    
    dispatcher.subscribe("agri.farmer_registered", track_event)
    
    farmer = FarmerDTO(
        id=str(uuid.uuid4()),
        name="Peter Aluru",
        location="Kisumu",
        contact="+254712345678"
    )
    
    await agri_module.register_farmer(farmer)
    
    # Verify persistence
    farmers = agri_module.list_all_farmers()
    assert len(farmers) == 1
    assert farmers[0].name == "Peter Aluru"
    
    # Wait for event processing
    import asyncio
    await asyncio.sleep(0.1)
    
    # Verify event dispatch
    assert len(dispatched_events) == 1
    assert dispatched_events[0].name == "agri.farmer_registered"
    assert dispatched_events[0].payload["id"] == farmer.id

@pytest.mark.asyncio
async def test_record_harvest(agri_module, dispatcher):
    dispatched_events = []
    async def track_event(event):
        dispatched_events.append(event)
    
    dispatcher.subscribe("agri.harvest_recorded", track_event)
    
    farmer_id = str(uuid.uuid4())
    harvest = HarvestDTO(
        id=str(uuid.uuid4()),
        farmer_id=farmer_id,
        crop_id="maize-01",
        quantity=500.5,
        unit="kg",
        quality_grade="A",
        harvest_date=datetime.now(timezone.utc),
        status="stored"
    )
    
    await agri_module.record_harvest(harvest)
    
    # Verify persistence
    harvests = agri_module.get_farmer_harvests(farmer_id)
    assert len(harvests) == 1
    assert harvests[0].quantity == 500.5
    
    # Wait for event processing
    import asyncio
    await asyncio.sleep(0.1)
    
    # Verify event dispatch
    assert len(dispatched_events) == 1
    assert dispatched_events[0].name == "agri.harvest_recorded"
    assert dispatched_events[0].payload["quantity"] == 500.5
