from aos.db.migrations import _001_initial_schema
from aos.db.migrations import _002_create_auth_tables
from aos.db.migrations import _003_create_agri_tables
from aos.db.migrations import _004_create_transport_tables

# Strict migration registry
MIGRATIONS = [
    _001_initial_schema,
    _002_create_auth_tables,
    _003_create_agri_tables,
    _004_create_transport_tables,
]
