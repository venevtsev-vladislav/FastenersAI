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
from database.supabase_client_v2 import SupabaseClientV2

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
                self.supabase_client = SupabaseClientV2()
            
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
                    # Create request line in database
                    line_id = await self.supabase_client.create_request_line(
                        request_id=request_id,
                        line_no=i,
                        raw_text=parsed_line.raw_text,
                        normalized_text=parsed_line.normalized_text
                    )
                    
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
                        price=None,
                        total=None,
                        status='error',
                        chosen_method='error',
                        candidates=[]
                    )
                    results.append(error_result)
            
            # Update request status
            await self.supabase_client.update_request_status(request_id, 'completed')
            
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
            for candidate in candidates:
                await self.supabase_client.add_candidate(
                    request_line_id=line_id,
                    ku=candidate.ku,
                    name=candidate.name,
                    score=candidate.score,
                    pack_qty=candidate.pack_qty,
                    price=candidate.price,
                    explanation=candidate.explanation,
                    source=candidate.source
                )
            
            # Check if we should auto-accept
            should_auto_accept, best_candidate = self.matching_engine.should_auto_accept(candidates)
            
            if should_auto_accept and best_candidate:
                # Auto-accept
                chosen_ku = best_candidate.ku
                status = 'ok'
                method = 'rules'
                
                # Calculate quantities and totals
                qty_packs, qty_units, price, total = self._calculate_quantities(
                    parsed_line, best_candidate
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
                qty_packs = qty_units = price = total = None
            
            # Update request line in database
            await self.supabase_client.update_request_line(
                line_id=line_id,
                chosen_ku=chosen_ku,
                qty_packs=qty_packs,
                qty_units=qty_units,
                price=price,
                total=total,
                status=status,
                chosen_method=method
            )
            
            return ProcessingResult(
                line_id=line_id,
                raw_text=parsed_line.raw_text,
                normalized_text=parsed_line.normalized_text,
                chosen_ku=chosen_ku,
                qty_packs=qty_packs,
                qty_units=qty_units,
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
                self.supabase_client = SupabaseClientV2()
            
            # Query the items table
            response = self.supabase_client.client.table('items').select('*').eq('is_active', True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error loading items: {e}")
            return []
    
    async def _load_aliases(self) -> List[Dict]:
        """Load aliases from database"""
        try:
            if not self.supabase_client:
                self.supabase_client = SupabaseClientV2()
            
            # Query the sku_aliases table
            response = self.supabase_client.client.table('sku_aliases').select('*').execute()
            
            return response.data if response.data else []
            
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
