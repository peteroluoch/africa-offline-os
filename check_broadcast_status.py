"""
Simple test to send a broadcast and check dashboard metrics.
"""
import sqlite3

# Connect to database
conn = sqlite3.connect("aos.db")

print("=" * 60)
print("🔍 CHECKING CURRENT BROADCAST STATUS")
print("=" * 60)

# Check broadcasts
cursor = conn.execute("SELECT COUNT(*) FROM broadcasts")
total_broadcasts = cursor.fetchone()[0]
print(f"\n📊 Total Broadcasts: {total_broadcasts}")

# Check deliveries
cursor = conn.execute("""
    SELECT status, COUNT(*) 
    FROM broadcast_deliveries 
    GROUP BY status
""")

print("\n📈 Delivery Status:")
stats = {"pending": 0, "sent": 0, "failed": 0}
for status, count in cursor.fetchall():
    stats[status] = count
    emoji = "⏳" if status == "pending" else "✅" if status == "sent" else "❌"
    print(f"  {emoji} {status.upper()}: {count}")

print("\n" + "=" * 60)
print("📊 DASHBOARD METRICS (What you'll see on UI)")
print("=" * 60)
print(f"  Pending:   {stats.get('pending', 0)} msgs")
print(f"  Delivered: {stats.get('sent', 0)} msgs")
print(f"  Failed:    {stats.get('failed', 0)} msgs")

# Check if there are any recent broadcasts
cursor = conn.execute("""
    SELECT id, community_id, status, created_at, sent_count, failed_count
    FROM broadcasts 
    ORDER BY created_at DESC 
    LIMIT 5
""")

print("\n📋 Recent Broadcasts:")
broadcasts = cursor.fetchall()
if broadcasts:
    for brd in broadcasts:
        print(f"  • {brd[0]}: {brd[2]} (sent: {brd[4]}, failed: {brd[5]})")
else:
    print("  No broadcasts yet")

conn.close()

print("\n✨ Refresh http://localhost:8000/community to see these metrics!")
