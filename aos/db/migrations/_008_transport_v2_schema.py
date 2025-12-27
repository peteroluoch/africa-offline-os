"""
Migration 008: Transport Module v2 Schema.
Transitions from formal Route/Vehicle model to Zones/Signals/Availability.
"""
import logging
import sqlite3

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # 1. Transport Zones Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transport_zones (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- road, area, stage, junction
        location_scope TEXT,
        active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tz_location ON transport_zones(location_scope)")

    # 2. Traffic Signals Table (Time-series data)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic_signals (
        id TEXT PRIMARY KEY,
        zone_id TEXT NOT NULL,
        state TEXT NOT NULL, -- flowing, slow, blocked
        source TEXT NOT NULL, -- user, agent, authority
        confidence_score REAL DEFAULT 1.0,
        reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY (zone_id) REFERENCES transport_zones (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts_zone ON traffic_signals(zone_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ts_expiry ON traffic_signals(expires_at)")

    # 3. Transport Availability Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transport_availability (
        id TEXT PRIMARY KEY,
        zone_id TEXT NOT NULL,
        destination TEXT NOT NULL,
        availability_state TEXT NOT NULL, -- available, limited, none
        reported_by TEXT NOT NULL,
        reported_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME,
        FOREIGN KEY (zone_id) REFERENCES transport_zones (id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ta_zone_dest ON transport_availability(zone_id, destination)")

    # 4. Data Migration: Convert existing routes to transport_zones (type='road')
    # First check if routes table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='routes'")
    if cursor.fetchone():
        cursor.execute("SELECT id, name, start_point, end_point FROM routes")
        routes = cursor.fetchall()
        for route_id, name, start, end in routes:
            # We'll create a zone for the route itself
            cursor.execute("""
                INSERT OR IGNORE INTO transport_zones (id, name, type, location_scope)
                VALUES (?, ?, 'road', ?)
            """, (route_id, name, f"{start}-{end}"))

    conn.commit()
    logger.info("Migration 008: Transport v2 schema applied and data migrated.")
