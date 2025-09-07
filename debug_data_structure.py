"""
Debug script to check data structure
"""

import asyncio
import logging
from database.supabase_client import init_supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_data_structure():
    """Debug the data structure"""
    try:
        await init_supabase()
        from database.supabase_client import _supabase_client
        client = _supabase_client
        
        if not client:
            logger.error("Supabase client not initialized")
            return
        
        # Check parts_catalog structure
        logger.info("Checking parts_catalog structure...")
        response = client.table('parts_catalog').select('*').limit(3).execute()
        
        if response.data:
            logger.info(f"Sample parts_catalog records:")
            for i, item in enumerate(response.data[:3], 1):
                logger.info(f"Record {i}:")
                for key, value in item.items():
                    logger.info(f"  {key}: {value}")
        
        # Check aliases structure
        logger.info("\nChecking aliases structure...")
        response = client.table('aliases').select('*').limit(3).execute()
        
        if response.data:
            logger.info(f"Sample aliases records:")
            for i, item in enumerate(response.data[:3], 1):
                logger.info(f"Record {i}:")
                for key, value in item.items():
                    logger.info(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_data_structure())
