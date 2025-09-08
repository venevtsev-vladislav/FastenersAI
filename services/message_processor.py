"""
Сервис для обработки различных типов сообщений
"""

import logging
import asyncio
import re
from telegram import Message
from services.openai_service import OpenAIService
from services.media_processor import MediaProcessor
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class MessageProcessor:
    """Класс для обработки различных типов сообщений"""
    
    def __init__(self, bot=None):
        self.openai_service = OpenAIService()
        self.media_processor = MediaProcessor()
        self.bot = bot
    
    async def process_message(self, message: Message) -> dict:
        """Обрабатывает сообщение и возвращает структурированный результат"""
        try:
            # Определяем тип сообщения
            if message.text:
                return await self._process_text_message(message)
            elif message.voice:
                return await self._process_voice_message(message)
            elif message.audio:
                return await self._process_audio_message(message)
            elif message.photo:
                return await self._process_photo_message(message)
            elif message.document:
                return await self._process_document_message(message)
            else:
                logger.warning(f"Неизвестный тип сообщения: {message}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            return None
    
    async def _process_text_message(self, message: Message) -> dict:
        """Обрабатывает текстовое сообщение"""
        text = message.text.strip()
        
        # Умный анализ намерения пользователя (встроенный SmartParser)
        try:
            # Определяем нужен ли GPT
            need_gpt, reason, basic_intent = self._analyze_query_complexity(text)
            
            if need_gpt:
                logger.info(f"🔍 Встроенный SmartParser: ИИ ассистент необходим для: {reason}")
                # Используем ассистента с векторным хранилищем для сложных запросов
                assistant_result = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Ассистент анализ успешен: {assistant_result}")
                
                # Обрабатываем результат ассистента
                if isinstance(assistant_result, dict) and 'items' in assistant_result:
                    # Если это массив items, обрабатываем как множественный заказ
                    if assistant_result['items'] and len(assistant_result['items']) > 0:
                        user_intent = {
                            'is_multiple_order': True,
                            'items': assistant_result['items']
                        }
                    else:
                        user_intent = {}
                else:
                    # Если это один объект
                    user_intent = assistant_result
            else:
                logger.info(f"🔍 Встроенный SmartParser: GPT НЕ нужен: {reason}")
                # Используем базовый user_intent
                user_intent = basic_intent
            
            # Если не удалось распознать, создаем базовый user_intent
            if not user_intent or user_intent.get('type') == 'неизвестно':
                logger.info("🔍 Не удалось распознать, создаем базовый user_intent")
                user_intent = self._create_basic_user_intent(text)
            # Нормализуем формат: если пришел список позиций, оборачиваем в объект множественного заказа
            if isinstance(user_intent, list):
                user_intent = { 'is_multiple_order': True, 'items': user_intent }
            
            return {
                'type': 'text',
                'original_content': text,
                'processed_text': text,
                'user_intent': user_intent
            }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе через SmartParser: {e}")
            # Fallback: используем ассистента, затем базовый разбор при неудаче
            try:
                assistant_result = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Fallback ассистент анализ успешен: {assistant_result}")
                if not assistant_result or (isinstance(assistant_result, dict) and assistant_result.get('type') == 'неизвестно'):
                    user_intent = self._create_basic_user_intent(text)
                else:
                    # Обрабатываем результат ассистента (может быть массив items или один объект)
                    if isinstance(assistant_result, dict) and 'items' in assistant_result:
                        # Если это массив items, обрабатываем как множественный заказ
                        if assistant_result['items'] and len(assistant_result['items']) > 0:
                            user_intent = {
                                'is_multiple_order': True,
                                'items': assistant_result['items']
                            }
                        else:
                            user_intent = {}
                    else:
                        # Если это один объект
                        user_intent = assistant_result
            except Exception as gpt_error:
                logger.error(f"Fallback GPT также не сработал: {gpt_error}")
                user_intent = self._create_basic_user_intent(text)
            
            return {
                'type': 'text',
                'original_content': text,
                'processed_text': text,
                'user_intent': user_intent
            }
    
    async def _process_voice_message(self, message: Message) -> dict:
        """Обрабатывает голосовое сообщение"""
        try:
            # Получаем файл
            if not self.bot:
                raise ValueError("Bot объект не доступен для обработки голосовых сообщений")
            
            voice_file = await self.bot.get_file(message.voice.file_id)
            
            # Проверяем размер
            if voice_file.file_size > MAX_FILE_SIZE:
                raise ValueError("Файл слишком большой")
            
            # Конвертируем в текст
            text = await self.media_processor.voice_to_text(voice_file.file_path)
            
            # Умный анализ намерения
            try:
                from services.smart_parser import SmartParser
                smart_parser = SmartParser()
                
                # Для голосовых сообщений всегда используем GPT (они сложные)
                user_intent = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Голосовой GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе голосового сообщения: {e}")
                user_intent = None
            
            return {
                'type': 'voice',
                'original_content': f"Голосовое сообщение ({message.voice.duration}с)",
                'processed_text': text,
                'user_intent': user_intent,
                'is_voice': True  # Добавляем флаг для подписи
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            return None
    
    async def _process_audio_message(self, message: Message) -> dict:
        """Обрабатывает аудио файл"""
        try:
            # Получаем файл
            if not self.bot:
                raise ValueError("Bot объект не доступен для обработки аудио сообщений")
            
            audio_file = await self.bot.get_file(message.audio.file_id)
            
            # Проверяем размер
            if audio_file.file_size > MAX_FILE_SIZE:
                raise ValueError("Файл слишком большой")
            
            # Конвертируем в текст
            text = await self.media_processor.audio_to_text(audio_file.file_path)
            
            # Умный анализ намерения
            try:
                from services.smart_parser import SmartParser
                smart_parser = SmartParser()
                
                # Для аудио файлов всегда используем GPT (они сложные)
                user_intent = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Аудио GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе аудио файла: {e}")
                user_intent = None
            
            return {
                'type': 'audio',
                'original_content': f"Аудио файл: {message.audio.title or 'Без названия'}",
                'processed_text': text,
                'user_intent': user_intent
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио файла: {e}")
            return None
    
    async def _process_photo_message(self, message: Message) -> dict:
        """Обрабатывает фото"""
        try:
            # Получаем файл (берем самое большое фото)
            if not self.bot:
                raise ValueError("Bot объект не доступен для обработки фото")
            
            photo = message.photo[-1]
            photo_file = await self.bot.get_file(photo.file_id)
            
            # Проверяем размер
            if photo_file.file_size > MAX_FILE_SIZE:
                raise ValueError("Файл слишком большой")
            
            # Извлекаем текст из изображения
            text = await self.media_processor.image_to_text(photo_file.file_path)
            
            # Для фото всегда используем GPT (они сложные)
            try:
                user_intent = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Фото GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе фото: {e}")
                user_intent = None
            
            return {
                'type': 'photo',
                'original_content': f"Фото ({photo.width}x{photo.height})",
                'processed_text': text,
                'user_intent': user_intent
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            return None
    
    async def _process_document_message(self, message: Message) -> dict:
        """Обрабатывает документ"""
        try:
            document = message.document
            
            # Проверяем размер
            if document.file_size > MAX_FILE_SIZE:
                raise ValueError("Файл слишком большой")
            
            # Получаем файл
            if not self.bot:
                raise ValueError("Bot объект не доступен для обработки документов")
            
            doc_file = await self.bot.get_file(document.file_id)
            
            # Обрабатываем в зависимости от типа
            if document.mime_type and 'audio' in document.mime_type:
                text = await self.media_processor.audio_to_text(doc_file.file_path)
            elif document.mime_type and 'image' in document.mime_type:
                text = await self.media_processor.image_to_text(doc_file.file_path)
            elif document.mime_type and 'pdf' in document.mime_type:
                text = await self.media_processor.pdf_to_text(doc_file.file_path)
            else:
                # Для других типов файлов пока возвращаем заглушку
                text = f"Файл: {document.file_name}"
            
            # Для документов всегда используем GPT (они сложные)
            try:
                user_intent = await self.openai_service.analyze_with_assistant(text)
                logger.info(f"Документ GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе документа: {e}")
                user_intent = None
            # Нормализуем формат для множественных позиций
            if isinstance(user_intent, list):
                user_intent = { 'is_multiple_order': True, 'items': user_intent }
            
            return {
                'type': 'document',
                'original_content': f"Документ: {document.file_name}",
                'processed_text': text,
                'user_intent': user_intent,
                'is_document': True  # Добавляем флаг для подписи
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            return None
    
    def _analyze_query_complexity(self, text: str) -> tuple[bool, str, dict]:
        """Анализирует сложность запроса и определяет нужен ли GPT"""
        text_lower = text.lower().strip()
        
        # Простые паттерны (НЕ нужен GPT)
        simple_patterns = [
            r'DIN\s+\d+\s+[MМ]\d+[x×]\d+',        # DIN 965 M6x20
            r'[MМ]\d+\s+\d+\s*мм',                # M6 20 мм
            r'винт\s+[MМ]\d+',                    # винт M6
            r'гайка\s+[MМ]\d+',                   # гайка M6
            r'болт\s+[MМ]\d+[x×]\d+',            # болт М6x40
            r'болт\s+[MМ]\d+\s+\d+\s*шт',      # болт M6 10 шт
        ]
        
        # Проверяем простые паттерны
        for pattern in simple_patterns:
            if re.search(pattern, text_lower):
                basic_intent = self._create_basic_user_intent(text)
                return False, "Простой формат", basic_intent
        
        # Индикаторы сложности (НУЖЕН GPT)
        complex_indicators = [
            'нужно', 'требуется', 'заказать', 'разных', 'несколько',
            'что-то', 'подходящий', 'для крепления', 'мебельный',
            'грибком', 'шестигранный', 'с фрезой'
        ]
        
        for indicator in complex_indicators:
            if indicator in text_lower:
                return True, f"Сложный запрос: {indicator}", {}
        
        # По умолчанию используем GPT для неопределенных случаев
        return True, "Неопределенный запрос", {}
    
    def _create_basic_user_intent(self, text: str) -> dict:
        """Создает базовый user_intent из текста"""
        text_lower = text.lower()
        
        # Определяем тип
        detected_type = 'саморез'
        if 'болт' in text_lower:
            detected_type = 'болт'
        elif 'винт' in text_lower:
            detected_type = 'винт'
        elif 'гайка' in text_lower:
            detected_type = 'гайка'
        elif 'шайба' in text_lower:
            detected_type = 'шайба'
        elif 'анкер' in text_lower:
            detected_type = 'анкер'
        
        # Ищем размеры M6x40
        diameter = None
        length = None
        match = re.search(r'[MМ](\d+)(?:[x×х]\s*(\d+))?', text_lower)
        if match:
            diameter = f"M{match.group(1)}"
            if match.group(2):
                length = f"{match.group(2)} мм"
        
        # Ищем количество
        quantity = None
        qty_match = re.search(r'(\d+)\s*шт', text_lower)
        if qty_match:
            quantity = int(qty_match.group(1))
        
        return {
            'type': detected_type,
            'diameter': diameter,
            'length': length,
            'quantity': quantity,
            'confidence': 0.7
        }

