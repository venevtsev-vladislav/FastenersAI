"""
Сервис для обработки медиа файлов (изображения, голосовые, документы)
"""

import logging
import os
import tempfile
from typing import Optional, Dict, Any
from telegram import Message
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Класс для обработки различных типов медиа файлов"""
    
    # Поддерживаемые типы файлов
    SUPPORTED_DOCUMENT_TYPES = ['.xlsx', '.xls', '.pdf']
    MAX_FILE_SIZE = 1024 * 1024  # 1 MB
    
    def __init__(self):
        self.temp_files = []  # Для отслеживания временных файлов
    
    async def process_media_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает медиа сообщение и возвращает результат"""
        try:
            if message.photo:
                return await self._process_photo(message, context)
            elif message.voice:
                return await self._process_voice(message, context)
            elif message.document:
                return await self._process_document(message, context)
            else:
                logger.warning(f"Неподдерживаемый тип медиа: {message.content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке медиа: {e}")
            return None
    
    async def _process_photo(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает фотографию"""
        try:
            # Берем фото наилучшего качества
            photo = message.photo[-1]
            
            # Скачиваем файл
            file = await context.bot.get_file(photo.file_id)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                await file.download_to_drive(temp_file.name)
                self.temp_files.append(temp_file.name)
                
                logger.info(f"Фото сохранено: {temp_file.name}")
                
                # TODO: Здесь можно добавить OCR для извлечения текста из изображения
                # Пока возвращаем базовую информацию
                return {
                    'type': 'photo',
                    'file_path': temp_file.name,
                    'file_size': photo.file_size,
                    'width': photo.width,
                    'height': photo.height,
                    'caption': message.caption or '',
                    'extracted_text': None  # Будет заполнено при добавлении OCR
                }
                
        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            return None
    
    async def _process_voice(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает голосовое сообщение"""
        try:
            voice = message.voice
            
            # Скачиваем файл
            file = await context.bot.get_file(voice.file_id)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                await file.download_to_drive(temp_file.name)
                self.temp_files.append(temp_file.name)
                
                logger.info(f"Голосовое сообщение сохранено: {temp_file.name}")
                
                # TODO: Здесь можно добавить распознавание речи (Speech-to-Text)
                # Пока возвращаем базовую информацию
                return {
                    'type': 'voice',
                    'file_path': temp_file.name,
                    'file_size': voice.file_size,
                    'duration': voice.duration,
                    'transcribed_text': None  # Будет заполнено при добавлении STT
                }
                
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            return None
    
    async def _process_document(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает документ"""
        try:
            document = message.document
            
            # Проверяем размер файла
            if document.file_size and document.file_size > self.MAX_FILE_SIZE:
                logger.warning(f"Файл слишком большой: {document.file_size} байт")
                return {
                    'type': 'document',
                    'error': f'Файл слишком большой. Максимальный размер: {self.MAX_FILE_SIZE // 1024} KB'
                }
            
            # Проверяем тип файла
            file_extension = os.path.splitext(document.file_name or '')[-1].lower()
            if file_extension not in self.SUPPORTED_DOCUMENT_TYPES:
                logger.warning(f"Неподдерживаемый тип файла: {file_extension}")
                return {
                    'type': 'document',
                    'error': f'Неподдерживаемый тип файла. Поддерживаются: {", ".join(self.SUPPORTED_DOCUMENT_TYPES)}'
                }
            
            # Скачиваем файл
            file = await context.bot.get_file(document.file_id)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                await file.download_to_drive(temp_file.name)
                self.temp_files.append(temp_file.name)
                
                logger.info(f"Документ сохранен: {temp_file.name}")
                
                # TODO: Здесь можно добавить парсинг Excel/PDF файлов
                # Пока возвращаем базовую информацию
                return {
                    'type': 'document',
                    'file_path': temp_file.name,
                    'file_name': document.file_name,
                    'file_size': document.file_size,
                    'mime_type': document.mime_type,
                    'file_extension': file_extension,
                    'caption': message.caption or '',
                    'parsed_content': None  # Будет заполнено при добавлении парсера
                }
                
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            return None
    
    def cleanup_temp_files(self):
        """Удаляет временные файлы"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"Временный файл удален: {temp_file}")
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла {temp_file}: {e}")
        
        self.temp_files.clear()
    
    def __del__(self):
        """Деструктор - очищает временные файлы"""
        self.cleanup_temp_files()