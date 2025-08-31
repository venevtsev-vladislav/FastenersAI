"""
Сервис для генерации вопросов уточнения через GPT
"""

import logging
from typing import Dict, List
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ClarificationService:
    """Сервис для генерации вопросов уточнения"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def generate_clarification_questions(self, user_query: str, low_confidence_results: List[Dict]) -> List[Dict]:
        """Генерирует вопросы для уточнения по результатам с низкой уверенностью"""
        try:
            if not low_confidence_results:
                return []
            
            questions = []
            
            for result in low_confidence_results:
                question = await self._generate_single_question(user_query, result)
                if question:
                    questions.append({
                        'result_sku': result.get('sku', ''),
                        'result_name': result.get('name', ''),
                        'confidence': result.get('confidence_score', 0),
                        'question': question,
                        'suggested_answers': await self._generate_suggested_answers(user_query, result)
                    })
            
            logger.info(f"Сгенерировано {len(questions)} вопросов для уточнения")
            return questions
            
        except Exception as e:
            logger.error(f"Ошибка при генерации вопросов уточнения: {e}")
            return []
    
    async def _generate_single_question(self, user_query: str, result: Dict) -> str:
        """Генерирует один вопрос для уточнения"""
        try:
            system_prompt = """
Ты - эксперт по крепежным деталям. Твоя задача - сгенерировать точный вопрос для уточнения запроса пользователя.

Пользователь ищет деталь, но найденный результат имеет низкую уверенность. Сгенерируй вопрос, который поможет уточнить:
- Какие именно характеристики важны
- Какие параметры можно изменить
- Какие альтернативы подойдут

Вопрос должен быть:
- Конкретным и понятным
- Направленным на уточнение параметров
- Предлагающим варианты выбора

Верни только вопрос, без дополнительного текста.
"""
            
            user_prompt = f"""
Запрос пользователя: "{user_query}"

Найденный результат (низкая уверенность):
- Название: {result.get('name', '')}
- SKU: {result.get('sku', '')}
- Уверенность: {result.get('confidence_score', 0)}%

Сгенерируй вопрос для уточнения:
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            question = response.choices[0].message.content.strip()
            return question
            
        except Exception as e:
            logger.error(f"Ошибка при генерации вопроса: {e}")
            return self._generate_fallback_question(user_query, result)
    
    async def _generate_suggested_answers(self, user_query: str, result: Dict) -> List[str]:
        """Генерирует предлагаемые ответы на вопрос уточнения"""
        try:
            system_prompt = """
Ты - эксперт по крепежным деталям. Сгенерируй 3-4 варианта ответа на вопрос уточнения.

Варианты должны быть:
- Конкретными и полезными
- Покрывать разные аспекты запроса
- Помогать уточнить параметры

Верни варианты в формате списка, каждый с новой строки.
"""
            
            user_prompt = f"""
Запрос пользователя: "{user_query}"
Найденный результат: {result.get('name', '')}

Сгенерируй варианты ответов для уточнения параметров:
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            # Разбиваем на варианты
            answers = [line.strip() for line in content.split('\n') if line.strip()]
            return answers[:4]  # Максимум 4 варианта
            
        except Exception as e:
            logger.error(f"Ошибка при генерации вариантов ответов: {e}")
            return ["Да, это то что нужно", "Нет, нужны другие параметры", "Можете уточнить размеры"]
    
    def _generate_fallback_question(self, user_query: str, result: Dict) -> str:
        """Fallback генерация вопроса без GPT"""
        name = result.get('name', '')
        
        if 'болт' in user_query.lower() and 'болт' not in name.lower():
            return "Вы ищете именно болт? Или подойдет винт или саморез?"
        elif 'размер' in user_query.lower():
            return "Какие точные размеры вам нужны? Диаметр и длина?"
        elif 'материал' in user_query.lower():
            return "Какой материал предпочтителен? Сталь, нержавейка, латунь?"
        else:
            return "Можете уточнить, какие именно характеристики важны для вас?"
    
    def filter_low_confidence_results(self, search_results: List[Dict], threshold: int = 90) -> List[Dict]:
        """Фильтрует результаты с низкой уверенностью"""
        return [result for result in search_results if result.get('confidence_score', 100) < threshold]
