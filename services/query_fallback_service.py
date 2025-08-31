"""
Сервис для умной обработки неудачных запросов
Если простой парсер не справился - обращаемся к ИИ для уточнения
"""

import logging
from typing import Dict, Any, Optional, List
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class QueryFallbackService:
    """Сервис для обработки неудачных запросов через ИИ"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def process_failed_query(
        self, 
        original_query: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Обрабатывает неудачный запрос через ИИ
        
        Args:
            original_query: Исходный запрос пользователя
            search_results: Результаты поиска (пустые или неудачные)
            
        Returns:
            Dict: Результат обработки с нормализованным запросом или ошибкой
        """
        try:
            logger.info(f"🔄 Обрабатываю неудачный запрос через ИИ: {original_query}")
            
            # Анализируем запрос через ИИ
            ai_analysis = await self._analyze_query_with_ai(original_query)
            
            if ai_analysis.get('can_normalize'):
                # ИИ смог нормализовать запрос
                normalized_query = ai_analysis['normalized_query']
                logger.info(f"✅ ИИ нормализовал запрос: {original_query} -> {normalized_query}")
                
                return {
                    'success': True,
                    'can_normalize': True,
                    'original_query': original_query,
                    'normalized_query': normalized_query,
                    'ai_suggestions': ai_analysis.get('suggestions', []),
                    'reason': 'ИИ успешно нормализовал запрос'
                }
            else:
                # ИИ не смог нормализовать запрос
                logger.warning(f"❌ ИИ не смог нормализовать запрос: {original_query}")
                
                return {
                    'success': False,
                    'can_normalize': False,
                    'original_query': original_query,
                    'ai_feedback': ai_analysis.get('feedback', ''),
                    'reason': 'ИИ не смог нормализовать запрос'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке неудачного запроса: {e}")
            return {
                'success': False,
                'can_normalize': False,
                'original_query': original_query,
                'error': str(e),
                'reason': 'Ошибка обработки запроса'
            }
    
    async def _analyze_query_with_ai(self, query: str) -> Dict[str, Any]:
        """Анализирует запрос через ИИ для нормализации"""
        try:
            prompt = f"""
Ты - эксперт по крепежным деталям. Пользователь отправил запрос, который не удалось разобрать автоматически.

ИСХОДНЫЙ ЗАПРОС: {query}

ТВОЯ ЗАДАЧА:
1. Проанализируй, что хочет пользователь
2. Попробуй нормализовать запрос в стандартный формат
3. Если не можешь - объясни, что именно неясно

ВОЗМОЖНЫЕ СЦЕНАРИИ:

**СЦЕНАРИЙ 1: Можете нормализовать**
- Определите тип детали, размеры, материал, покрытие
- Предложите стандартную формулировку
- Дайте рекомендации по улучшению запроса

**СЦЕНАРИЙ 2: Не можете нормализовать**
- Укажите, что именно неясно
- Предложите альтернативные формулировки
- Объясните, какие параметры нужны

ФОРМАТ ОТВЕТА:
{{
    "can_normalize": true/false,
    "normalized_query": "стандартная формулировка или null",
    "suggestions": ["рекомендации по улучшению"],
    "feedback": "объяснение почему не удалось нормализовать",
    "confidence": 0.95
}}

Будь конкретным и полезным!
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по крепежным деталям. Помогаешь нормализовать запросы пользователей."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Парсим JSON ответ
            try:
                import json
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)
                    return result
                else:
                    # Fallback: анализируем текстовый ответ
                    return self._parse_text_response(ai_response)
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON ответ: {e}")
                return self._parse_text_response(ai_response)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе запроса через ИИ: {e}")
            return {
                'can_normalize': False,
                'feedback': f'Ошибка анализа: {str(e)}',
                'confidence': 0.0
            }
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Парсит текстовый ответ ИИ"""
        response_lower = response.lower()
        
        # Пытаемся понять, смог ли ИИ нормализовать
        if any(word in response_lower for word in ['винт', 'болт', 'гайка', 'шайба', 'саморез']):
            can_normalize = True
            normalized_query = response
        else:
            can_normalize = False
            normalized_query = None
        
        return {
            'can_normalize': can_normalize,
            'normalized_query': normalized_query,
            'feedback': response,
            'confidence': 0.7 if can_normalize else 0.3
        }
    
    def get_user_friendly_message(self, fallback_result: Dict[str, Any]) -> str:
        """Формирует понятное сообщение для пользователя"""
        if fallback_result.get('can_normalize'):
            return (
                f"🤔 Ваш запрос был не совсем понятен, но я попробовал его разобрать:\n\n"
                f"📝 **Исходный запрос:** {fallback_result['original_query']}\n"
                f"✅ **Нормализованный запрос:** {fallback_result['normalized_query']}\n\n"
                f"🔄 Попробуйте использовать нормализованную формулировку для лучших результатов!"
            )
        else:
            return (
                f"😔 К сожалению, не удалось разобрать ваш запрос:\n\n"
                f"📝 **Запрос:** {fallback_result['original_query']}\n\n"
                f"💡 **Рекомендации:**\n"
                f"• Укажите тип детали (винт, болт, гайка, шайба)\n"
                f"• Укажите размеры (M6, 6 мм, длина)\n"
                f"• Укажите материал/покрытие (сталь, цинк, нержавеющая)\n"
                f"• Укажите стандарт (DIN, ISO, ГОСТ)\n\n"
                f"🔄 Попробуйте переформулировать запрос более конкретно!"
            )
