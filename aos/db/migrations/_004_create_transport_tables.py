"""
Migration 004: Create Transport Tables.
Defines tables for vehicles, routes, and bookings.
"""
import sqlite3
import logging
import uuid
import json

logger = logging.getLogger("aos.db.migrations")

def migrate(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # Routes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS routes (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        start_point TEXT,
        end_point TEXT,
        base_price REAL,
        metadata TEXT
    )
    """)
    
    # Vehicles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id TEXT PRIMARY KEY,
        plate_number TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL, -- Matatu, Boda Boda, Truck
        capacity INTEGER,
        current_route_id TEXT,
        current_status TEXT, -- AVAILABLE, FULL, EN_ROUTE, OFF_DUTY
        last_seen TIMESTAMP,
        metadata TEXT,
        FOREIGN KEY (current_route_id) REFERENCES routes (id)
    )
    """)
    
    # Bookings/Status Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        vehicle_id TEXT,
        route_id TEXT,
        customer_phone TEXT,
        status TEXT, -- PENDING, CONFIRMED, CANCELLED
        seats INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
        FOREIGN KEY (route_id) REFERENCES routes (id)
    )
    """)
    
    # Bootstrap some data
    routes = [
        ("r-46", "Route 46 (Town - Kawangware)", "Town", "Kawangware", 50.0),
        ("r-23", "Route 23 (Town - Rongai)", "Town", "Rongai", 100.0),
        ("r-1", "Route 1 (Town - Kibera)", "Town", "Kibera", 30.0)
    ]
    
    for rid, name, start, end, price in routes:
        cursor.execute(
            "INSERT OR IGNORE INTO routes (id, name, start_point, end_point, base_price) VALUES (?, ?, ?, ?, ?)",
            (rid, name, start, end, price)
        )
    
    conn.commit()
    logger.info("Migration 004: Transport tables created.")
