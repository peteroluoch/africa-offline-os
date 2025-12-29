from aos.db.migrations import (
    _001_initial_schema,
    _002_create_auth_tables,
    _003_create_agri_tables,
    _004_create_transport_tables,
    _005_create_community_tables,
    _006_telegram_users,
    _007_domain_aware_users,
    _008_transport_v2_schema,
    _009_community_members,
    _010_broadcast_tables,
    _011_community_activity_log,
    _012_community_admin_rbac,
    _013_ensure_base_roles,
)

# Strict migration registry
MIGRATIONS = [
    _001_initial_schema,
    _002_create_auth_tables,
    _003_create_agri_tables,
    _004_create_transport_tables,
    _005_create_community_tables,
    _006_telegram_users,
    _007_domain_aware_users,
    _008_transport_v2_schema,
    _009_community_members,
    _010_broadcast_tables,
    _011_community_activity_log,
    _012_community_admin_rbac,
    _013_ensure_base_roles,
]
