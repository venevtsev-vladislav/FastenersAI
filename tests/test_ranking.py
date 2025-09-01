"""
Unit тесты для сервиса ранжирования
"""

import pytest
from unittest.mock import Mock, patch
from core.services.ranking import RankingService, RankingTokens, MatchAnalysis


class TestRankingService:
    """Тесты для RankingService"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.service = RankingService()
    
    def test_normalize_string(self):
        """Тест нормализации строки"""
        assert self.service.normalize_string("М6×40") == "m6x40"
        assert self.service.normalize_string("DIN 933") == "din933"
        assert self.service.normalize_string("Оцинкованный") == "цинк"
        assert self.service.normalize_string("") == ""
        assert self.service.normalize_string(None) == ""
    
    def test_canonicalize_diameter(self):
        """Тест канонизации диаметра"""
        assert self.service.canonicalize_diameter("6 мм") == "6"
        assert self.service.canonicalize_diameter("M6") == "M6"
        assert self.service.canonicalize_diameter("М6") == "M6"
        assert self.service.canonicalize_diameter("") == ""
    
    def test_canonicalize_length(self):
        """Тест канонизации длины"""
        assert self.service.canonicalize_length("40 мм") == "40"
        assert self.service.canonicalize_length("90") == "90"
        assert self.service.canonicalize_length("") == ""
    
    def test_generate_mxl_variants(self):
        """Тест генерации вариантов размеров"""
        variants = self.service.generate_mxl_variants("M6", "40")
        expected = ["M6x40", "M6 x 40", "М6x40", "М6 x 40", "M6-40", "M6 - 40", "М6-40", "М6 - 40", "M640", "М640"]
        assert set(variants) == set(expected)
        
        # Тест для уголков
        angle_variants = self.service.generate_mxl_variants("50x50", "40")
        assert "50x50x40" in angle_variants
        assert "50х50х40" in angle_variants
    
    def test_extract_tokens(self):
        """Тест извлечения токенов"""
        user_intent = {
            'type': 'болт',
            'standard': 'DIN 933',
            'diameter': 'M6',
            'length': '40',
            'coating': 'оцинкованный'
        }
        
        tokens = self.service.extract_tokens("болт M6x40 DIN 933", user_intent)
        
        assert tokens.type_tok == 'болт'
        assert 'DIN933' in tokens.std_toks
        assert len(tokens.mxl_toks) > 0
        assert 'оцинкованный' in tokens.coat_toks
    
    def test_analyze_matches(self):
        """Тест анализа совпадений"""
        tokens = RankingTokens(
            type_tok='болт',
            std_toks=['DIN933'],
            mxl_toks=['M6x40'],
            coat_toks=['оцинкованный']
        )
        
        analysis = self.service.analyze_matches("Болт M6x40 DIN 933 оцинкованный", tokens)
        
        assert analysis.type_match is True
        assert analysis.standard_match is True
        assert analysis.size_match is True
        assert analysis.coating_match is True
        assert len(analysis.matched_tokens) > 0
        assert len(analysis.explanation) > 0
    
    def test_calculate_probability(self):
        """Тест расчета вероятности"""
        analysis = MatchAnalysis(
            type_match=True,
            standard_match=True,
            size_match=True,
            coating_match=False,
            matched_tokens=['болт', 'DIN933', 'M6x40'],
            explanation=['✅ Совпадение типа: болт', '✅ Совпадение стандарта: DIN933', '✅ Совпадение размеров: M6x40']
        )
        
        probability, explanation = self.service.calculate_probability(analysis)
        
        # Базовые очки: 25 + 40 + 30 = 95
        # Бонус за стандарт + размеры: +15
        # Бонус за тип + размеры: +10
        # Бонус за полное совпадение: +20
        # Итого: 95 + 15 + 10 + 20 = 140, но ограничено 100
        assert probability == 100
        assert "Итоговая вероятность: 100%" in explanation
    
    def test_get_match_reason(self):
        """Тест определения причины совпадения"""
        tokens = RankingTokens(
            type_tok='болт',
            std_toks=['DIN933'],
            mxl_toks=['M6x40'],
            coat_toks=['оцинкованный']
        )
        
        reason = self.service.get_match_reason("Болт M6x40 DIN 933", tokens)
        assert reason == 'Точное совпадение типа и размеров'
        
        reason = self.service.get_match_reason("Болт DIN 933", tokens)
        assert reason == 'Совпадение типа детали'
    
    def test_rank_results(self):
        """Тест ранжирования результатов"""
        results = [
            {'name': 'Болт M6x40 DIN 933', 'sku': 'B001'},
            {'name': 'Болт M6x40', 'sku': 'B002'},
            {'name': 'Болт DIN 933', 'sku': 'B003'}
        ]
        
        user_intent = {
            'type': 'болт',
            'standard': 'DIN 933',
            'diameter': 'M6',
            'length': '40'
        }
        
        ranked = self.service.rank_results(results, "болт M6x40 DIN 933", user_intent)
        
        assert len(ranked) == 3
        assert ranked[0]['sku'] == 'B001'  # Полное совпадение
        assert ranked[0]['probability_percent'] > ranked[1]['probability_percent']
        assert 'confidence_score' in ranked[0]
        assert 'match_reason' in ranked[0]
    
    def test_rank_results_empty(self):
        """Тест ранжирования пустых результатов"""
        ranked = self.service.rank_results([], "запрос", {})
        assert ranked == []
    
    def test_probability_limits(self):
        """Тест ограничений вероятности"""
        # Только покрытие - максимум 20%
        analysis = MatchAnalysis(
            type_match=False,
            standard_match=False,
            size_match=False,
            coating_match=True,
            matched_tokens=['оцинкованный'],
            explanation=['✅ Совпадение покрытия: оцинкованный']
        )
        
        probability, _ = self.service.calculate_probability(analysis)
        assert probability <= 20
        
        # Только тип без размеров и стандарта - максимум 40%
        analysis = MatchAnalysis(
            type_match=True,
            standard_match=False,
            size_match=False,
            coating_match=False,
            matched_tokens=['болт'],
            explanation=['✅ Совпадение типа: болт']
        )
        
        probability, _ = self.service.calculate_probability(analysis)
        assert probability <= 40


if __name__ == '__main__':
    pytest.main([__file__])
