"""
One-time script to backfill invite_slug for existing communities in production.
Run this via: fly ssh console --app africa-offline-os -C "python3 backfill_slugs.py"
"""
import sqlite3
import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text)
    return text.strip('_')

conn = sqlite3.connect("aos.db")
cursor = conn.cursor()

# Get all communities without slugs
cursor.execute("SELECT id, name FROM community_groups WHERE invite_slug IS NULL OR invite_slug = ''")
communities = cursor.fetchall()

print(f"Found {len(communities)} communities without slugs")

for community_id, name in communities:
    base_slug = slugify(name)
    slug = base_slug
    suffix = 1
    
    # Ensure uniqueness
    while True:
        cursor.execute("SELECT COUNT(*) FROM community_groups WHERE invite_slug = ?", (slug,))
        if cursor.fetchone()[0] == 0:
            break
        slug = f"{base_slug}_{suffix}"
        suffix += 1
    
    # Update
    cursor.execute("UPDATE community_groups SET invite_slug = ? WHERE id = ?", (slug, community_id))
    print(f"✓ {name} → {slug}")

conn.commit()
conn.close()
print("Done!")
