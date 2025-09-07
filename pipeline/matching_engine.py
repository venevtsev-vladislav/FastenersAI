"""
Matching and scoring engine for fastener identification
Based on the comprehensive specification
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pipeline.text_parser import ParsedLine

logger = logging.getLogger(__name__)

@dataclass
class MatchCandidate:
    """Match candidate data structure"""
    ku: str
    name: str
    pack_qty: Optional[float]
    price: Optional[float]
    score: float
    explanation: str
    source: str  # rules/vector/gpt

class MatchingEngine:
    """Main matching engine for fastener identification"""
    
    def __init__(self):
        # Scoring weights according to specification
        self.weights = {
            'exact_alias': 0.6,
            'ku_match': 1.0,
            'diameter_match': 0.3,
            'length_match': 0.3,
            'material_match': 0.15,
            'coating_match': 0.15,
            'type_match': 0.2,  # Required filter
            'standard_match': 0.1,
        }
        
        # Type filter patterns
        self.type_patterns = {
            'болт': ['болт', 'bolt'],
            'винт': ['винт', 'screw'],
            'саморез': ['саморез', 'self-tapping'],
            'анкер': ['анкер', 'anchor'],
            'гайка': ['гайка', 'nut'],
            'шайба': ['шайба', 'washer'],
            'дюбель': ['дюбель', 'dowel'],
            'шуруп': ['шуруп', 'wood screw'],
        }
    
    async def find_candidates(self, parsed_line: ParsedLine, items: List[Dict], 
                            aliases: List[Dict]) -> List[MatchCandidate]:
        """Find candidates for a parsed line"""
        candidates = []
        
        # 1. Exact alias match
        alias_candidates = await self._find_alias_matches(parsed_line, aliases, items)
        candidates.extend(alias_candidates)
        
        # 2. Fuzzy name/specs match
        fuzzy_candidates = await self._find_fuzzy_matches(parsed_line, items)
        candidates.extend(fuzzy_candidates)
        
        # 3. Apply type filter
        candidates = self._apply_type_filter(parsed_line, candidates)
        
        # 4. Calculate scores
        for candidate in candidates:
            candidate.score = self._calculate_score(parsed_line, candidate)
        
        # 5. Sort by score
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # 6. Remove duplicates (same KU)
        unique_candidates = []
        seen_kus = set()
        for candidate in candidates:
            if candidate.ku not in seen_kus:
                unique_candidates.append(candidate)
                seen_kus.add(candidate.ku)
        
        return unique_candidates
    
    async def _find_alias_matches(self, parsed_line: ParsedLine, aliases: List[Dict], 
                                items: List[Dict]) -> List[MatchCandidate]:
        """Find exact alias matches"""
        candidates = []
        
        # Create items lookup
        items_lookup = {item['ku']: item for item in items}
        
        for alias in aliases:
            if (alias.get('alias', '') or '').lower() == parsed_line.normalized_text.lower():
                item = items_lookup.get(alias['ku'])
                if item:
                    candidate = MatchCandidate(
                        ku=item['ku'],
                        name=item['name'],
                        pack_qty=item.get('pack_qty'),
                        price=item.get('price'),
                        score=0.0,  # Will be calculated later
                        explanation=f"Exact alias match: {alias['alias']}",
                        source='rules'
                    )
                    candidates.append(candidate)
                    logger.debug(f"Found alias match: {alias['alias']} -> {item['ku']}")
        
        return candidates
    
    async def _find_fuzzy_matches(self, parsed_line: ParsedLine, items: List[Dict]) -> List[MatchCandidate]:
        """Find fuzzy matches by name and specs"""
        candidates = []
        
        for item in items:
            if not item.get('is_active', True):
                continue
            
            # Calculate similarity score
            similarity = self._calculate_similarity(parsed_line, item)
            
            if similarity > 0.1:  # Minimum threshold
                candidate = MatchCandidate(
                    ku=item['ku'],
                    name=item['name'],
                    pack_qty=item.get('pack_qty'),
                    price=item.get('price'),
                    score=similarity,
                    explanation=f"Fuzzy match: {similarity:.2f} similarity",
                    source='rules'
                )
                candidates.append(candidate)
        
        return candidates
    
    def _calculate_similarity(self, parsed_line: ParsedLine, item: Dict) -> float:
        """Calculate similarity between parsed line and item"""
        score = 0.0
        name = (item.get('name', '') or '').lower()
        specs = item.get('specs_json', {})
        
        # Name similarity
        name_similarity = self._calculate_text_similarity(
            parsed_line.normalized_text.lower(), 
            name
        )
        score += name_similarity * 0.4
        
        # Specs similarity
        if specs:
            specs_similarity = self._calculate_specs_similarity(parsed_line, specs)
            score += specs_similarity * 0.6
        
        return min(score, 1.0)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using word overlap"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_specs_similarity(self, parsed_line: ParsedLine, specs: Dict) -> float:
        """Calculate similarity based on specs"""
        score = 0.0
        params = parsed_line.extracted_params or {}
        
        # Diameter match
        if 'diameter' in params and 'diameter' in specs:
            if (params.get('diameter', '') or '').lower() == (specs.get('diameter', '') or '').lower():
                score += self.weights['diameter_match']
        
        # Length match
        if 'length' in params and 'length' in specs:
            if params['length'] == specs['length']:
                score += self.weights['length_match']
        
        # Material match
        if 'material' in params and 'material' in specs:
            if (params.get('material', '') or '').lower() in (specs.get('material', '') or '').lower():
                score += self.weights['material_match']
        
        # Coating match
        if 'coating' in params and 'coating' in specs:
            if (params.get('coating', '') or '').lower() in (specs.get('coating', '') or '').lower():
                score += self.weights['coating_match']
        
        # Standard match
        if 'standard' in params and 'standard' in specs:
            if (params.get('standard', '') or '').lower() in (specs.get('standard', '') or '').lower():
                score += self.weights['standard_match']
        
        return score
    
    def _apply_type_filter(self, parsed_line: ParsedLine, candidates: List[MatchCandidate]) -> List[MatchCandidate]:
        """Apply type filter - remove candidates that don't match the required type"""
        if not parsed_line.extracted_params or 'type' not in parsed_line.extracted_params:
            return candidates
        
        required_type = (parsed_line.extracted_params.get('type', '') or '').lower()
        filtered_candidates = []
        
        for candidate in candidates:
            if self._matches_type(candidate.name, required_type):
                filtered_candidates.append(candidate)
            else:
                logger.debug(f"Filtered out {candidate.ku} - type mismatch")
        
        return filtered_candidates
    
    def _matches_type(self, item_name: str, required_type: str) -> bool:
        """Check if item name matches required type"""
        name_lower = (item_name or '').lower()
        
        for type_name, patterns in self.type_patterns.items():
            if any(pattern in required_type for pattern in patterns):
                return any(pattern in name_lower for pattern in patterns)
        
        return True  # If type not recognized, allow all
    
    def _calculate_score(self, parsed_line: ParsedLine, candidate: MatchCandidate) -> float:
        """Calculate final score for candidate"""
        score = 0.0
        
        # Base score from matching algorithm
        score += candidate.score * 0.7
        
        # Bonus for exact KU match
        if parsed_line.normalized_text.lower() == (candidate.ku or '').lower():
            score += self.weights['ku_match']
        
        # Bonus for exact alias match
        if candidate.source == 'rules' and 'Exact alias match' in candidate.explanation:
            score += self.weights['exact_alias']
        
        # Apply type filter penalty
        if not self._matches_type(candidate.name, parsed_line.normalized_text):
            score = 0.0
        
        return min(score, 1.0)
    
    def should_auto_accept(self, candidates: List[MatchCandidate]) -> Tuple[bool, Optional[MatchCandidate]]:
        """Check if best candidate should be auto-accepted"""
        if not candidates:
            return False, None
        
        best = candidates[0]
        
        # Check auto-accept threshold
        if best.score < 0.75:
            return False, None
        
        # Check gap to second best
        if len(candidates) > 1:
            gap = best.score - candidates[1].score
            if gap < 0.1:
                return False, None
        
        return True, best
    
    def get_candidates_for_gpt(self, candidates: List[MatchCandidate], limit: int = 5) -> List[MatchCandidate]:
        """Get top candidates for GPT validation"""
        return candidates[:limit]

# Global matching engine instance
_matching_engine = None

def get_matching_engine() -> MatchingEngine:
    """Get global matching engine instance"""
    global _matching_engine
    if _matching_engine is None:
        _matching_engine = MatchingEngine()
    return _matching_engine
