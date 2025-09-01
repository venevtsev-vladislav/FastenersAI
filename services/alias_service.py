"""
Сервис для работы со справочником синонимов (aliases)
Берет данные из таблицы Supabase `aliases` и кэширует их в памяти,
чтобы расширять поисковые запросы устойчивыми синонимами.
"""

import logging
import time
from typing import Dict, List

from database.supabase_client import get_aliases

logger = logging.getLogger(__name__)


class AliasService:
    """Загружает и кэширует синонимы, предоставляет методы расширения токенов."""

    def __init__(self, ttl_seconds: int = 600):
        self._alias_to_tokens: Dict[str, List[str]] = {}
        self._last_loaded_at: float = 0.0
        self._ttl_seconds = ttl_seconds

    async def _ensure_loaded(self) -> None:
        now = time.time()
        if self._alias_to_tokens and (now - self._last_loaded_at) < self._ttl_seconds:
            return

        try:
            rows = await get_aliases()
            mapping: Dict[str, List[str]] = {}
            for row in rows:
                alias = (row.get('alias') or '').strip().lower()
                maps_to = row.get('maps_to') or []
                if not alias:
                    continue
                # maps_to может быть строкой или массивом строк
                if isinstance(maps_to, str):
                    tokens = [maps_to]
                elif isinstance(maps_to, list):
                    tokens = [str(x) for x in maps_to]
                else:
                    tokens = []
                mapping[alias] = [t.strip() for t in tokens if str(t).strip()]

            self._alias_to_tokens = mapping
            self._last_loaded_at = now
            logger.info(f"AliasService: загружено {len(self._alias_to_tokens)} синонимов")
        except Exception as e:
            logger.warning(f"AliasService: не удалось загрузить синонимы: {e}")

    async def expand_tokens(self, tokens: List[str], original_text: str = "") -> List[str]:
        """Возвращает список токенов с расширениями по справочнику.
        - для каждого токена добавляет соответствующие maps_to
        - также сканирует original_text на предмет наличия алиасов (фраз)
        """
        await self._ensure_loaded()

        expanded: List[str] = []
        seen = set()

        def add(tok: str):
            t = (tok or '').strip()
            if not t:
                return
            if t.lower() in seen:
                return
            seen.add(t.lower())
            expanded.append(t)

        original_lower = (original_text or '').lower()

        # Сначала добавляем исходные токены и их карты
        for tok in tokens:
            add(tok)
            mapped = self._alias_to_tokens.get(tok.lower())
            if mapped:
                for m in mapped:
                    add(m)

        # Затем добавляем алиасы, встречающиеся в исходном тексте, как отдельные расширения
        for alias, mapped in self._alias_to_tokens.items():
            if alias and alias in original_lower:
                for m in mapped:
                    add(m)

        return expanded


