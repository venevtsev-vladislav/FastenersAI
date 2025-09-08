"""
GPT validation service for uncertain matches
Based on the comprehensive specification
"""

import logging
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pipeline.matching_engine import MatchCandidate
from pipeline.text_parser import ParsedLine
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

@dataclass
class GPTValidationResult:
    """GPT validation result"""
    decision: str  # KU or 'unsure'
    confidence: float  # 0..1
    reason: str
    chosen_ku: Optional[str] = None

class GPTValidator:
    """GPT validation service for uncertain matches"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        self.accept_confidence_threshold = 0.8
    
    async def validate_candidates(self, parsed_line: ParsedLine, 
                                candidates: List[MatchCandidate]) -> GPTValidationResult:
        """Validate candidates using GPT"""
        try:
            if not candidates:
                return GPTValidationResult(
                    decision='unsure',
                    confidence=0.0,
                    reason='No candidates provided'
                )

            logger.info(
                f"Sending line '{parsed_line.raw_text}' with {len(candidates)} candidates to GPT"
            )

            # Prepare prompt
            prompt = self._build_validation_prompt(parsed_line, candidates)

            # Call GPT
            response = await self.openai_service.call_gpt(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse response
            result = self._parse_gpt_response(response)
            
            logger.info(f"GPT validation result: {result.decision} (confidence: {result.confidence})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in GPT validation: {e}")
            return GPTValidationResult(
                decision='unsure',
                confidence=0.0,
                reason=f'Error: {str(e)}'
            )
    
    def _build_validation_prompt(self, parsed_line: ParsedLine, 
                               candidates: List[MatchCandidate]) -> str:
        """Build validation prompt for GPT"""
        
        # Format candidates for prompt
        candidates_text = []
        for i, candidate in enumerate(candidates, 1):
            candidate_info = f"{i}. KU: {candidate.ku}\n"
            candidate_info += f"   Name: {candidate.name}\n"
            candidate_info += f"   Pack Qty: {candidate.pack_qty or 'N/A'}\n"
            candidate_info += f"   Price: {candidate.price or 'N/A'}\n"
            candidate_info += f"   Score: {candidate.score:.3f}\n"
            candidate_info += f"   Source: {candidate.source}\n"
            candidates_text.append(candidate_info)
        
        candidates_str = "\n".join(candidates_text)
        
        prompt = f"""
Вы - эксперт по крепежным изделиям. Вам нужно выбрать наиболее подходящий вариант из списка кандидатов для запроса пользователя.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{parsed_line.raw_text}

НОРМАЛИЗОВАННЫЙ ЗАПРОС:
{parsed_line.normalized_text}

ИЗВЛЕЧЕННЫЕ ПАРАМЕТРЫ:
{json.dumps(parsed_line.extracted_params or {}, ensure_ascii=False, indent=2)}

КАНДИДАТЫ:
{candidates_str}

ИНСТРУКЦИИ:
1. Внимательно проанализируйте запрос пользователя и каждый кандидат
2. Учитывайте тип изделия (болт/винт/анкер/гайка и т.д.)
3. Учитывайте диаметр и длину
4. Учитывайте материал и покрытие
5. Учитывайте стандарты (DIN, ГОСТ, ISO)
6. Учитывайте специальные признаки (с крюком, с насечками, класс прочности и т.д.)
7. НЕ придумывайте значения, которых нет в данных

ОТВЕТ ДОЛЖЕН БЫТЬ В ФОРМАТЕ JSON:
{{
    "decision": "<KU_код_выбранного_кандидата_или_unsure>",
    "confidence": <число_от_0_до_1>,
    "reason": "Объяснение выбора"
}}

Если ни один кандидат не подходит достаточно хорошо, используйте "unsure" в качестве решения.
"""
        
        return prompt
    
    def _parse_gpt_response(self, response: str) -> GPTValidationResult:
        """Parse GPT response"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            decision = data.get('decision', 'unsure')
            confidence = float(data.get('confidence', 0.0))
            reason = data.get('reason', 'No reason provided')
            
            # Validate confidence range
            confidence = max(0.0, min(1.0, confidence))
            
            # Extract chosen KU if decision is not 'unsure'
            chosen_ku = None
            if decision != 'unsure':
                chosen_ku = decision
            
            return GPTValidationResult(
                decision=decision,
                confidence=confidence,
                reason=reason,
                chosen_ku=chosen_ku
            )
            
        except Exception as e:
            logger.error(f"Error parsing GPT response: {e}")
            logger.error(f"Response was: {response}")
            
            return GPTValidationResult(
                decision='unsure',
                confidence=0.0,
                reason=f'Failed to parse response: {str(e)}'
            )
    
    def should_accept_gpt_decision(self, result: GPTValidationResult) -> bool:
        """Check if GPT decision should be accepted"""
        return (result.decision != 'unsure' and 
                result.confidence >= self.accept_confidence_threshold)
    
    async def validate_single_line(self, parsed_line: ParsedLine, 
                                 candidates: List[MatchCandidate]) -> Tuple[Optional[str], str, str]:
        """Validate single line and return result"""
        result = await self.validate_candidates(parsed_line, candidates)
        
        if self.should_accept_gpt_decision(result):
            return result.chosen_ku, 'ok', 'gpt'
        else:
            return None, 'needs_review', 'gpt'

# Global GPT validator instance
_gpt_validator = None

def get_gpt_validator() -> GPTValidator:
    """Get global GPT validator instance"""
    global _gpt_validator
    if _gpt_validator is None:
        _gpt_validator = GPTValidator()
    return _gpt_validator
