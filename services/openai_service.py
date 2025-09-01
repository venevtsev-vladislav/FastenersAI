"""
Сервис для работы с OpenAI GPT
"""

import logging
import json
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL

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
    
    async def analyze_user_intent(self, text: str) -> dict:
        """Анализирует намерение пользователя и извлекает параметры поиска"""
        try:
            system_prompt = """Ты — эксперт по крепежным деталям. Твоя задача: по пользовательскому запросу ИДЕНТИФИЦИРОВАТЬ и НОРМАЛИЗОВАТЬ параметры крепежа и выдать ТОЛЬКО валидный JSON без пояснений, без Markdown и без дополнительного текста.

ОБЩИЕ ПРАВИЛА ВЫВОДА:
- Всегда отвечай ровно одним JSON-объектом или массивом объектов (если в запросе явно несколько позиций).
- Используй поля из схемы ниже. Поля, которые невозможно определить уверенно, опускай или ставь null. Ничего не выдумывай, но допускай аккуратные выводы по сленгу/шаблонам (с понижением confidence).
- Единицы длины по умолчанию — мм, если явно не указано иное. Диаметр метрика — формат "M6", "M10" и т.п.
- Размеры распознавай из форматов: "М6 на 40", "М6х40", "M6x40", "M6×40", "на 40", а также с пробелами/разными "x/×/х".
- Количество распознавай как число + единица ("шт", "штук", "тыс.шт"). Если указано "N тыс.шт" — количество = N*1000 шт. Если указано только "тыс.шт" без числа — трактуй как 1000 шт. Если количество не упомянуто — не выводи поле quantity.
- Покрытие и материал НЕ путать: например, "оцинкованный" — это coating="цинк", а не материал. "нержавейка" — это материал="нержавеющая сталь".
- Стандарт ищи по явным "DIN/ISO/ГОСТ/EN" или выводи по устойчивым соответствиям типа/подтипа (см. ниже). Если уверенности нет — не заполняй standard.
- confidence в диапазоне [0,1]: высокая (≥0.9), если найдены согласованные тип/подтип + размеры и стандарт; средняя (~0.7), если без стандарта, но размеры/покрытие ясны; низкая (≤0.5), если только частичные намёки.

НОРМАЛИЗАЦИЯ СЛЕНГА/ЖАРГОНА → ТЕХНИЧЕСКИЕ ТЕРМИНЫ:
1) Тип детали и подтип:
   - "болт с грибком", "болт-грибок", "грибок" → type="болт", subtype="грибовидная головка" (обычно DIN 603)
   - "болт под ключ", "болт шестигранник", "шестигранный болт" → type="болт", subtype="шестигранная головка" (DIN 933 — полная резьба; DIN 931 — частичная, если явно сказано)
   - "саморез клоп", "клоп" → type="саморез", subtype="с прессшайбой"
   - "саморез для ГКЛ", "саморез для гипсокартона", "саморез для крепления ГКЛ к дереву" → type="саморез", subtype="для гипсокартона"
   - "саморез по дереву" → type="саморез", subtype="по дереву"
   - "саморез по металлу" → type="саморез", subtype="по металлу"
   - "анкер забиваемый" → type="анкер", subtype="забиваемый"
2) Материал (примерные соответствия): "нерж", "нержавейка" → "нержавеющая сталь"; "латунь" → "латунь"; "алюминий" → "алюминий"; "сталь", "металл" → "сталь".
3) Покрытие: "цинкованный/оцинкованный" → coating="цинк". "нержавейка" — это материал, НЕ покрытие.
4) Класс прочности: извлекай A2, A4, 8.8, 10.9, 12.9 и т.п.
5) Размеры: "М6 на 40" → diameter="M6", length="40 мм"; "М6х40" → diameter="M6", length="40 мм"; "на 40" → length="40 мм".
6) ТОЧНЫЕ РАЗМЕРЫ: Если в тексте есть точные размеры типа "50х50х35", "100х100х80" - сохраняй их как diameter="50х50", length="35 мм". НЕ упрощай размеры!
7) РАЗМЕРЫ УГОЛКОВ: "50х50х35" → diameter="50х50", length="35 мм"; "100х100х80" → diameter="100х100", length="80 мм".
8) ТОЧНЫЕ НАЗВАНИЯ: Если в тексте есть точные названия типа "ОЦ. Крепежный уголок", "равносторонний уголок" - сохраняй их в subtype.

ИНФЕРЕНС СТАНДАРТА ПО ТИПУ/ПОДТИПУ (если явно не указано, но тип однозначен):
- Болт с грибовидной головкой → DIN 603.
- Болт шестигранная головка: если явно "полная резьба" → DIN 933; если явно "частичная резьба" → DIN 931; иначе standard не указывать.
(Другие соответствия добавляй только если в запросе присутствуют прямые признаки/номера стандарта.)

СХЕМА ВЫВОДА (для каждой позиции):
{
  "type": string,                    // напр. "болт", "саморез", "анкер"
  "subtype": string|null,            // напр. "грибовидная головка", "шестигранная головка"
  "standard": string|null,           // напр. "DIN 603", "DIN 933", "ISO 7380-1", "ГОСТ …"
  "diameter": string|null,           // напр. "M6", "3.5 мм"
  "length": string|null,             // в мм по умолчанию, напр. "40 мм"
  "material": string|null,           // "сталь", "нержавейшая сталь", "латунь"…
  "coating": string|null,            // "цинк", "черный оксид", и т.п. (если есть)
  "grade": string|null,              // A2, A4, 8.8, 10.9, 12.9 и т.д.
  "quantity": string|null,           // напр. "100 шт", "2 тыс.шт", "1000 шт"
  "additional_features": [string],   // нормализованные особенности (напр. "грибовидная головка", "с прессшайбой")
  "confidence": number               // 0..1
}

ЕСЛИ В ЗАПРОСЕ ОДНА ДЕТАЛЬ — верни один объект по схеме. Если несколько — верни массив таких объектов.

ПРИМЕРЫ НОРМАЛИЗАЦИИ (пример ответа — только JSON без комментариев):
1) Запрос: "болт с грибком М6 на 40, цинкованный"
→ {
  "type": "болт",
  "subtype": "грибовидная головка",
  "standard": "DIN 603",
  "diameter": "M6",
  "length": "40 мм",
  "material": null,
  "coating": "цинк",
  "grade": null,
  "quantity": null,
  "additional_features": ["грибовидная головка"],
  "confidence": 0.92
}
2) Запрос: "саморез клоп 3.5х25"
→ {
  "type": "саморез",
  "subtype": "с прессшайбой",
  "standard": null,
  "diameter": "3.5 мм",
  "length": "25 мм",
  "material": null,
  "coating": null,
  "grade": null,
  "quantity": null,
  "additional_features": ["с прессшайбой"],
  "confidence": 0.8
}
3) Запрос: "болт под ключ М10х30, оцинкованный 10.9, 200 шт"
→ {
  "type": "болт",
  "subtype": "шестигранная головка",
  "standard": null,
  "diameter": "M10",
  "length": "30 мм",
  "material": "сталь",
  "coating": "цинк",
  "grade": "10.9",
  "quantity": "200 шт",
  "additional_features": ["шестигранная головка"],
  "confidence": 0.85
}
4) Запрос: "50х50х35 ОЦ. Крепежный уголок (100 шт)"
→ {
  "type": "уголок",
  "subtype": "ОЦ. Крепежный уголок",
  "standard": null,
  "diameter": "50х50",
  "length": "35 мм",
  "material": null,
  "coating": "цинк",
  "grade": null,
  "quantity": "100 шт",
  "additional_features": ["крепежный"],
  "confidence": 0.95
}
5) Запрос из счета: "1 AJJ005035233099 50х50х35 ОЦ. Крепежный уголок (100 шт) 10упак 498,00 1 000 4,98 4 980,00"
→ {
  "type": "уголок",
  "subtype": "ОЦ. Крепежный уголок",
  "standard": null,
  "diameter": "50х50",
  "length": "35 мм",
  "material": null,
  "coating": "цинк",
  "grade": null,
  "quantity": "1000 шт",
  "additional_features": ["крепежный"],
    "confidence": 0.95
}
6) Запрос: "Саморез для крепления ГКЛ к дереву 4,2х 90 (2000шт.)"
→ {
  "type": "саморез",
  "subtype": "для гипсокартона",
  "standard": null,
  "diameter": "4.2 мм",
  "length": "90 мм",
  "material": "сталь",
  "coating": null,
  "grade": null,
  "quantity": "2000 шт",
  "additional_features": ["для гипсокартона", "по дереву"],
  "confidence": 0.9
}

СТРОГО: выводи только JSON (объект или массив). Никаких пояснений, текста или Markdown. Если данных недостаточно — заполни, что возможно, остальное опусти или поставь null и понизь confidence."""
            
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

