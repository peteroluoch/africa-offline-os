"""
Test script to send a broadcast and see the FAANG dashboard metrics update.
"""
import asyncio
import sqlite3
from aos.db.engine import connect
from aos.bus.dispatcher import EventDispatcher
from aos.modules.community import CommunityModule

async def main():
    # Connect to database
    conn = connect("aos.db")
    
    # Initialize module
    dispatcher = EventDispatcher()
    community = CommunityModule(dispatcher, conn)
    await community.initialize()
    
    print("=" * 60)
    print("🚀 TESTING FAANG BROADCAST SYSTEM")
    print("=" * 60)
    
    # Get existing groups
    groups = community._groups.list_all()
    if not groups:
        print("❌ No groups found. Please create a group first.")
        return
    
    print(f"\n📊 Found {len(groups)} groups:")
    groups_with_members = []
    for i, group in enumerate(groups[:10], 1):
        member_count = len(community.get_community_members(group.id))
        print(f"  {i}. {group.name} ({member_count} members)")
        if member_count > 0:
            groups_with_members.append((group, member_count))
    
    if not groups_with_members:
        print("\n❌ No groups with members found. Please add members to a group first.")
        return
    
    # Use group with most members
    group, member_count = max(groups_with_members, key=lambda x: x[1])
    print(f"\n✅ Using group: {group.name} (ID: {group.id})")
    
    # Get members
    members = community.get_community_members(group.id)
    print(f"📱 Members: {len(members)}")
    
    if len(members) == 0:
        print("⚠️  No members in this group. Add members first.")
        return
    
    # Calculate cost
    estimated_cost = len(members) * 0.80
    print(f"\n💰 Estimated Cost: KES {estimated_cost:.2f}")
    
    # Send broadcast
    print("\n📤 Sending broadcast...")
    try:
        announcement = await community.publish_announcement(
            group_id=group.id,
            message="🧪 TEST: FAANG Broadcast System - This is a test message to verify the new dashboard metrics!",
            urgency="normal",
            actor_id="system",  # Use system to bypass admin check
            cost_confirmed=True  # Explicitly confirm cost
        )
        
        print(f"✅ Broadcast created: {announcement.id}")
        
        # Get broadcast ID
        broadcast_id = community._broadcasts._db.execute(
            "SELECT id FROM broadcasts WHERE idempotency_key = ?", 
            (announcement.id,)
        ).fetchone()[0]
        
        print(f"📋 Broadcast ID: {broadcast_id}")
        
        # Check status
        broadcast = community._broadcasts.get_broadcast(broadcast_id)
        print(f"📊 Status: {broadcast['status']}")
        
        # Process the broadcast (simulate worker)
        print("\n⚙️  Processing broadcast (simulating worker)...")
        await community._worker._process_broadcast(broadcast_id)
        
        # Check delivery status
        cursor = conn.execute("""
            SELECT status, COUNT(*) 
            FROM broadcast_deliveries 
            WHERE broadcast_id = ?
            GROUP BY status
        """, (broadcast_id,))
        
        print("\n📈 Delivery Status:")
        for status, count in cursor.fetchall():
            print(f"  {status}: {count}")
        
        # Show overall stats
        print("\n" + "=" * 60)
        print("📊 OVERALL DASHBOARD METRICS")
        print("=" * 60)
        
        stats = conn.execute("""
            SELECT status, COUNT(*) 
            FROM broadcast_deliveries 
            GROUP BY status
        """).fetchall()
        
        for status, count in stats:
            emoji = "⏳" if status == "pending" else "✅" if status == "sent" else "❌"
            print(f"  {emoji} {status.upper()}: {count}")
        
        print("\n✨ Refresh your dashboard at http://localhost:8000/community to see the updated metrics!")
        
    except ValueError as e:
        if "COST_CONFIRMATION_REQUIRED" in str(e):
            print(f"\n🔒 COST GUARDRAIL TRIGGERED!")
            print(str(e).replace("|", "\n"))
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await community.shutdown()
        conn.close()

if __name__ == "__main__":
    asyncio.run(main())
