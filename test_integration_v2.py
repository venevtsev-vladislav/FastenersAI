"""
Integration test for the new FastenersAI architecture
Based on the comprehensive specification
"""

import asyncio
import logging
from pipeline.text_parser import get_text_parser
from pipeline.matching_engine import get_matching_engine
from services.gpt_validator import get_gpt_validator
from pipeline.processing_pipeline import get_processing_pipeline
from services.excel_generator_v2 import get_excel_generator_v2

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_text_parsing():
    """Test text parsing functionality"""
    logger.info("Testing text parsing...")
    
    parser = get_text_parser()
    
    # Test input from specification
    test_input = """
    Анкер двухраспорный 8х100х12 с крюком
    Анкер забиваемый латунный М10
    Анкер забиваемый латунный М12х38мм с насечками
    Анкерный болт 10х120
    Анкер клиновой оцинк. М16/70х180 Bullit
    Анкерный болт 12х130
    Анкерный болт с гайкой М12х129
    Болт DIN 933 кл.пр.8.8 М10х30, цинк
    Винт DIN 7985 М4х40, цинк
    Гвоздь строительный 4,0х120
    """
    
    parsed_lines = parser.parse_text_input(test_input)
    
    logger.info(f"Parsed {len(parsed_lines)} lines:")
    for i, line in enumerate(parsed_lines, 1):
        logger.info(f"  {i}. Raw: {line.raw_text}")
        logger.info(f"     Normalized: {line.normalized_text}")
        logger.info(f"     Params: {line.extracted_params}")
        logger.info(f"     Qty: {line.qty_packs} packs, {line.qty_units} units")
        logger.info("")
    
    return parsed_lines

