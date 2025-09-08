"""
Enhanced message handler for the new FastenersAI architecture
Based on the comprehensive specification
"""

import logging
import os
import tempfile
from typing import Optional
from telegram import Update, Message
from telegram.ext import ContextTypes
from database.supabase_client_legacy import get_supabase_client_legacy
from pipeline.processing_pipeline import get_processing_pipeline
from services.excel_generator_v2 import get_excel_generator_v2
from services.openai_service import OpenAIService

# Import enhanced logging
try:
    from railway_logging import log_gpt_request, log_gpt_response, log_processing_pipeline, log_error
except ImportError:
    # Fallback if railway_logging is not available
    def log_gpt_request(text, user_id=None, chat_id=None):
        logging.info(f"🤖 GPT ЗАПРОС | user_id={user_id} | chat_id={chat_id} | text={text[:100]}...")
    
    def log_gpt_response(response, user_id=None, chat_id=None):
        logging.info(f"✅ GPT ОТВЕТ | user_id={user_id} | chat_id={chat_id} | response={response}")
    
    def log_processing_pipeline(step, data=None, user_id=None, chat_id=None):
        logging.info(f"🔄 PIPELINE {step} | user_id={user_id} | chat_id={chat_id}")
    
    def log_error(error, context=None, user_id=None, chat_id=None):
        logging.error(f"❌ ОШИБКА | context={context} | user_id={user_id} | chat_id={chat_id} | error={str(error)}")

logger = logging.getLogger(__name__)

