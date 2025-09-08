"""
Main processing pipeline for fastener matching
Based on the comprehensive specification
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pipeline.text_parser import TextParser, ParsedLine
from pipeline.matching_engine import MatchingEngine, MatchCandidate
from services.gpt_validator import GPTValidator
from database.supabase_client import init_supabase, _supabase_client

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Processing result for a single line"""
    line_id: int
    raw_text: str
    normalized_text: str
    chosen_ku: Optional[str]
    qty_packs: Optional[float]
    qty_units: Optional[float]
    unit: Optional[str]
    price: Optional[float]
    total: Optional[float]
    status: str  # ok/needs_review/not_found/error
    chosen_method: str  # rules/vector/gpt/manual
    candidates: List[MatchCandidate]

class ProcessingPipeline:
    """Main processing pipeline"""
    
    def __init__(self):
        self.text_parser = TextParser()
        self.matching_engine = MatchingEngine()
        self.gpt_validator = GPTValidator()
        self.supabase_client = None
    
    async def process_request(self, request_id: str, input_text: str, 
                            source: str = 'text') -> List[ProcessingResult]:
        """Process a complete request"""
        try:
            # Initialize Supabase client
            if not self.supabase_client:
                await init_supabase()
                from database.supabase_client import _supabase_client
                self.supabase_client = _supabase_client
            
            # Parse input text into lines
            parsed_lines = self.text_parser.parse_text_input(input_text)
            
            if not parsed_lines:
                logger.warning("No lines parsed from input")
                return []
            
            # Load data from database
            items = await self._load_items()
            aliases = await self._load_aliases()
            
            if not items:
                logger.error("No items loaded from database")
                return []
            
            # Process each line
            results = []
            for i, parsed_line in enumerate(parsed_lines, 1):
                try:
                    # Create request line in database (simplified for testing)
                    line_id = f"{request_id}_line_{i}"
                    
                    # Process the line
                    result = await self._process_line(
                        line_id, parsed_line, items, aliases
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing line {i}: {e}")
                    # Create error result
                    error_result = ProcessingResult(
                        line_id=0,
                        raw_text=parsed_line.raw_text,
                        normalized_text=parsed_line.normalized_text,
                        chosen_ku=None,
                        qty_packs=None,
                        qty_units=None,
                        unit=None,
                        price=None,
                        total=None,
                        status='error',
                        chosen_method='error',
                        candidates=[]
                    )
                    results.append(error_result)
            
            # Update request status (simplified for testing)
            logger.info(f"Request {request_id} completed")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise
    
    async def _process_line(self, line_id: int, parsed_line: ParsedLine, 
                          items: List[Dict], aliases: List[Dict]) -> ProcessingResult:
        """Process a single line"""
        try:
            # Find candidates
            candidates = await self.matching_engine.find_candidates(
                parsed_line, items, aliases
            )

            # Save candidates to database
            logger.info(f"Found {len(candidates)} candidates for line")
            for candidate in candidates:
                # Add candidates to database (simplified for testing)
                pass
            
            # Check if we should auto-accept
            should_auto_accept, best_candidate = self.matching_engine.should_auto_accept(candidates)

            chosen_candidate = None
            if should_auto_accept and best_candidate:
                # Auto-accept
                chosen_candidate = best_candidate
                chosen_ku = best_candidate.ku
                status = 'ok'
                method = 'rules'

                # Calculate quantities and totals
                qty_packs, qty_units, price, total = self._calculate_quantities(
                    parsed_line, chosen_candidate
                )

            elif candidates:
                # Need GPT validation
                gpt_candidates = self.matching_engine.get_candidates_for_gpt(candidates)
                chosen_ku, status, method = await self.gpt_validator.validate_single_line(
                    parsed_line, gpt_candidates
                )

                # Find the chosen candidate
                chosen_candidate = None
                if chosen_ku:
                    for candidate in candidates:
                        if candidate.ku == chosen_ku:
                            chosen_candidate = candidate
                            break
                
                if chosen_candidate:
                    qty_packs, qty_units, price, total = self._calculate_quantities(
                        parsed_line, chosen_candidate
                    )
                else:
                    qty_packs = qty_units = price = total = None
                    
            else:
                # No candidates found
                chosen_ku = None
                status = 'not_found'
                method = 'rules'
                chosen_candidate = None
                qty_packs = qty_units = price = total = None
            
            # Update request line in database (simplified for testing)
            logger.info(f"Line processed: {status}")
            
            return ProcessingResult(
                line_id=line_id,
                raw_text=parsed_line.raw_text,
                normalized_text=parsed_line.normalized_text,
                chosen_ku=chosen_ku,
                qty_packs=qty_packs,
                qty_units=qty_units,
                unit=chosen_candidate.unit if chosen_candidate else None,
                price=price,
                total=total,
                status=status,
                chosen_method=method,
                candidates=candidates
            )
            
        except Exception as e:
            logger.error(f"Error processing line {line_id}: {e}")
            raise
    
    def _calculate_quantities(self, parsed_line: ParsedLine, 
                            candidate: MatchCandidate) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Calculate quantities and totals"""
        qty_packs = parsed_line.qty_packs
        qty_units = parsed_line.qty_units
        price = candidate.price
        total = None
        
        # If we have qty_packs and pack_qty, calculate qty_units
        if qty_packs and candidate.pack_qty:
            qty_units = qty_packs * candidate.pack_qty
        
        # Calculate total
        if price and (qty_units or qty_packs):
            total = price * (qty_units or qty_packs)
        
        return qty_packs, qty_units, price, total
    
    async def _load_items(self) -> List[Dict]:
        """Load items from database"""
        try:
            if not self.supabase_client:
                await init_supabase()
                from database.supabase_client import _supabase_client
                self.supabase_client = _supabase_client
            
            # Query the parts_catalog table
            response = self.supabase_client.table('parts_catalog').select('*').execute()
            
            if response.data:
                logger.info(f"Loaded {len(response.data)} items from database")
                # Convert to new format
                items = []
                for item in response.data:
                    items.append({
                        'sku': item.get('sku', ''),
                        'name': item.get('name', '') or '',
                        'pack_qty': item.get('pack_size', 1),
                        'price': item.get('price', 0),
                        'unit': item.get('unit', ''),
                        'is_active': True,
                        'specs_json': {
                            'diameter': item.get('diameter', ''),
                            'length': item.get('length', ''),
                            'strength_class': item.get('strength_class', ''),
                            'coating': item.get('coating', '')
                        }
                    })
                return items
            else:
                logger.warning("No items found in database, using sample data")
                # Fallback to sample data if database is empty
                return [
                    {
                        'sku': 'BOLT-M10x30-8.8',
                        'name': 'Болт DIN 933 кл.пр.8.8 М10х30, цинк',
                        'pack_qty': 100,
                        'price': 2.50,
                        'unit': 'шт',
                        'is_active': True,
                        'specs_json': {
                            'diameter': 'M10',
                            'length': '30',
                            'strength_class': '8.8',
                            'coating': 'цинк'
                        }
                    },
                    {
                        'sku': 'ANCHOR-M10x100',
                        'name': 'Анкер клиновой оцинк. М10х100',
                        'pack_qty': 25,
                        'price': 15.80,
                        'unit': 'шт',
                        'is_active': True,
                        'specs_json': {
                            'diameter': 'M10',
                            'length': '100',
                            'type': 'клиновой',
                            'coating': 'оцинк'
                        }
                    }
                ]
            
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            return []
    
    async def _load_aliases(self) -> List[Dict]:
        """Load aliases from database"""
        try:
            if not self.supabase_client:
                await init_supabase()
                from database.supabase_client import _supabase_client
                self.supabase_client = _supabase_client
            
            # Query the aliases table
            response = self.supabase_client.table('aliases').select('*').execute()
            
            if response.data:
                logger.info(f"Loaded {len(response.data)} aliases from database")
                # Convert to new format
                aliases = []
                for alias in response.data:
                    # Parse maps_to JSON to get ku
                    maps_to = alias.get('maps_to', {})
                    if isinstance(maps_to, str):
                        try:
                            maps_to = json.loads(maps_to)
                        except:
                            maps_to = {}
                    
                    # Handle different formats of maps_to
                    if isinstance(maps_to, dict):
                        # Single mapping - extract type and subtype
                        alias_type = maps_to.get('type', '')
                        alias_subtype = maps_to.get('subtype', '')
                        if alias_type:
                            aliases.append({
                                'alias': alias.get('alias', ''),
                                'type': alias_type,
                                'subtype': alias_subtype,
                                'weight': alias.get('confidence', 1.0)
                            })
                    elif isinstance(maps_to, list):
                        # Multiple mappings
                        for item in maps_to:
                            if isinstance(item, dict):
                                alias_type = item.get('type', '')
                                alias_subtype = item.get('subtype', '')
                                if alias_type:
                                    aliases.append({
                                        'alias': alias.get('alias', ''),
                                        'type': alias_type,
                                        'subtype': alias_subtype,
                                        'weight': alias.get('confidence', 1.0)
                                    })
                    else:
                        # Fallback
                        aliases.append({
                            'alias': alias.get('alias', ''),
                            'ku': '',
                            'weight': alias.get('confidence', 1.0)
                        })
                return aliases
            else:
                logger.warning("No aliases found in database, using sample data")
                # Fallback to sample aliases
                return [
                    {'alias': 'болт м10х30', 'ku': 'BOLT-M10x30-8.8', 'weight': 1.0},
                    {'alias': 'болт din 933 м10х30', 'ku': 'BOLT-M10x30-8.8', 'weight': 1.0},
                    {'alias': 'анкер м10х100', 'ku': 'ANCHOR-M10x100', 'weight': 1.0},
                    {'alias': 'анкер клиновой м10х100', 'ku': 'ANCHOR-M10x100', 'weight': 1.0}
                ]
            
        except Exception as e:
            logger.error(f"Error loading aliases: {e}")
            return []

# Global processing pipeline instance
_processing_pipeline = None

def get_processing_pipeline() -> ProcessingPipeline:
    """Get global processing pipeline instance"""
    global _processing_pipeline
    if _processing_pipeline is None:
        _processing_pipeline = ProcessingPipeline()
    return _processing_pipeline
