"""
Сервис для обработки медиафайлов (голос, аудио, изображения)
"""

import logging
import asyncio

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Класс для обработки медиафайлов"""
    
    def __init__(self):
        # TODO: Добавить реальные сервисы для обработки медиа
        pass
    
    async def voice_to_text(self, file_path: str) -> str:
        """Конвертирует голосовое сообщение в текст через OpenAI Whisper"""
        try:
            logger.info(f"Обработка голосового файла: {file_path}")
            
            # Скачиваем файл если это URL
            local_file_path = await self._download_file(file_path)
            if not local_file_path:
                return "Ошибка скачивания файла"
            
            # Импортируем OpenAI клиент
            from openai import AsyncOpenAI
            from config import OPENAI_API_KEY
            
            # Создаем клиент
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            # Открываем локальный файл
            with open(local_file_path, 'rb') as audio_file:
                # Отправляем в Whisper API
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"  # Указываем русский язык
                )
            
            # Получаем распознанный текст
            recognized_text = response.text.strip()
            logger.info(f"Whisper распознал текст: '{recognized_text}'")
            
            # Удаляем временный файл
            import os
            try:
                os.remove(local_file_path)
                logger.info(f"Временный файл удален: {local_file_path}")
            except:
                pass
            
            return recognized_text
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голоса через Whisper: {e}")
            # Fallback на заглушку
            return "Ошибка распознавания голоса"
    
    async def _download_file(self, file_url: str) -> str:
        """Скачивает файл по URL и возвращает локальный путь"""
        try:
            import aiohttp
            import tempfile
            import os
            
            # Создаем временный файл
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.oga')
            temp_path = temp_file.name
            temp_file.close()
            
            logger.info(f"Скачиваю файл в: {temp_path}")
            
            # Скачиваем файл
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Записываем в временный файл
                        with open(temp_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"Файл успешно скачан: {len(content)} байт")
                        return temp_path
                    else:
                        logger.error(f"Ошибка скачивания: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла: {e}")
            return None
    
    async def audio_to_text(self, file_path: str) -> str:
        """Конвертирует аудио файл в текст через OpenAI Whisper"""
        try:
            logger.info(f"Обработка аудио файла: {file_path}")
            
            # Скачиваем файл если это URL
            local_file_path = await self._download_file(file_path)
            if not local_file_path:
                return "Ошибка скачивания файла"
            
            # Импортируем OpenAI клиент
            from openai import AsyncOpenAI
            from config import OPENAI_API_KEY
            
            # Создаем клиент
            client = AsyncOpenAI(api_key=OPENAI_API_KEY)
            
            # Открываем локальный файл
            with open(local_file_path, 'rb') as audio_file:
                # Отправляем в Whisper API
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )
            
            # Получаем распознанный текст
            recognized_text = response.text.strip()
            logger.info(f"Whisper распознал аудио: '{recognized_text}'")
            
            # Удаляем временный файл
            import os
            try:
                os.remove(local_file_path)
                logger.info(f"Временный файл удален: {local_file_path}")
            except:
                pass
            
            return recognized_text
            
        except Exception as e:
            logger.error(f"Ошибка при обработке аудио через Whisper: {e}")
            return "Ошибка распознавания аудио"
    
    async def image_to_text(self, file_path: str) -> str:
        """Извлекает текст из изображения (OCR)"""
        try:
            logger.info(f"Обработка изображения: {file_path}")
            
            # Скачиваем файл если это URL
            local_file_path = await self._download_file(file_path)
            if not local_file_path:
                return "Ошибка скачивания файла"
            
            # TODO: Реализовать OCR через API (например, Tesseract или облачный сервис)
            # Пока возвращаем заглушку
            await asyncio.sleep(1)
            return "Изображение крепежной детали"
            
        except Exception as e:
            logger.error(f"Ошибка при обработке изображения: {e}")
            return "Ошибка обработки изображения"
    
    async def pdf_to_text(self, file_path: str) -> str:
        """Извлекает текст из PDF файла"""
        try:
            logger.info(f"Обработка PDF файла: {file_path}")
            
            # Скачиваем файл если это URL
            local_file_path = await self._download_file(file_path)
            if not local_file_path:
                return "Ошибка скачивания файла"
            
            # TODO: Реализовать PDF парсинг через PyPDF2 или pdfplumber
            # Пока возвращаем заглушку
            await asyncio.sleep(1)
            return "PDF файл с технической документацией"
            
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF: {e}")
            return "Ошибка обработки PDF"

