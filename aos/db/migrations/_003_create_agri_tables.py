from sqlite3 import Connection


def up(conn: Connection) -> None:
    """Create agri-domain tables."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            contact TEXT NOT NULL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS crops (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            growing_season TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS harvests (
            id TEXT PRIMARY KEY,
            farmer_id TEXT NOT NULL,
            crop_id TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit TEXT DEFAULT 'kg',
            quality_grade TEXT NOT NULL,
            harvest_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'stored',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id),
            FOREIGN KEY (crop_id) REFERENCES crops(id)
        )
    """)

    # Create some default crops for the Lighthouse module
    conn.execute("INSERT OR IGNORE INTO crops (id, name, crop_type, growing_season) VALUES (?, ?, ?, ?)",
                 ("maize-01", "Yellow Maize", "Cereal", "Long Rains"))
    conn.execute("INSERT OR IGNORE INTO crops (id, name, crop_type, growing_season) VALUES (?, ?, ?, ?)",
                 ("beans-01", "Rosecoco Beans", "Legume", "Short Rains"))
    conn.execute("INSERT OR IGNORE INTO crops (id, name, crop_type, growing_season) VALUES (?, ?, ?, ?)",
                 ("coffee-01", "Arabica Coffee", "Cash Crop", "Perennial"))

def down(conn: Connection) -> None:
    """Drop agri-domain tables."""
    conn.execute("DROP TABLE IF EXISTS harvests")
    conn.execute("DROP TABLE IF EXISTS crops")
    conn.execute("DROP TABLE IF EXISTS farmers")
