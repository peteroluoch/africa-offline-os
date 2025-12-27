#!/usr/bin/env python3
"""
Seed Transport Zones for Nairobi
Populates the database with real Nairobi transport zones for testing Transport Module v2.
"""
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS
from aos.core.config import Settings
from aos.bus.dispatcher import EventDispatcher
from aos.modules.transport import TransportModule

def seed_nairobi_zones():
    """Seed Nairobi transport zones."""
    print("🚌 Seeding Nairobi Transport Zones...\n")
    
    # Initialize database
    settings = Settings()
    db_conn = connect(settings.sqlite_path)
    
    # Run migrations
    mgr = MigrationManager(db_conn)
    mgr.apply_migrations(MIGRATIONS)
    
    # Initialize Transport Module
    dispatcher = EventDispatcher()
    transport = TransportModule(dispatcher, db_conn)
    
    # Define Nairobi zones
    zones = [
        # Major Roads
        {
            "name": "Waiyaki Way",
            "type": "road",
            "location_scope": "Westlands-CBD",
            "description": "Major highway connecting Westlands to CBD"
        },
        {
            "name": "Thika Road",
            "type": "road",
            "location_scope": "Thika-CBD",
            "description": "Superhighway to Thika and Eastern Bypass"
        },
        {
            "name": "Mombasa Road",
            "type": "road",
            "location_scope": "Industrial Area-CBD",
            "description": "Main route to Jomo Kenyatta Airport and Mombasa"
        },
        {
            "name": "Ngong Road",
            "type": "road",
            "location_scope": "Ngong-CBD",
            "description": "Route through Kilimani, Hurlingham to CBD"
        },
        {
            "name": "Jogoo Road",
            "type": "road",
            "location_scope": "Eastlands-CBD",
            "description": "Eastern corridor to Donholm, Umoja, Kayole"
        },
        
        # Key Areas
        {
            "name": "CBD (Central Business District)",
            "type": "area",
            "location_scope": "Nairobi Central",
            "description": "Downtown Nairobi business hub"
        },
        {
            "name": "Westlands",
            "type": "area",
            "location_scope": "Westlands",
            "description": "Commercial and residential area"
        },
        {
            "name": "Industrial Area",
            "type": "area",
            "location_scope": "Industrial Area",
            "description": "Manufacturing and warehousing zone"
        },
        
        # Major Stages
        {
            "name": "Rongai Stage",
            "type": "stage",
            "location_scope": "Rongai",
            "description": "Main matatu stage for Rongai route"
        },
        {
            "name": "Kawangware Stage",
            "type": "stage",
            "location_scope": "Kawangware",
            "description": "Matatu stage for Kawangware and surrounding areas"
        },
        {
            "name": "Githurai 45",
            "type": "stage",
            "location_scope": "Githurai",
            "description": "Major stage on Thika Road"
        },
        {
            "name": "Machakos Country Bus",
            "type": "stage",
            "location_scope": "CBD",
            "description": "Long-distance bus terminal for Machakos and Eastern Kenya"
        },
        
        # Key Junctions
        {
            "name": "Westlands Roundabout",
            "type": "junction",
            "location_scope": "Westlands",
            "description": "Major junction connecting Waiyaki Way and Uhuru Highway"
        },
        {
            "name": "Museum Hill Roundabout",
            "type": "junction",
            "location_scope": "Museum Hill",
            "description": "Junction near National Museum"
        },
        {
            "name": "Pangani Roundabout",
            "type": "junction",
            "location_scope": "Pangani",
            "description": "Junction on Thika Road"
        }
    ]
    
    # Register zones
    registered_zones = []
    for zone_data in zones:
        zone_id = transport.register_zone(
            name=zone_data["name"],
            type=zone_data["type"],
            location_scope=zone_data["location_scope"]
        )
        registered_zones.append({
            "id": zone_id,
            "name": zone_data["name"],
            "type": zone_data["type"]
        })
        print(f"✅ Registered: {zone_data['name']} ({zone_data['type']})")
    
    print(f"\n🎉 Successfully seeded {len(registered_zones)} Nairobi transport zones!")
    print("\n📊 Zone Breakdown:")
    print(f"   - Roads: {len([z for z in zones if z['type'] == 'road'])}")
    print(f"   - Areas: {len([z for z in zones if z['type'] == 'area'])}")
    print(f"   - Stages: {len([z for z in zones if z['type'] == 'stage'])}")
    print(f"   - Junctions: {len([z for z in zones if z['type'] == 'junction'])}")
    
    print("\n🧪 Test Commands (Telegram):")
    print("   /zones - List all zones")
    print("   /state Waiyaki Way - Check Waiyaki Way intelligence")
    print("   /traffic Thika Road flowing - Report traffic on Thika Road")
    print("   /avl Rongai Stage Rongai available - Report vehicles to Rongai")
    
    db_conn.close()
    return registered_zones

if __name__ == "__main__":
    seed_nairobi_zones()
