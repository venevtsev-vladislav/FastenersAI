"""
Debug script to test the processing pipeline
"""

import asyncio
import logging
from pipeline.processing_pipeline import get_processing_pipeline
from database.supabase_client import init_supabase, _supabase_client

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_pipeline():
    """Debug the processing pipeline"""
    try:
        # Test Supabase connection
        logger.info("Testing Supabase connection...")
        await init_supabase()
        
        # Import after init
        from database.supabase_client import _supabase_client
        client = _supabase_client
        
        if not client:
            logger.error("Supabase client not initialized")
            return
        
        # Test processing pipeline
        logger.info("Testing processing pipeline...")
        pipeline = get_processing_pipeline()
        
        # Test loading items through pipeline
        logger.info("Testing items loading...")
        items = await pipeline._load_items()
        logger.info(f"Loaded {len(items)} items")
        
        if items:
            logger.info("Sample item:")
            logger.info(f"  KU: {items[0].get('ku', 'N/A')}")
            logger.info(f"  Name: {items[0].get('name', 'N/A')}")
            logger.info(f"  Price: {items[0].get('price', 'N/A')}")
        
        # Test loading aliases through pipeline
        logger.info("Testing aliases loading...")
        aliases = await pipeline._load_aliases()
        logger.info(f"Loaded {len(aliases)} aliases")
        
        if aliases:
            logger.info("Sample alias:")
            logger.info(f"  Alias: {aliases[0].get('alias', 'N/A')}")
            logger.info(f"  KU: {aliases[0].get('ku', 'N/A')}")
        
        test_input = "Болт DIN 933 кл.пр.8.8 М10х30, цинк"
        logger.info(f"Processing: {test_input}")
        
        results = await pipeline.process_request(
            request_id="debug-123",
            input_text=test_input,
            source="text"
        )
        
        logger.info(f"Processing completed. Results: {len(results)}")
        
        for i, result in enumerate(results, 1):
            logger.info(f"Result {i}:")
            logger.info(f"  Raw: {result.raw_text}")
            logger.info(f"  Normalized: {result.normalized_text}")
            logger.info(f"  Chosen KU: {result.chosen_ku}")
            logger.info(f"  Status: {result.status}")
            logger.info(f"  Method: {result.chosen_method}")
            logger.info(f"  Candidates: {len(result.candidates)}")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
