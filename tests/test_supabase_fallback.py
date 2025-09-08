import os
import sys
import pytest

# Ensure package root is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure required env variables for config
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test')
os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('SUPABASE_URL', 'http://localhost')
os.environ.setdefault('SUPABASE_KEY', 'test')

from pipeline.matching_engine import MatchingEngine
from pipeline.text_parser import ParsedLine
import asyncio


def test_supabase_search_fallback(monkeypatch):
    engine = MatchingEngine()
    parsed = ParsedLine(raw_text="болт м10", normalized_text="болт м10", extracted_params={})

    async def fake_search(query, intent):
        return [{
            'sku': 'TEST',
            'name': 'Болт М10',
            'pack_size': 1,
            'price': 1.0,
            'unit': 'шт',
            'probability_percent': 80,
            'match_reason': 'test'
        }]

    monkeypatch.setattr('pipeline.matching_engine.search_parts', fake_search)

    candidates = asyncio.run(engine.find_candidates(parsed, items=[], aliases=[]))
    assert candidates, "Supabase fallback should return candidates"
    assert candidates[0].ku == 'TEST'
