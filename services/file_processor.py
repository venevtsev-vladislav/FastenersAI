"""
Сервис для обработки файлов (Excel, PDF, изображения)
"""

import logging
import os
import tempfile
import pandas as pd
from typing import Optional, Dict, Any, List
from telegram import Message
from telegram.ext import ContextTypes
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class FileProcessor:
    """Класс для обработки различных типов файлов"""
    
    # Поддерживаемые типы файлов
    SUPPORTED_DOCUMENT_TYPES = ['.xlsx', '.xls', '.pdf', '.jpg', '.jpeg', '.png']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_FILES_PER_REQUEST = 3  # Максимум 3 файла одновременно
    
    def __init__(self):
        self.temp_files = []  # Для отслеживания временных файлов
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def process_single_file(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает один файл"""
        try:
            if message.photo:
                return await self._process_photo(message, context)
            elif message.document:
                return await self._process_document(message, context)
            else:
                logger.warning(f"Неподдерживаемый тип файла: {message.content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обработке файла: {e}")
            return None
    
    async def process_multiple_files(self, messages: List[Message], context: ContextTypes.DEFAULT_TYPE) -> List[Dict[str, Any]]:
        """Обрабатывает несколько файлов параллельно"""
        try:
            # Ограничиваем количество файлов
            if len(messages) > self.MAX_FILES_PER_REQUEST:
                logger.warning(f"Слишком много файлов: {len(messages)}. Обрабатываем только первые {self.MAX_FILES_PER_REQUEST}")
                messages = messages[:self.MAX_FILES_PER_REQUEST]
            
            # Создаем задачи для параллельной обработки
            tasks = []
            for message in messages:
                task = asyncio.create_task(self.process_single_file(message, context))
                tasks.append(task)
            
            # Ждем завершения всех задач
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Ошибка при обработке файла {i+1}: {result}")
                    processed_results.append({
                        'type': 'error',
                        'error': f'Ошибка при обработке файла {i+1}: {str(result)}'
                    })
                elif result:
                    processed_results.append(result)
                else:
                    processed_results.append({
                        'type': 'error',
                        'error': f'Не удалось обработать файл {i+1}'
                    })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Ошибка при обработке множественных файлов: {e}")
            return []
    
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
    
    async def _process_document(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает документ"""
        try:
            document = message.document
            
            # Проверяем размер файла
            if document.file_size and document.file_size > self.MAX_FILE_SIZE:
                logger.warning(f"Файл слишком большой: {document.file_size} байт")
                return {
                    'type': 'document',
                    'error': f'Файл слишком большой. Максимальный размер: {self.MAX_FILE_SIZE // 1024 // 1024} MB'
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
                
                # Обрабатываем в зависимости от типа файла
                if file_extension in ['.xlsx', '.xls']:
                    parsed_content = await self._parse_excel(temp_file.name)
                elif file_extension == '.pdf':
                    parsed_content = await self._parse_pdf(temp_file.name)
                elif file_extension in ['.jpg', '.jpeg', '.png']:
                    parsed_content = await self._parse_image(temp_file.name)
                else:
                    parsed_content = None
                
                return {
                    'type': 'document',
                    'file_path': temp_file.name,
                    'file_name': document.file_name,
                    'file_size': document.file_size,
                    'mime_type': document.mime_type,
                    'file_extension': file_extension,
                    'caption': message.caption or '',
                    'parsed_content': parsed_content
                }
                
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            return None
    
    async def _parse_excel(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Парсит Excel файл"""
        try:
            # Используем ThreadPoolExecutor для синхронных операций
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, self._parse_excel_sync, file_path)
            return result
        except Exception as e:
            logger.error(f"Ошибка при парсинге Excel: {e}")
            return None
    
    def _parse_excel_sync(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Синхронный парсинг Excel файла"""
        try:
            # Читаем все листы
            excel_file = pd.ExcelFile(file_path)
            sheets_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # Конвертируем в словарь для JSON сериализации
                sheets_data[sheet_name] = {
                    'data': df.to_dict('records'),
                    'columns': df.columns.tolist(),
                    'shape': df.shape
                }
            
            return {
                'type': 'excel',
                'sheets': sheets_data,
                'total_sheets': len(excel_file.sheet_names)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при синхронном парсинге Excel: {e}")
            return None
    
    async def _parse_pdf(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Парсит PDF файл"""
        try:
            # TODO: Добавить парсинг PDF с помощью PyPDF2 или pdfplumber
            # Пока возвращаем заглушку
            return {
                'type': 'pdf',
                'message': 'Парсинг PDF файлов будет добавлен в следующих версиях'
            }
        except Exception as e:
            logger.error(f"Ошибка при парсинге PDF: {e}")
            return None
    
    async def _parse_image(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Парсит изображение (OCR)"""
        try:
            # TODO: Добавить OCR с помощью Tesseract или других библиотек
            # Пока возвращаем заглушку
            return {
                'type': 'image',
                'message': 'OCR для изображений будет добавлен в следующих версиях'
            }
        except Exception as e:
            logger.error(f"Ошибка при парсинге изображения: {e}")
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
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

