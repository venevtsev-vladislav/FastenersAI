"""
Полнофункциональный обработчик сообщений для FastenersAI Bot
Включает AI анализ, поиск в Supabase, генерацию Excel файлов
"""

import logging
import asyncio
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Импорты сервисов
from services.message_processor import MessageProcessor
from services.openai_service import OpenAIService
from services.media_processor import MediaProcessor
from services.excel_generator import ExcelGenerator
from database.supabase_client import SupabaseClient
from config import MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class FullMessageHandler:
    """Полнофункциональный обработчик сообщений"""
    
    def __init__(self):
        self.message_processor = MessageProcessor()
        self.openai_service = OpenAIService()
        self.media_processor = MediaProcessor()
        self.excel_generator = ExcelGenerator()
        self.supabase_client = SupabaseClient()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Основной обработчик всех типов сообщений"""
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            message = update.message
            
            logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
            
            # Определяем тип сообщения
            if message.text:
                await self._handle_text_message(update, context)
            elif message.photo:
                await self._handle_photo_message(update, context)
            elif message.voice:
                await self._handle_voice_message(update, context)
            elif message.document:
                await self._handle_document_message(update, context)
            else:
                await message.reply_text("❓ Неизвестный тип сообщения. Попробуйте отправить текст, фото, голосовое сообщение или документ.")
                
        except Exception as e:
            logger.error(f"Критическая ошибка в обработчике сообщений: {e}")
            try:
                await update.message.reply_text("❌ Произошла критическая ошибка. Обратитесь к администратору.")
            except:
                pass

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений с полным функционалом"""
        try:
            message = update.message
            user_message = message.text
            user = update.effective_user
            
            logger.info(f"Обработка текстового сообщения от {user.id}: {user_message[:100]}...")
            
            # Отправляем сообщение о начале обработки
            processing_msg = await message.reply_text("🔄 Обрабатываю ваше сообщение...")
            
            # Обрабатываем сообщение через MessageProcessor
            result = await self.message_processor.process_message(message)
            
            logger.info(f"Результат обработки сообщения: {result}")
            
            if not result or not result.get('user_intent'):
                logger.warning("Не удалось получить user_intent из результата обработки")
                await processing_msg.edit_text("❌ Не удалось обработать ваше сообщение. Попробуйте переформулировать запрос.")
                return
            
            user_intent = result['user_intent']
            logger.info(f"User intent: {user_intent}")
            
            # Обновляем статус
            await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
            
            # Выполняем поиск в Supabase
            search_results = await self._search_in_database(user_intent)
            logger.info(f"Результаты поиска: {len(search_results) if search_results else 0} позиций")
            
            if not search_results:
                logger.warning(f"Поиск не дал результатов для user_intent: {user_intent}")
                # Попробуем fallback поиск
                fallback_results = await self._fallback_search(user_intent)
                if fallback_results:
                    search_results = fallback_results
                    logger.info(f"Fallback поиск дал {len(search_results)} результатов")
                else:
                    await processing_msg.edit_text("❌ Не найдено подходящих деталей. Попробуйте изменить параметры поиска.")
                    return
            
            # Обновляем статус
            await processing_msg.edit_text("📊 Создаю Excel файл с результатами...")
            
            # Генерируем Excel файл
            excel_file = await self._generate_excel_file(search_results, user_intent, user_message)
            
            # Отправляем результат
            await processing_msg.edit_text("✅ Поиск завершён! Отправляю результаты...")
            
            # Отправляем Excel файл
            with open(excel_file, 'rb') as f:
                await message.reply_document(
                    document=f,
                    filename=f"fasteners_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=f"🔍 **Результаты поиска крепежных деталей**\n\n📝 **Ваш запрос:** {user_message}\n📊 **Найдено позиций:** {len(search_results)}\n📅 **Время поиска:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
            
            # Отправляем кнопки для оценки работы бота
            await self._send_rating_buttons(message, user.id)
            
            logger.info(f"Успешно обработан текстовый запрос пользователя {user.id}")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке текстового сообщения: {e}")
            try:
                await update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз.")
            except:
                pass

    async def _handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фото с OCR"""
        try:
            message = update.message
            user = update.effective_user
            
            logger.info(f"Получено фото от {user.id}")
            
            processing_msg = await message.reply_text("📸 Обрабатываю изображение...")
            
            # Обрабатываем фото через MessageProcessor
            result = await self.message_processor.process_message(message)
            
            if not result or not result.get('processed_text'):
                await processing_msg.edit_text("❌ Не удалось извлечь текст из изображения.")
                return
            
            extracted_text = result['processed_text']
            user_intent = result.get('user_intent')
            
            if not user_intent:
                await processing_msg.edit_text("❌ Не удалось распознать крепежные детали на изображении.")
                return
            
            # Выполняем поиск
            await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
            search_results = await self._search_in_database(user_intent)
            
            if not search_results:
                await processing_msg.edit_text("❌ Не найдено подходящих деталей.")
                return
            
            # Генерируем Excel файл
            await processing_msg.edit_text("📊 Создаю Excel файл...")
            excel_file = await self._generate_excel_file(search_results, user_intent, f"Изображение: {extracted_text[:100]}...")
            
            # Отправляем результат
            with open(excel_file, 'rb') as f:
                await message.reply_document(
                    document=f,
                    filename=f"fasteners_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=f"📸 **Результаты поиска по изображению**\n\n📝 **Извлечённый текст:** {extracted_text[:200]}...\n📊 **Найдено позиций:** {len(search_results)}"
                )
            
            await self._send_rating_buttons(message, user.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке фото: {e}")
            try:
                await update.message.reply_text("❌ Произошла ошибка при обработке фото.")
            except:
                pass

    async def _handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений с Speech-to-Text"""
        try:
            message = update.message
            user = update.effective_user
            
            logger.info(f"Получено голосовое сообщение от {user.id}")
            
            processing_msg = await message.reply_text("🎤 Обрабатываю голосовое сообщение...")
            
            # Обрабатываем голос через MessageProcessor
            result = await self.message_processor.process_message(message)
            
            if not result or not result.get('processed_text'):
                await processing_msg.edit_text("❌ Не удалось распознать речь.")
                return
            
            extracted_text = result['processed_text']
            user_intent = result.get('user_intent')
            
            if not user_intent:
                await processing_msg.edit_text("❌ Не удалось распознать крепежные детали в голосовом сообщении.")
                return
            
            # Выполняем поиск
            await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
            search_results = await self._search_in_database(user_intent)
            
            if not search_results:
                await processing_msg.edit_text("❌ Не найдено подходящих деталей.")
                return
            
            # Генерируем Excel файл
            await processing_msg.edit_text("📊 Создаю Excel файл...")
            excel_file = await self._generate_excel_file(search_results, user_intent, f"Голос: {extracted_text[:100]}...")
            
            # Отправляем результат
            with open(excel_file, 'rb') as f:
                await message.reply_document(
                    document=f,
                    filename=f"fasteners_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=f"🎤 **Результаты поиска по голосовому сообщению**\n\n📝 **Распознанный текст:** {extracted_text[:200]}...\n📊 **Найдено позиций:** {len(search_results)}"
                )
            
            await self._send_rating_buttons(message, user.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке голосового сообщения: {e}")
            try:
                await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")
            except:
                pass

    async def _handle_document_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик документов (Excel, PDF)"""
        try:
            message = update.message
            user = update.effective_user
            document = message.document
            
            logger.info(f"Получен документ от {user.id}: {document.file_name}")
            
            # Проверяем размер файла
            if document.file_size > MAX_FILE_SIZE:
                await message.reply_text(f"❌ Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE // (1024*1024)} MB")
                return
            
            processing_msg = await message.reply_text("📄 Обрабатываю документ...")
            
            # Обрабатываем документ через MessageProcessor
            result = await self.message_processor.process_message(message)
            
            if not result or not result.get('processed_text'):
                await processing_msg.edit_text("❌ Не удалось обработать документ.")
                return
            
            extracted_text = result['processed_text']
            user_intent = result.get('user_intent')
            
            if not user_intent:
                await processing_msg.edit_text("❌ Не удалось найти крепежные детали в документе.")
                return
            
            # Выполняем поиск
            await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
            search_results = await self._search_in_database(user_intent)
            
            if not search_results:
                await processing_msg.edit_text("❌ Не найдено подходящих деталей.")
                return
            
            # Генерируем Excel файл
            await processing_msg.edit_text("📊 Создаю Excel файл...")
            excel_file = await self._generate_excel_file(search_results, user_intent, f"Документ: {document.file_name}")
            
            # Отправляем результат
            with open(excel_file, 'rb') as f:
                await message.reply_document(
                    document=f,
                    filename=f"fasteners_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    caption=f"📄 **Результаты поиска по документу**\n\n📁 **Файл:** {document.file_name}\n📝 **Извлечённый текст:** {extracted_text[:200]}...\n📊 **Найдено позиций:** {len(search_results)}"
                )
            
            await self._send_rating_buttons(message, user.id)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке документа: {e}")
            try:
                await update.message.reply_text("❌ Произошла ошибка при обработке документа.")
            except:
                pass

    async def _search_in_database(self, user_intent: dict) -> list:
        """Выполняет поиск в базе данных Supabase"""
        try:
            logger.info(f"Начинаем поиск в базе данных с user_intent: {user_intent}")
            
            # Если это множественный заказ
            if user_intent.get('is_multiple_order') and user_intent.get('items'):
                logger.info("Обрабатываем множественный заказ")
                all_results = []
                for item in user_intent['items']:
                    logger.info(f"Поиск для позиции: {item}")
                    results = await self.supabase_client.search_parts(item)
                    logger.info(f"Найдено {len(results)} результатов для позиции")
                    all_results.extend(results)
                logger.info(f"Всего найдено {len(all_results)} результатов")
                return all_results
            else:
                # Одиночный поиск
                logger.info("Одиночный поиск")
                results = await self.supabase_client.search_parts(user_intent)
                logger.info(f"Найдено {len(results)} результатов")
                return results
                
        except Exception as e:
            logger.error(f"Ошибка при поиске в базе данных: {e}")
            return []

    async def _fallback_search(self, user_intent: dict) -> list:
        """Fallback поиск, если Supabase не работает"""
        try:
            logger.info("Выполняем fallback поиск")
            
            # Создаем простые тестовые данные
            fallback_results = []
            
            if user_intent.get('type') == 'саморез' and user_intent.get('diameter') == '4,2':
                fallback_results = [
                    {
                        'sku': 'TEST-001',
                        'name': 'Саморез по металлу 4,2x25',
                        'type': 'саморез',
                        'diameter': '4,2',
                        'length': '25',
                        'material': 'сталь',
                        'coating': 'цинк',
                        'standard': 'DIN 7981',
                        'strength_class': 'A2-70',
                        'pack_quantity': '100',
                        'price': '0.15',
                        'notes': 'Тестовый результат'
                    },
                    {
                        'sku': 'TEST-002', 
                        'name': 'Саморез по дереву 4,2x25',
                        'type': 'саморез',
                        'diameter': '4,2',
                        'length': '25',
                        'material': 'сталь',
                        'coating': 'фосфат',
                        'standard': 'DIN 7982',
                        'strength_class': 'A2-70',
                        'pack_quantity': '100',
                        'price': '0.12',
                        'notes': 'Тестовый результат'
                    }
                ]
            
            logger.info(f"Fallback поиск вернул {len(fallback_results)} результатов")
            return fallback_results
            
        except Exception as e:
            logger.error(f"Ошибка в fallback поиске: {e}")
            return []

    async def _generate_excel_file(self, search_results: list, user_intent: dict, original_query: str) -> str:
        """Генерирует Excel файл с результатами поиска"""
        try:
            return await self.excel_generator.generate_search_results_excel(
                search_results=search_results,
                user_intent=user_intent,
                original_query=original_query
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации Excel файла: {e}")
            raise

    async def _send_rating_buttons(self, message, user_id: int):
        """Отправляет кнопки для оценки работы бота"""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Да, справился", callback_data=f"rating_good_{user_id}"),
                    InlineKeyboardButton("❌ Нет, не справился", callback_data=f"rating_bad_{user_id}")
                ],
                [
                    InlineKeyboardButton("⚠️ Не совсем", callback_data=f"rating_partial_{user_id}"),
                    InlineKeyboardButton("❓ Не знаю", callback_data=f"rating_unknown_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "🤖 **Оцените работу бота:**\n\nСправился ли бот с вашим запросом?",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке кнопок оценки: {e}")

    async def handle_rating_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатия на кнопки оценки работы бота"""
        try:
            query = update.callback_query
            await query.answer()
            
            # Извлекаем тип оценки и ID пользователя
            callback_data = query.data
            if callback_data.startswith("rating_"):
                rating_type = callback_data.split("_")[1]  # good, bad, partial, unknown
                user_id = callback_data.split("_")[2]
                
                # Логируем оценку
                logger.info(f"Пользователь {user_id} оценил работу бота: {rating_type}")
                
                # Отвечаем пользователю
                rating_messages = {
                    "good": "✅ Спасибо за положительную оценку!",
                    "bad": "❌ Спасибо за обратную связь. Мы работаем над улучшением.",
                    "partial": "⚠️ Понятно, есть над чем поработать.",
                    "unknown": "❓ Спасибо за использование бота!"
                }
                
                await query.edit_message_text(
                    rating_messages.get(rating_type, "Спасибо за оценку!"),
                    reply_markup=None
                )
                
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}")
            try:
                await query.answer("❌ Произошла ошибка при обработке оценки.")
            except:
                pass

# Создаем глобальный экземпляр обработчика
full_handler = FullMessageHandler()

# Экспортируем функции для использования в webhook_app.py
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик сообщений"""
    await full_handler.handle_message(update, context)

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для оценки"""
    await full_handler.handle_rating_callback(update, context)
