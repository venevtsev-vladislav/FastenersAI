"""
Text parsing and normalization pipeline
Based on the comprehensive specification
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedLine:
    """Parsed line data structure"""
    raw_text: str
    normalized_text: str
    qty_packs: Optional[float] = None
    qty_units: Optional[float] = None
    extracted_params: Dict[str, str] = None

class TextNormalizer:
    """Text normalization according to specification rules"""
    
    def __init__(self):
        # Size normalization patterns
        self.size_patterns = [
            (r'(\d+)\s*[xх×*]\s*(\d+)', r'\1x\2'),  # M10x120, M10х120, M10*120 -> M10x120
            (r'М(\d+)\s*[xх×*]\s*(\d+)', r'M\1x\2'),  # М10x120 -> M10x120
            (r'(\d+)\s*[xх×*]\s*(\d+)\s*мм', r'\1x\2'),  # 10x120мм -> 10x120
        ]
        
        # Material/coating normalization
        self.material_synonyms = {
            'оцинкованный': ['оцинк', 'цинк', 'zn', 'цинковый'],
            'латунный': ['латунь', 'brass'],
            'нержавеющий': ['нержавейка', 'stainless', 'inox'],
            'стальной': ['сталь', 'steel'],
        }
        
        # Type synonyms
        self.type_synonyms = {
            'анкер клиновой': ['клиновой анкер', 'анкер-клиновой'],
            'анкер забиваемый': ['забиваемый анкер', 'анкер-забиваемый'],
            'анкерный болт': ['болт анкерный', 'анкер-болт'],
            'болт din': ['din болт', 'болт по din'],
            'винт din': ['din винт', 'винт по din'],
        }
        
        # Quantity extraction patterns
        self.qty_patterns = [
            r'(\d+)\s*шт',
            r'(\d+)\s*уп',
            r'(\d+)\s*штук',
            r'(\d+)\s*упаковок',
            r'(\d+)\s*шт\.',
            r'(\d+)\s*уп\.',
        ]
    
    def normalize_text(self, text: str) -> str:
        """Normalize text according to specification rules"""
        if not text:
            return ""
        
        normalized = text.strip()
        
        # Apply size normalization
        for pattern, replacement in self.size_patterns:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # Normalize materials/coatings
        normalized = self._normalize_materials(normalized)
        
        # Normalize types
        normalized = self._normalize_types(normalized)
        
        # Clean up extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_materials(self, text: str) -> str:
        """Normalize material and coating terms"""
        text_lower = text.lower()
        
        for standard, variants in self.material_synonyms.items():
            for variant in variants:
                if variant in text_lower:
                    text = re.sub(re.escape(variant), standard, text, flags=re.IGNORECASE)
                    break
        
        return text
    
    def _normalize_types(self, text: str) -> str:
        """Normalize fastener type terms"""
        text_lower = text.lower()
        
        for standard, variants in self.type_synonyms.items():
            for variant in variants:
                if variant in text_lower:
                    text = re.sub(re.escape(variant), standard, text, flags=re.IGNORECASE)
                    break
        
        return text
    
    def extract_quantity(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract quantity from text"""
        for pattern in self.qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                qty = float(match.group(1))
                unit = 'шт' if 'шт' in match.group(0).lower() else 'уп'
                return qty, unit
        
        return None, None
    
    def extract_parameters(self, text: str) -> Dict[str, str]:
        """Extract parameters from text"""
        params = {}
        
        # Extract diameter
        diameter_match = re.search(r'[МM](\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if diameter_match:
            params['diameter'] = f"M{diameter_match.group(1)}"
        
        # Extract length
        length_match = re.search(r'[МM]\d+(?:\.\d+)?[xх×*](\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if length_match:
            params['length'] = length_match.group(1)
        
        # Extract strength class
        strength_match = re.search(r'кл\.пр\.(\d+\.\d+)', text, re.IGNORECASE)
        if strength_match:
            params['strength_class'] = strength_match.group(1)
        
        # Extract standard
        din_match = re.search(r'DIN\s*(\d+)', text, re.IGNORECASE)
        if din_match:
            params['standard'] = f"DIN {din_match.group(1)}"
        
        # Extract coating
        coating_match = re.search(r'(оцинк|цинк|латун|нержавеющий)', text, re.IGNORECASE)
        if coating_match:
            coating = coating_match.group(1).lower()
            if coating in ['оцинк', 'цинк']:
                params['coating'] = 'оцинкованный'
            elif coating == 'латун':
                params['coating'] = 'латунный'
            elif coating == 'нержавеющий':
                params['coating'] = 'нержавеющий'
        
        return params

class TextParser:
    """Main text parser for different input types"""
    
    def __init__(self):
        self.normalizer = TextNormalizer()
    
    def parse_text_input(self, text: str) -> List[ParsedLine]:
        """Parse text input into individual lines"""
        if not text:
            return []
        
        # Split by common delimiters (comma removed to keep numbers like "4,0" intact)
        lines = re.split(r'[\n;\t]+', text)
        
        parsed_lines = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            # Normalize the line
            normalized = self.normalizer.normalize_text(line)
            
            # Extract quantity
            qty, unit = self.normalizer.extract_quantity(line)
            
            # Extract parameters
            params = self.normalizer.extract_parameters(normalized)
            
            # Calculate qty_units if we have qty_packs and pack_qty
            qty_units = None
            if qty and unit == 'шт':
                qty_units = qty
            elif qty and unit == 'уп':
                qty_packs = qty
            else:
                qty_packs = None
            
            parsed_line = ParsedLine(
                raw_text=line,
                normalized_text=normalized,
                qty_packs=qty_packs,
                qty_units=qty_units,
                extracted_params=params
            )
            
            parsed_lines.append(parsed_line)
            logger.debug(f"Parsed line {i}: {line} -> {normalized}")
        
        return parsed_lines
    
    def parse_excel_input(self, excel_data: List[List[str]]) -> List[ParsedLine]:
        """Parse Excel input data"""
        parsed_lines = []
        
        for i, row in enumerate(excel_data, 1):
            if not row or not any(cell for cell in row):
                continue
            
            # Join all non-empty cells into a single text
            line_text = ' '.join(str(cell).strip() for cell in row if cell)
            if not line_text:
                continue
            
            # Parse as text
            line_parsed = self.parse_text_input(line_text)
            if line_parsed:
                # Update line number to match Excel row
                line_parsed[0].raw_text = f"Row {i}: {line_parsed[0].raw_text}"
                parsed_lines.extend(line_parsed)
        
        return parsed_lines
    
    def parse_voice_input(self, transcript: str) -> List[ParsedLine]:
        """Parse voice input transcript"""
        # Voice input is treated as text after transcription
        return self.parse_text_input(transcript)
    
    def parse_image_input(self, ocr_text: str) -> List[ParsedLine]:
        """Parse OCR text from image"""
        # OCR text is treated as text after processing
        return self.parse_text_input(ocr_text)

# Global parser instance
_text_parser = None

def get_text_parser() -> TextParser:
    """Get global text parser instance"""
    global _text_parser
    if _text_parser is None:
        _text_parser = TextParser()
    return _text_parser
