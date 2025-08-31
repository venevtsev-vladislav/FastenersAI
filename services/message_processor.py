"""
Сервис для обработки различных типов сообщений
"""

import logging
import asyncio
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
        
        # Умный анализ намерения пользователя
        try:
            from services.smart_parser import SmartParser
            smart_parser = SmartParser()
            
            # Определяем нужен ли GPT
            parse_result = smart_parser.parse_query(text)
            
            if parse_result['need_gpt']:
                logger.info(f"🔍 SmartParser: GPT необходим для: {parse_result['reason']}")
                # Используем GPT для сложных запросов
                user_intent = await self.openai_service.analyze_user_intent(text)
                logger.info(f"GPT анализ успешен: {user_intent}")
            else:
                logger.info(f"🔍 SmartParser: GPT НЕ нужен: {parse_result['reason']}")
                # Используем результат парсинга по правилам
                user_intent = parse_result['user_intent']
            
            return {
                'type': 'text',
                'original_content': text,
                'processed_text': text,
                'user_intent': user_intent
            }
                
        except Exception as e:
            logger.error(f"Ошибка при анализе через SmartParser: {e}")
            # Fallback: используем GPT
            try:
                user_intent = await self.openai_service.analyze_user_intent(text)
                logger.info(f"Fallback GPT анализ успешен: {user_intent}")
            except Exception as gpt_error:
                logger.error(f"Fallback GPT также не сработал: {gpt_error}")
                user_intent = None
            
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
                user_intent = await self.openai_service.analyze_user_intent(text)
                logger.info(f"Голосовой GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе голосового сообщения: {e}")
                user_intent = None
            
            return {
                'type': 'voice',
                'original_content': f"Голосовое сообщение ({message.voice.duration}с)",
                'processed_text': text,
                'user_intent': user_intent
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
                user_intent = await self.openai_service.analyze_user_intent(text)
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
            
            # Умный анализ намерения
            try:
                from services.smart_parser import SmartParser
                smart_parser = SmartParser()
                
                # Для фото всегда используем GPT (они сложные)
                user_intent = await self.openai_service.analyze_user_intent(text)
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
            
            # Умный анализ намерения
            try:
                from services.smart_parser import SmartParser
                smart_parser = SmartParser()
                
                # Для документов всегда используем GPT (они сложные)
                user_intent = await self.openai_service.analyze_user_intent(text)
                logger.info(f"Документ GPT анализ успешен: {user_intent}")
            except Exception as e:
                logger.error(f"Ошибка при анализе документа: {e}")
                user_intent = None
            
            return {
                'type': 'document',
                'original_content': f"Документ: {document.file_name}",
                'processed_text': text,
                'user_intent': user_intent
            }
            
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            return None

