"""
Component tests for FastenersAI V2
Tests individual components without database dependency
"""

import asyncio
import logging
from pipeline.text_parser import get_text_parser
from pipeline.matching_engine import get_matching_engine
from services.gpt_validator import get_gpt_validator
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
    Болт DIN 933 кл.пр.8.8 М10х30, цинк
    Винт DIN 7985 М4х40, цинк
    """
    
    parsed_lines = parser.parse_text_input(test_input)
    
    logger.info(f"✅ Parsed {len(parsed_lines)} lines successfully")
    for i, line in enumerate(parsed_lines, 1):
        logger.info(f"  {i}. {line.raw_text} -> {line.normalized_text}")
        if line.extracted_params:
            logger.info(f"     Params: {line.extracted_params}")
    
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
        
        logger.info(f"✅ Found {len(candidates)} candidates")
        for i, candidate in enumerate(candidates, 1):
            logger.info(f"  {i}. {candidate.ku} (score: {candidate.score:.3f})")
        
        # Test auto-accept logic
        should_auto_accept, best_candidate = engine.should_auto_accept(candidates)
        logger.info(f"✅ Auto-accept: {should_auto_accept}")
        if best_candidate:
            logger.info(f"   Best: {best_candidate.ku} (score: {best_candidate.score:.3f})")
    
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
            score=0.85,
            explanation='Exact match',
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
    
    logger.info(f"✅ GPT validation result:")
    logger.info(f"   Decision: {result.decision}")
    logger.info(f"   Confidence: {result.confidence}")
    logger.info(f"   Should accept: {validator.should_accept_gpt_decision(result)}")
    
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
                    score=0.95,
                    explanation='Exact match',
                    source='rules'
                )
            ]
        )
    ]
    
    # Mock request data
    request_data = {
        'input_lines': ['Болт DIN 933 кл.пр.8.8 М10х30, цинк'],
        'source': 'text'
    }
    
    # Generate Excel
    excel_file = await generator.generate_excel(
        request_id='test-123',
        results=results,
        request_data=request_data
    )
    
    logger.info(f"✅ Excel file generated: {excel_file}")
    
    return excel_file

async def main():
    """Run all component tests"""
    logger.info("🚀 Starting FastenersAI V2 component tests...")
    
    try:
        # Test individual components
        await test_text_parsing()
        await test_matching_engine()
        await test_gpt_validator()
        await test_excel_generation()
        
        logger.info("🎉 All component tests completed successfully! ✅")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