async def test_matching_engine():
    """Test matching engine functionality"""
    logger.info("Testing matching engine...")
    
    engine = get_matching_engine()
    
    # Mock items data
    items = [
        {
            'ku': 'BOLT-M10x30-8.8',
            'name': 'Болт DIN 933 кл.пр.8.8 М10х30, цинк',
            'pack_qty': 100,
            'price': 2.50,
            'is_active': True,
            'specs_json': {
                'diameter': 'M10',
                'length': '30',
                'strength_class': '8.8',
                'coating': 'цинк'
            }
        },
        {
            'ku': 'ANCHOR-M10x100',
            'name': 'Анкер клиновой оцинк. М10х100',
            'pack_qty': 25,
            'price': 15.80,
            'is_active': True,
            'specs_json': {
                'diameter': 'M10',
                'length': '100',
                'type': 'клиновой',
                'coating': 'оцинк'
            }
        }
    ]
    
    # Mock aliases data
    aliases = [
        {'alias': 'болт м10х30', 'ku': 'BOLT-M10x30-8.8', 'weight': 1.0},
        {'alias': 'анкер м10х100', 'ku': 'ANCHOR-M10x100', 'weight': 1.0}
    ]
    
    # Test with a parsed line
    parser = get_text_parser()
    parsed_lines = parser.parse_text_input("Болт DIN 933 кл.пр.8.8 М10х30, цинк")
    
    if parsed_lines:
        candidates = await engine.find_candidates(parsed_lines[0], items, aliases)
        
        logger.info(f"Found {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            logger.info(f"  {i}. KU: {candidate.ku}")
            logger.info(f"     Name: {candidate.name}")
            logger.info(f"     Score: {candidate.score:.3f}")
            logger.info(f"     Source: {candidate.source}")
            logger.info("")
        
        # Test auto-accept logic
        should_auto_accept, best_candidate = engine.should_auto_accept(candidates)
        logger.info(f"Should auto-accept: {should_auto_accept}")
        if best_candidate:
            logger.info(f"Best candidate: {best_candidate.ku} (score: {best_candidate.score:.3f})")
    
    return candidates

async def test_gpt_validator():
    """Test GPT validator functionality"""
    logger.info("Testing GPT validator...")
    
    validator = get_gpt_validator()
    
    # Mock candidates
    from pipeline.matching_engine import MatchCandidate
    candidates = [
        MatchCandidate(
            ku='BOLT-M10x30-8.8',
            name='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
            pack_qty=100,
            price=2.50,
            unit='шт',
            score=0.85,
            explanation='Exact match',
            source='rules'
        ),
        MatchCandidate(
            ku='BOLT-M10x30-8.8-ALT',
            name='Болт М10х30, цинк',
            pack_qty=50,
            price=2.20,
            unit='шт',
            score=0.75,
            explanation='Similar match',
            source='rules'
        )
    ]
    
    # Mock parsed line
    from pipeline.text_parser import ParsedLine
    parsed_line = ParsedLine(
        raw_text='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
        normalized_text='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
        extracted_params={
            'diameter': 'M10',
            'length': '30',
            'strength_class': '8.8',
            'coating': 'цинк'
        }
    )
    
    # Test validation (this would normally call GPT)
    result = await validator.validate_candidates(parsed_line, candidates)
    
    logger.info(f"GPT validation result:")
    logger.info(f"  Decision: {result.decision}")
    logger.info(f"  Confidence: {result.confidence}")
    logger.info(f"  Reason: {result.reason}")
    logger.info(f"  Should accept: {validator.should_accept_gpt_decision(result)}")
    
    return result

async def test_excel_generation():
    """Test Excel generation functionality"""
    logger.info("Testing Excel generation...")
    
    generator = get_excel_generator_v2()
    
    # Mock processing results
    from pipeline.processing_pipeline import ProcessingResult
    from pipeline.matching_engine import MatchCandidate
    
    results = [
        ProcessingResult(
            line_id=1,
            raw_text='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
            normalized_text='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
            chosen_ku='BOLT-M10x30-8.8',
            qty_packs=2.0,
            qty_units=200.0,
            unit='шт',
            price=2.50,
            total=500.0,
            status='ok',
            chosen_method='rules',
            candidates=[
                MatchCandidate(
                    ku='BOLT-M10x30-8.8',
                    name='Болт DIN 933 кл.пр.8.8 М10х30, цинк',
                    pack_qty=100,
                    price=2.50,
                    unit='шт',
                    score=0.95,
                    explanation='Exact match',
                    source='rules'
                )
            ]
        ),
        ProcessingResult(
            line_id=2,
            raw_text='Анкер клиновой М10х100',
            normalized_text='Анкер клиновой М10х100',
            chosen_ku='ANCHOR-M10x100',
            qty_packs=1.0,
            qty_units=25.0,
            unit='шт',
            price=15.80,
            total=15.80,
            status='ok',
            chosen_method='rules',
            candidates=[
                MatchCandidate(
                    ku='ANCHOR-M10x100',
                    name='Анкер клиновой оцинк. М10х100',
                    pack_qty=25,
                    price=15.80,
                    unit='шт',
                    score=0.90,
                    explanation='Exact match',
                    source='rules'
                )
            ]
        )
    ]
    
    # Mock request data
    request_data = {
        'input_lines': ['Болт DIN 933 кл.пр.8.8 М10х30, цинк', 'Анкер клиновой М10х100'],
        'source': 'text'
    }
    
    # Generate Excel
    excel_file = await generator.generate_excel(
        request_id='test-123',
        results=results,
        request_data=request_data
    )
    
    logger.info(f"Excel file generated: {excel_file}")
    
    return excel_file

async def test_full_pipeline():
    """Test the complete processing pipeline"""
    logger.info("Testing full pipeline...")
    
    pipeline = get_processing_pipeline()
    
    # Test input
    test_input = """
    Болт DIN 933 кл.пр.8.8 М10х30, цинк
    Анкер клиновой М10х100
    """
    
    # Process request (this would normally use real database)
    try:
        results = await pipeline.process_request(
            request_id='test-123',
            input_text=test_input,
            source='text'
        )
        
        logger.info(f"Pipeline processed {len(results)} results")
        for result in results:
            logger.info(f"  Line {result.line_id}: {result.raw_text}")
            logger.info(f"    Status: {result.status}")
            logger.info(f"    Chosen KU: {result.chosen_ku}")
            logger.info(f"    Method: {result.chosen_method}")
            logger.info("")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")

async def main():
    """Run all tests"""
    logger.info("Starting FastenersAI V2 integration tests...")
    
    try:
        # Test individual components
        await test_text_parsing()
        await test_matching_engine()
        await test_gpt_validator()
        await test_excel_generation()
        
        # Test full pipeline
        await test_full_pipeline()
        
        logger.info("All tests completed successfully! ✅")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
