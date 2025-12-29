"""
Seed script to populate community groups with realistic test data.
Run this to create 15 diverse community groups for testing pagination and UI.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import uuid
import sqlite3
from aos.db.engine import connect
from aos.bus.dispatcher import EventDispatcher
from aos.modules.community import CommunityModule

# Sample community groups representing real Kenyan communities
SAMPLE_GROUPS = [
    {
        "name": "St. Mary's Catholic Church",
        "tags": ["church", "catholic", "sunday-service"],
        "location": "Kawangware, Nairobi",
        "admin_id": "OP-001",
        "group_type": "church",
        "description": "Weekly mass and community outreach programs"
    },
    {
        "name": "Jamia Mosque Eastleigh",
        "tags": ["mosque", "friday-prayer", "islamic"],
        "location": "Eastleigh, Nairobi",
        "admin_id": "OP-002",
        "group_type": "mosque",
        "description": "Friday prayers and Quran study sessions"
    },
    {
        "name": "Kibera Youth Empowerment",
        "tags": ["youth", "empowerment", "skills"],
        "location": "Kibera, Nairobi",
        "admin_id": "OP-003",
        "group_type": "youth-group",
        "description": "Skills training and mentorship for youth"
    },
    {
        "name": "Umoja SACCO",
        "tags": ["sacco", "savings", "loans"],
        "location": "Umoja, Nairobi",
        "admin_id": "OP-004",
        "group_type": "sacco",
        "description": "Community savings and credit cooperative"
    },
    {
        "name": "Mama Mboga Traders Association",
        "tags": ["traders", "women", "market"],
        "location": "Gikomba Market, Nairobi",
        "admin_id": "OP-005",
        "group_type": "traders",
        "description": "Support network for vegetable vendors"
    },
    {
        "name": "Nairobi Baptist Church",
        "tags": ["church", "baptist", "sunday-service"],
        "location": "Ngong Road, Nairobi",
        "admin_id": "OP-006",
        "group_type": "church",
        "description": "Sunday worship and Bible study groups"
    },
    {
        "name": "Mathare Community Health Workers",
        "tags": ["health", "community", "volunteers"],
        "location": "Mathare, Nairobi",
        "admin_id": "OP-007",
        "group_type": "health",
        "description": "Community health education and first aid"
    },
    {
        "name": "Kasarani Football Academy",
        "tags": ["sports", "youth", "football"],
        "location": "Kasarani, Nairobi",
        "admin_id": "OP-008",
        "group_type": "sports",
        "description": "Youth football training and tournaments"
    },
    {
        "name": "Huruma Seventh Day Adventist",
        "tags": ["church", "adventist", "saturday-service"],
        "location": "Huruma, Nairobi",
        "admin_id": "OP-009",
        "group_type": "church",
        "description": "Saturday worship and health ministry"
    },
    {
        "name": "Dandora Waste Pickers Cooperative",
        "tags": ["cooperative", "environment", "recycling"],
        "location": "Dandora, Nairobi",
        "admin_id": "OP-010",
        "group_type": "cooperative",
        "description": "Waste recycling and environmental conservation"
    },
    {
        "name": "Korogocho Women's Group",
        "tags": ["women", "empowerment", "crafts"],
        "location": "Korogocho, Nairobi",
        "admin_id": "OP-011",
        "group_type": "women-group",
        "description": "Beadwork and handicrafts cooperative"
    },
    {
        "name": "Masjid Nur Mosque",
        "tags": ["mosque", "islamic", "community"],
        "location": "South C, Nairobi",
        "admin_id": "OP-012",
        "group_type": "mosque",
        "description": "Daily prayers and Islamic education"
    },
    {
        "name": "Kayole Boda Boda Association",
        "tags": ["transport", "boda-boda", "riders"],
        "location": "Kayole, Nairobi",
        "admin_id": "OP-013",
        "group_type": "transport",
        "description": "Motorcycle taxi riders welfare group"
    },
    {
        "name": "Mukuru Arts & Culture Center",
        "tags": ["arts", "culture", "youth"],
        "location": "Mukuru, Nairobi",
        "admin_id": "OP-014",
        "group_type": "arts",
        "description": "Music, dance, and drama programs"
    },
    {
        "name": "Zimmerman Farmers Market",
        "tags": ["farmers", "market", "agriculture"],
        "location": "Zimmerman, Nairobi",
        "admin_id": "OP-015",
        "group_type": "farmers",
        "description": "Weekly farmers market and agricultural training"
    }
]


async def seed_community_groups():
    """Seed the database with sample community groups and members."""
    print("[SEED] Seeding community groups...")
    
    # Connect to database
    conn = connect("aos.db")
    dispatcher = EventDispatcher()
    community_module = CommunityModule(dispatcher, conn)
    
    # Track created group IDs
    group_ids = []
    
    # Register each group
    for idx, group_data in enumerate(SAMPLE_GROUPS, 1):
        try:
            group = await community_module.register_group(**group_data)
            group_ids.append(group.id)
            print(f"[OK] [{idx}/15] Created Group: {group.name}")
        except Exception as e:
            print(f"[FAIL] [{idx}/15] Failed to create {group_data['name']}: {e}")
            
    # Seed sample members
    print("\n[MEMBER] Seeding community members...")
    channels = ["sms", "ussd", "telegram", "whatsapp"]
    member_count = 0
    
    for group_id in group_ids:
        # 15 members per group
        for i in range(15):
            # Mix of formats: some with 07..., some with +254...
            if i % 2 == 0:
                user_id = f"0711{str(uuid.uuid4().int)[:6]}"
            else:
                user_id = f"+254722{str(uuid.uuid4().int)[:6]}"
                
            channel = channels[i % len(channels)]
            
            try:
                community_module.add_member_to_community(group_id, user_id, channel)
                member_count += 1
            except Exception as e:
                print(f"[WARN] Failed to add member {user_id}: {e}")
            
    print(f"[DONE] Seeded {member_count} members across {len(group_ids)} groups (~15 per group).")
    
    conn.close()
    print("\n[ALL] Seeding complete! Visit http://localhost:8000/community to see the groups and members.")


if __name__ == "__main__":
    asyncio.run(seed_community_groups())
