import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from aos.db.engine import connect
from aos.db.repository import CommunityGroupRepository

conn = connect('aos.db')
repo = CommunityGroupRepository(conn)

# Get first group
groups = repo.list_all()
if not groups:
    print("No groups found!")
    exit(1)

group = groups[0]
print(f"\nTesting update of group: {group.name} ({group.id})")
print(f"Current code: {group.community_code}, active: {group.code_active}")

# Update it
group.community_code = 'TEST_CODE'
group.code_active = True

print("\nAttempting save...")
try:
    repo.save(group)
    print("\n✅ Success! Group saved.")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

conn.close()
