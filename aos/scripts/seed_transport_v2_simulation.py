
import asyncio
import logging
import sqlite3
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from aos.bus.dispatcher import EventDispatcher
from aos.modules.transport import TransportModule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aos.seed")

async def seed_simulation():
    """
    Seed Transport Module v2 with realistic Nairobi traffic data.
    """
    logger.info("🌱 Seeding Transport v2 Simulation Data...")
    
    # 1. Setup DB and Module
    db_path = "aos.db"
    conn = sqlite3.connect(db_path)
    dispatcher = EventDispatcher()
    module = TransportModule(dispatcher, conn)
    await module.initialize()

    # 2. Seed Zones (The Skeleton)
    logger.info("  ...Creating Zones")
    
    # Major Roads
    waiyaki_id = module.register_zone("Waiyaki Way", "road", "Westlands")
    thika_id = module.register_zone("Thika Road", "road", "Nairobi")
    mombasa_id = module.register_zone("Mombasa Road", "road", "Nairobi")
    langata_id = module.register_zone("Langata Road", "road", "Nairobi")
    
    # Key Hubs
    cdb_id = module.register_zone("CBD", "area", "Nairobi")
    westlands_id = module.register_zone("Westlands", "area", "Nairobi")
    railways_id = module.register_zone("Railways Station", "stage", "CBD")
    
    logger.info(f"    - Created 7 zones (Waiyaki, Thika, Mombasa, Langata, CBD, Westlands, Railways)")

    # 3. Seed Traffic Signals (The Flesh - Monday Morning Scenario)
    logger.info("  ...Injecting Traffic Signals (Monday Morning Scenario)")

    # Scenario: Waiyaki Way is BLOCKED (Construction)
    module.report_traffic_signal(waiyaki_id, "blocked", "user_254711000001", expires_in_minutes=1440)
    module.report_traffic_signal(waiyaki_id, "blocked", "agent_westlands", expires_in_minutes=1440) # Agent confirms
    logger.info("    ! Waiyaki Way -> BLOCKED (Confirmed by Agent)")

    # Scenario: Thika Road is FLOWING (Surprise!)
    module.report_traffic_signal(thika_id, "flowing", "user_254722000002", expires_in_minutes=1440)
    logger.info("    -> Thika Road -> FLOWING")

    # Scenario: Mombasa Road is SLOW
    module.report_traffic_signal(mombasa_id, "slow", "user_254733000003", expires_in_minutes=1440)
    logger.info("    ~ Mombasa Road -> SLOW")
    
    # Scenario: CBD is Gridlock
    module.report_traffic_signal(cdb_id, "blocked", "authority_police", expires_in_minutes=1440)
    logger.info("    ! CBD -> BLOCKED (Reported by Police)")

    # 4. Seed Availability (The Commuter View)
    logger.info("  ...Reporting Availability")
    
    # Railways Stage
    module.report_availability(railways_id, "Rongai", "limited", "marshal_jane")
    module.report_availability(railways_id, "Ngong", "available", "marshal_john")
    logger.info("    @ Railways: Rongai (Limited), Ngong (Available)")

    logger.info("✅ Seeding Complete. System is LIVE with data.")
    logger.info("   Try Telegram commands: /zones, /traffic, /avoid")

if __name__ == "__main__":
    asyncio.run(seed_simulation())
