"""
Phase 3 End-to-End Verification Script
Tests the complete community code flow
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_phase3_complete():
    """Complete Phase 3 verification"""
    
    logger.info("=" * 60)
    logger.info("PHASE 3 VERIFICATION - Community Codes")
    logger.info("=" * 60)
    
    # Test 1: Database Schema
    logger.info("\n[TEST 1] Database Schema Verification")
    conn = sqlite3.connect("aos.db")
    cursor = conn.execute("PRAGMA table_info(community_groups)")
    columns = {row[1] for row in cursor.fetchall()}
    
    assert "community_code" in columns, "Missing community_code column"
    assert "code_active" in columns, "Missing code_active column"
    logger.info("✅ Schema verified")
    
    # Test 2: Active Code Exists
    logger.info("\n[TEST 2] Active Community Code Check")
    cursor = conn.execute("""
        SELECT id, name, community_code, code_active 
        FROM community_groups 
        WHERE community_code IS NOT NULL AND code_active = 1
    """)
    active_codes = cursor.fetchall()
    
    assert len(active_codes) > 0, "No active community codes found"
    logger.info(f"✅ Found {len(active_codes)} active code(s)")
    
    for row in active_codes:
        logger.info(f"   - {row[1]}: '{row[2]}' (ID: {row[0]})")
    
    # Test 3: Repository Lookup
    logger.info("\n[TEST 3] Repository get_by_code() Test")
    from aos.db.engine import connect
    from aos.db.repository import CommunityGroupRepository
    
    db_conn = connect("aos.db")
    repo = CommunityGroupRepository(db_conn)
    
    test_code = active_codes[0][2]  # Use first active code
    logger.info(f"Testing lookup for: '{test_code}'")
    
    # Test exact match
    result = repo.get_by_code(test_code)
    assert result is not None, f"Failed to find code: {test_code}"
    logger.info(f"✅ Exact match found: {result.name}")
    
    # Test case insensitivity
    result_lower = repo.get_by_code(test_code.lower())
    assert result_lower is not None, "Case-insensitive lookup failed"
    logger.info(f"✅ Lowercase match found: {result_lower.name}")
    
    result_upper = repo.get_by_code(test_code.upper())
    assert result_upper is not None, "Uppercase lookup failed"
    logger.info(f"✅ Uppercase match found: {result_upper.name}")
    
    # Test with whitespace
    result_space = repo.get_by_code(f"  {test_code}  ")
    assert result_space is not None, "Whitespace handling failed"
    logger.info(f"✅ Whitespace-padded match found: {result_space.name}")
    
    # Test 4: Module Integration
    logger.info("\n[TEST 4] CommunityModule Integration")
    from aos.modules.community import CommunityModule
    from aos.bus.dispatcher import EventDispatcher
    
    dispatcher = EventDispatcher()
    module = CommunityModule(dispatcher, db_conn)
    
    result = module.get_group_by_code(test_code)
    assert result is not None, "Module lookup failed"
    logger.info(f"✅ Module lookup successful: {result.name}")
    
    # Test 5: Invalid Code Rejection
    logger.info("\n[TEST 5] Invalid Code Rejection")
    invalid = repo.get_by_code("INVALID_CODE_999")
    assert invalid is None, "Invalid code should return None"
    logger.info("✅ Invalid code correctly rejected")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("ALL TESTS PASSED ✅")
    logger.info("=" * 60)
    logger.info("\nNext Steps:")
    logger.info(f"1. Deploy to production: fly deploy --app africa-offline-os")
    logger.info(f"2. In Telegram, type: {test_code}")
    logger.info(f"3. Expected: Confirmation prompt to join '{result.name}'")
    logger.info("=" * 60)
    
    conn.close()
    db_conn.close()

if __name__ == "__main__":
    try:
        test_phase3_complete()
    except AssertionError as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
