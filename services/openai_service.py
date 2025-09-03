"""
Сервис для работы с OpenAI GPT
"""

import logging
import json
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL
from utils.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class OpenAIService:
    """Сервис для работы с OpenAI API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.model = OPENAI_MODEL
        self.assistant_id = "asst_HjGYPyU5L7uTWZA8q4mHUhGA"  # ID вашего ассистента
        self.prompt_loader = PromptLoader()
    
    async def analyze_user_intent(self, text: str) -> dict:
        """Анализирует намерение пользователя и извлекает параметры поиска"""
        try:
            # Загружаем системный промпт из JSON файла
            system_prompt = self.prompt_loader.get_system_prompt("assistant_prompt.json")
            
            user_prompt = f"""Проанализируй этот запрос и найди информацию о крепежных изделиях.

ВАЖНО: Если это большой текст (например, из PDF счета), найди только строки с товарами/позициями и проигнорируй реквизиты, адреса, итоги и другую служебную информацию.

Текст для анализа:
{text}

ИНСТРУКЦИЯ ПО ИЗВЛЕЧЕНИЮ:
1. Если это счет/накладная - найди строки типа "№ Артикул Товары Кол-во Ед. Цена Сумма"
2. Если это простой запрос - обработай весь текст
3. Игнорируй служебную информацию (реквизиты, адреса, итоги, подписи)
4. Извлекай только информацию о крепежных изделиях"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000  # Увеличиваем для сложных заказов
            )
            
            # Парсим ответ
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                logger.info(f"GPT анализ успешен: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"Не удалось распарсить JSON от GPT: {content}")
                # Возвращаем базовую структуру
                return {
                    "type": "неизвестно",
                    "diameter": None,
                    "length": None,
                    "material": None,
                    "coating": None,
                    "head_type": None,
                    "standard": None,
                    "quantity": None,
                    "additional_features": [],
                    "confidence": 0.5,
                    "raw_text": text
                }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе через GPT: {e}")
            return {
                "type": "неизвестно",
                "diameter": None,
                "length": None,
                "material": None,
                "coating": None,
                "head_type": None,
                "standard": None,
                "quantity": None,
                "additional_features": [],
                "confidence": 0.0,
                "raw_text": text,
                "error": str(e)
            }
    
    async def search_query_optimization(self, user_intent: dict) -> str:
        """Оптимизирует поисковый запрос на основе анализа GPT"""
        try:
            system_prompt = """
Ты - эксперт по поиску крепежных деталей. На основе анализа намерения пользователя создай оптимальный поисковый запрос для поиска в каталоге.

Учитывай:
- Основные характеристики (тип, размеры)
- Синонимы и альтернативные названия
- Приоритет важности параметров

Верни только поисковый запрос, без дополнительных комментариев.
"""
            
            user_prompt = f"Создай поисковый запрос для: {json.dumps(user_intent, ensure_ascii=False)}"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Оптимизированный запрос: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при оптимизации запроса: {e}")
            # Возвращаем базовый запрос
            return f"{user_intent.get('type', 'деталь')} {user_intent.get('diameter', '')} {user_intent.get('length', '')}"

    async def analyze_with_assistant(self, text: str) -> dict:
        """Анализирует намерение пользователя через ассистента с векторным хранилищем (Assistants API v2)."""
        try:
            logger.info(f"Анализ через ассистента с векторным хранилищем: {text[:100]}...")

            # Создаем thread (заголовок v2 задан на клиенте через default_headers)
            thread = await self.client.beta.threads.create()

            # Добавляем сообщение
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Проанализируй запрос крепежа и извлеки параметры:\n\n{text}"
            )

            # Запускаем ассистента
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )

            # Ждем завершения
            import asyncio
            while run.status in ['queued', 'in_progress']:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )

            if run.status == 'completed':
                # Получаем ответ
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )

                assistant_message = messages.data[0].content[0].text.value
                logger.info(f"Ответ ассистента: {assistant_message}")

                # Парсим JSON
                try:
                    result = json.loads(assistant_message)
                    logger.info(f"Ассистент анализ успешен: {result}")
                    return result
                except json.JSONDecodeError as json_error:
                    logger.error(f"Ошибка парсинга JSON от ассистента: {json_error}")
                    logger.error(f"Ответ ассистента: {assistant_message}")
                    return {'type': 'неизвестно', 'confidence': 0.1}
            else:
                logger.error(f"Ассистент завершился с ошибкой: {run.status}")
                return {'type': 'неизвестно', 'confidence': 0.1}

        except Exception as e:
            logger.error(f"Ошибка при работе с ассистентом: {e}")
            return {'type': 'неизвестно', 'confidence': 0.1}

