import json
import logging
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class AliasService:
    """Service for expanding search tokens using a simple alias dictionary.

    The service loads a small built-in dictionary of aliases (synonyms) for
    common fastener-related terms. Given a list of tokens it returns the
    original tokens plus any aliases found for them, helping to improve
    search results.
    """

    def __init__(self, alias_file: str | None = None) -> None:
        self.alias_map = self._load_aliases(alias_file)

    def _load_aliases(self, alias_file: str | None) -> Dict[str, List[str]]:
        """Load aliases from JSON file or use the built-in defaults."""
        if alias_file:
            path = Path(alias_file)
        else:
            path = Path(__file__).with_name("aliases.json")
        aliases: Dict[str, List[str]] = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                aliases = {
                    k.lower(): [v.lower() for v in values]
                    for k, values in data.items()
                    if isinstance(values, list)
                }
            except Exception as exc:
                logger.warning(f"Failed to load aliases from {path}: {exc}")
        else:
            # Minimal built-in mapping to keep the service functional
            aliases = {
                "шуруп": ["саморез", "винт"],
                "дюбель": ["анкер"],
                "гайка": ["nut"],
                "болт": ["винт"],
            }
        return aliases

    async def expand_tokens(self, tokens: List[str], original_text: str | None = None) -> List[str]:
        """Return unique tokens expanded with aliases."""
        if not tokens:
            return []

        original_text = (original_text or "").lower()
        result: Set[str] = set()

        for token in tokens:
            token_lower = token.lower()
            result.add(token_lower)

            # Check direct match in alias map
            if token_lower in self.alias_map:
                result.update(self.alias_map[token_lower])

            # Check if token matches any of the alias values
            for canon, variants in self.alias_map.items():
                if token_lower in variants:
                    result.add(canon)
                    result.update(variants)

            # Extra expansion: if any alias word appears in original text
            for canon, variants in self.alias_map.items():
                if canon in original_text or any(v in original_text for v in variants):
                    result.add(canon)
                    result.update(variants)

        return list(result)