class MessageHandlerV2:
    """Enhanced message handler for the new architecture"""
    
    def __init__(self):
        self.supabase_client = None
        self.processing_pipeline = get_processing_pipeline()
        self.excel_generator = get_excel_generator_v2()
        self.openai_service = OpenAIService()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        try:
            message = update.effective_message
            if not message:
                return
            
            user_id = str(update.effective_user.id)
            chat_id = str(update.effective_chat.id)
            
            # Initialize Supabase client
            if not self.supabase_client:
                self.supabase_client = await get_supabase_client_legacy()
            
            # Send processing message
            processing_msg = await message.reply_text("🔄 Обрабатываю ваш запрос...")
            
            # Determine message type and process
            if message.text:
                await self._handle_text_message(message, user_id, chat_id)
            elif message.photo:
                await self._handle_photo_message(message, user_id, chat_id, context)
            elif message.voice:
                await self._handle_voice_message(message, user_id, chat_id, context)
            elif message.document:
                await self._handle_document_message(message, user_id, chat_id, context)
            else:
                await message.reply_text("❌ Неподдерживаемый тип сообщения")
                return
            
            # Delete processing message
            try:
                await processing_msg.delete()
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await message.reply_text("❌ Произошла ошибка при обработке сообщения")
    
    async def _handle_text_message(self, message: Message, user_id: str, chat_id: str):
        """Handle text messages"""
        try:
            text = message.text.strip()
            if not text:
                await message.reply_text("❌ Пустое сообщение")
                return
            
            # Log the incoming text message
            log_processing_pipeline("TEXT_MESSAGE_RECEIVED", {"text": text[:200]}, user_id, chat_id)
            
            # Process with GPT Assistant directly first
            log_processing_pipeline("STARTING_GPT_ANALYSIS", {"input_text": text[:200]}, user_id, chat_id)
            
            # Use GPT Assistant for analysis
            gpt_result = await self.openai_service.analyze_with_assistant(text)
            
            log_processing_pipeline("GPT_ANALYSIS_COMPLETED", {"gpt_result": gpt_result}, user_id, chat_id)
            
            # Create request with GPT result
            request_id = await self.supabase_client.create_request_with_gpt_result(
                chat_id=chat_id,
                user_id=user_id,
                source='text',
                original_content=text,
                gpt_result=gpt_result
            )
            
            log_processing_pipeline("REQUEST_CREATED", {"request_id": request_id, "gpt_result_saved": True}, user_id, chat_id)
            
            # Convert GPT result to processing results format
            results = self._convert_gpt_result_to_processing_results(gpt_result, request_id)
            
            log_processing_pipeline("PROCESSING_COMPLETED", {"results_count": len(results) if results else 0}, user_id, chat_id)
            
            # Generate Excel
            request_data = {
                'input_lines': [text],
                'source': 'text'
            }
            
            excel_file = await self.excel_generator.generate_excel(
                request_id=request_id,
                results=results,
                request_data=request_data
            )
            
            log_processing_pipeline("EXCEL_GENERATED", {"file": excel_file}, user_id, chat_id)
            
            # Send Excel file
            await self._send_excel_file(message, excel_file, request_id)
            
            log_processing_pipeline("RESPONSE_SENT", {"request_id": request_id}, user_id, chat_id)
            
        except Exception as e:
            log_error(e, "TEXT_MESSAGE_HANDLING", user_id, chat_id)
            await message.reply_text("❌ Ошибка обработки текстового сообщения")
    
    async def _handle_photo_message(self, message: Message, user_id: str, chat_id: str,
                                    context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages with OCR"""
        try:
            # Get the highest resolution photo
            photo = message.photo[-1]
            
            # Download photo
            file = await context.bot.get_file(photo.file_id)
            photo_path = os.path.join(tempfile.gettempdir(), f"photo_{photo.file_id}.jpg")
            await file.download_to_drive(photo_path)
            
            # Perform OCR (placeholder - would use actual OCR service)
            ocr_text = await self._perform_ocr(photo_path)
            
            if not ocr_text:
                await message.reply_text("❌ Не удалось распознать текст на изображении")
                return
            
            # Create request
            request_id = await self.supabase_client.create_request(
                chat_id=chat_id,
                user_id=user_id,
                source='image'
            )
            
            # Process request
            results = await self.processing_pipeline.process_request(
                request_id=request_id,
                input_text=ocr_text,
                source='image'
            )
            
            # Generate Excel
            request_data = {
                'input_lines': [ocr_text],
                'source': 'image',
                'attachment_id': photo.file_id
            }
            
            excel_file = await self.excel_generator.generate_excel(
                request_id=request_id,
                results=results,
                request_data=request_data
            )
            
            # Send Excel file
            await self._send_excel_file(message, excel_file, request_id)
            
            # Clean up
            os.remove(photo_path)
            
        except Exception as e:
            logger.error(f"Error handling photo message: {e}")
            await message.reply_text("❌ Ошибка обработки изображения")
    
    async def _handle_voice_message(self, message: Message, user_id: str, chat_id: str,
                                    context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages with speech-to-text"""
        try:
            # Get voice file
            voice = message.voice
            file = await context.bot.get_file(voice.file_id)
            voice_path = os.path.join(tempfile.gettempdir(), f"voice_{voice.file_id}.ogg")
            await file.download_to_drive(voice_path)
            
            # Perform speech-to-text (placeholder - would use actual STT service)
            transcript = await self._perform_speech_to_text(voice_path)
            
            if not transcript:
                await message.reply_text("❌ Не удалось распознать речь")
                return
            
            # Create request
            request_id = await self.supabase_client.create_request(
                chat_id=chat_id,
                user_id=user_id,
                source='voice'
            )
            
            # Process request
            results = await self.processing_pipeline.process_request(
                request_id=request_id,
                input_text=transcript,
                source='voice'
            )
            
            # Generate Excel
            request_data = {
                'input_lines': [transcript],
                'source': 'voice',
                'attachment_id': voice.file_id
            }
            
            excel_file = await self.excel_generator.generate_excel(
                request_id=request_id,
                results=results,
                request_data=request_data
            )
            
            # Send Excel file
            await self._send_excel_file(message, excel_file, request_id)
            
            # Clean up
            os.remove(voice_path)
            
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")
            await message.reply_text("❌ Ошибка обработки голосового сообщения")
    
    async def _handle_document_message(self, message: Message, user_id: str, chat_id: str,
                                       context: ContextTypes.DEFAULT_TYPE):
        """Handle document messages (Excel files)"""
        try:
            document = message.document
            
            # Check if it's an Excel file
            if not document.file_name.lower().endswith(('.xlsx', '.xls')):
                await message.reply_text("❌ Поддерживаются только Excel файлы (.xlsx, .xls)")
                return
            
            # Download document
            file = await context.bot.get_file(document.file_id)
            doc_path = os.path.join(tempfile.gettempdir(), f"doc_{document.file_id}.xlsx")
            await file.download_to_drive(doc_path)
            
            # Parse Excel file (placeholder - would use actual Excel parser)
            excel_data = await self._parse_excel_file(doc_path)
            
            if not excel_data:
                await message.reply_text("❌ Не удалось прочитать Excel файл")
                return
            
            # Create request
            request_id = await self.supabase_client.create_request(
                chat_id=chat_id,
                user_id=user_id,
                source='excel'
            )
            
            # Process request
            results = await self.processing_pipeline.process_request(
                request_id=request_id,
                input_text=excel_data,
                source='excel'
            )
            
            # Generate Excel
            request_data = {
                'input_lines': excel_data,
                'source': 'excel',
                'attachment_id': document.file_id
            }
            
            excel_file = await self.excel_generator.generate_excel(
                request_id=request_id,
                results=results,
                request_data=request_data
            )
            
            # Send Excel file
            await self._send_excel_file(message, excel_file, request_id)
            
            # Clean up
            os.remove(doc_path)
            
        except Exception as e:
            logger.error(f"Error handling document message: {e}")
            await message.reply_text("❌ Ошибка обработки документа")
    
    async def _send_excel_file(self, message: Message, excel_file: str, request_id: str):
        """Send Excel file to user"""
        try:
            with open(excel_file, 'rb') as f:
                await message.reply_document(
                    document=f,
                    filename=f"fasteners_result_{request_id}.xlsx",
                    caption="📊 Результат обработки запроса"
                )
            
            # Clean up temp file
            os.remove(excel_file)
            
        except Exception as e:
            logger.error(f"Error sending Excel file: {e}")
            await message.reply_text("❌ Ошибка отправки файла")
    
    async def _perform_ocr(self, image_path: str) -> str:
        """Perform OCR on image (placeholder)"""
        # This would use actual OCR service like PaddleOCR or Tesseract
        # For now, return sample text
        return "Анкер клиновой М10х100\nБолт DIN 933 М12х40"
    
    async def _perform_speech_to_text(self, voice_path: str) -> str:
        """Perform speech-to-text (placeholder)"""
        # This would use actual STT service like OpenAI Whisper
        # For now, return sample text
        return "Анкер клиновой М10х100, болт DIN 933 М12х40"
    
    async def _parse_excel_file(self, excel_path: str) -> list:
        """Parse Excel file (placeholder)"""
        # This would use actual Excel parser with openpyxl
        # For now, return sample data
        return ["Анкер клиновой М10х100", "Болт DIN 933 М12х40"]
    
    def _convert_gpt_result_to_processing_results(self, gpt_result: dict, request_id: str) -> list:
        """Convert GPT result to processing results format"""
        try:
            from pipeline.processing_pipeline import ProcessingResult
            
            results = []
            
            if not gpt_result:
                return results
            
            # Handle multiple items
            if 'items' in gpt_result and isinstance(gpt_result['items'], list):
                for i, item in enumerate(gpt_result['items'], 1):
                    result = ProcessingResult(
                        line_id=f"{request_id}_line_{i}",
                        raw_text=f"{item.get('type', '')} {item.get('diameter', '')} {item.get('length', '')} {item.get('quantity', '')}",
                        normalized_text=f"{item.get('type', '')} {item.get('diameter', '')} {item.get('length', '')} {item.get('quantity', '')}",
                        chosen_ku=None,  # No specific KU from GPT
                        qty_packs=None,
                        qty_units=None,
                        unit='шт',
                        price=None,
                        total=None,
                        status='ok' if item.get('confidence', 0) > 0.5 else 'needs_review',
                        chosen_method='gpt',
                        candidates=[]
                    )
                    results.append(result)
            
            # Handle single item
            elif isinstance(gpt_result, dict) and 'type' in gpt_result:
                result = ProcessingResult(
                    line_id=f"{request_id}_line_1",
                    raw_text=f"{gpt_result.get('type', '')} {gpt_result.get('diameter', '')} {gpt_result.get('length', '')} {gpt_result.get('quantity', '')}",
                    normalized_text=f"{gpt_result.get('type', '')} {gpt_result.get('diameter', '')} {gpt_result.get('length', '')} {gpt_result.get('quantity', '')}",
                    chosen_ku=None,
                    qty_packs=None,
                    qty_units=None,
                    unit='шт',
                    price=None,
                    total=None,
                    status='ok' if gpt_result.get('confidence', 0) > 0.5 else 'needs_review',
                    chosen_method='gpt',
                    candidates=[]
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error converting GPT result: {e}")
            return []

# Global message handler instance
_message_handler_v2 = None

def get_message_handler_v2() -> MessageHandlerV2:
    """Get global message handler instance"""
    global _message_handler_v2
    if _message_handler_v2 is None:
        _message_handler_v2 = MessageHandlerV2()
    return _message_handler_v2

# Handler functions for Telegram bot
async def handle_message_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message - entry point"""
    handler = get_message_handler_v2()
    await handler.handle_message(update, context)
