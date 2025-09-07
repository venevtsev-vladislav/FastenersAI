"""
Сервис для обработки файлов (Excel, PDF, изображения) - версия для Railway
Без pandas для избежания конфликтов с numpy
"""

import logging
import os
import tempfile
from typing import Optional, Dict, Any, List
from telegram import Message
from telegram.ext import ContextTypes
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class FileProcessor:
    """Класс для обработки различных типов файлов - версия для Railway"""
    
    # Поддерживаемые типы файлов
    SUPPORTED_EXTENSIONS = {
        '.xlsx': 'Excel файл',
        '.xls': 'Excel файл',
        '.pdf': 'PDF документ',
        '.jpg': 'Изображение',
        '.jpeg': 'Изображение',
        '.png': 'Изображение',
        '.gif': 'Изображение',
        '.bmp': 'Изображение',
        '.webp': 'Изображение'
    }
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def process_file(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """
        Обрабатывает файл, отправленный пользователем
        
        Args:
            message: Сообщение с файлом
            context: Контекст бота
            
        Returns:
            Словарь с результатами обработки или None при ошибке
        """
        try:
            # Получаем информацию о файле
            file_info = await self._get_file_info(message)
            if not file_info:
                return None
            
            # Проверяем тип файла
            if not self._is_supported_file(file_info['extension']):
                await message.reply_text(
                    f"❌ Неподдерживаемый тип файла: {file_info['extension']}\n"
                    f"Поддерживаемые форматы: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
                )
                return None
            
            # Обрабатываем файл в зависимости от типа
            if file_info['extension'] in ['.xlsx', '.xls']:
                return await self._process_excel_file(message, file_info, context)
            elif file_info['extension'] == '.pdf':
                return await self._process_pdf_file(message, file_info, context)
            elif file_info['extension'] in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                return await self._process_image_file(message, file_info, context)
            else:
                await message.reply_text("❌ Неизвестный тип файла")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке файла: {e}")
            await message.reply_text("❌ Произошла ошибка при обработке файла")
            return None
    
    async def _get_file_info(self, message: Message) -> Optional[Dict[str, Any]]:
        """Получает информацию о файле"""
        try:
            if message.document:
                file = message.document
                file_name = file.file_name or "unknown_file"
            elif message.photo:
                file = message.photo[-1]  # Берем самое большое фото
                file_name = f"photo_{file.file_id}.jpg"
            else:
                return None
            
            # Получаем расширение файла
            extension = os.path.splitext(file_name)[1].lower()
            
            return {
                'file': file,
                'file_name': file_name,
                'extension': extension,
                'file_size': file.file_size
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о файле: {e}")
            return None
    
    def _is_supported_file(self, extension: str) -> bool:
        """Проверяет, поддерживается ли тип файла"""
        return extension in self.SUPPORTED_EXTENSIONS
    
    async def _process_excel_file(self, message: Message, file_info: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает Excel файл"""
        try:
            await message.reply_text("📊 Обработка Excel файла...")
            
            # Скачиваем файл
            file_path = await self._download_file(file_info['file'], file_info['file_name'])
            if not file_path:
                return None
            
            # Для Railway версии просто возвращаем информацию о файле
            result = {
                'type': 'excel',
                'file_name': file_info['file_name'],
                'file_size': file_info['file_size'],
                'status': 'downloaded',
                'message': 'Excel файл загружен. Полная обработка будет доступна в полной версии бота.'
            }
            
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке Excel файла: {e}")
            return None
    
    async def _process_pdf_file(self, message: Message, file_info: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает PDF файл"""
        try:
            await message.reply_text("📄 Обработка PDF файла...")
            
            # Скачиваем файл
            file_path = await self._download_file(file_info['file'], file_info['file_name'])
            if not file_path:
                return None
            
            # Для Railway версии просто возвращаем информацию о файле
            result = {
                'type': 'pdf',
                'file_name': file_info['file_name'],
                'file_size': file_info['file_size'],
                'status': 'downloaded',
                'message': 'PDF файл загружен. Полная обработка будет доступна в полной версии бота.'
            }
            
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF файла: {e}")
            return None
    
    async def _process_image_file(self, message: Message, file_info: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает изображение"""
        try:
            await message.reply_text("🖼️ Обработка изображения...")
            
            # Скачиваем файл
            file_path = await self._download_file(file_info['file'], file_info['file_name'])
            if not file_path:
                return None
            
            # Для Railway версии просто возвращаем информацию о файле
            result = {
                'type': 'image',
                'file_name': file_info['file_name'],
                'file_size': file_info['file_size'],
                'status': 'downloaded',
                'message': 'Изображение загружено. Полная обработка будет доступна в полной версии бота.'
            }
            
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            return None
    
    async def _download_file(self, file, file_name: str) -> Optional[str]:
        """Скачивает файл во временную директорию"""
        try:
            # Создаем временный файл
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, file_name)
            
            # Скачиваем файл
            await file.download_to_drive(file_path)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла: {e}")
            return None
    
    def cleanup(self):
        """Очищает ресурсы"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
