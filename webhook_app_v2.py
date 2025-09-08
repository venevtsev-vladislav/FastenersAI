"""
Enhanced webhook app for the new FastenersAI architecture
Based on the comprehensive specification
"""

import os
import logging
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

# Import handlers
from handlers.command_handler import handle_start, handle_help
from handlers.message_handler_v2 import handle_message_v2

# Import improved logging
from railway_logging import setup_railway_logging, log_telegram_message, log_error

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
SECRET = os.getenv('TG_WEBHOOK_SECRET', '')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set")

# Setup improved logging for Railway
setup_railway_logging()
log = logging.getLogger('webhook_v2')

# Create FastAPI app
app = FastAPI(title="FastenersAI Bot V2", version="2.0.0")

# Global application instance
application = None

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command handler"""
    await update.message.reply_text(
        "✅ **Статус бота:**\n"
        "🟢 Онлайн и готов к работе\n"
        "🌐 Режим: Webhook V2\n"
        "🔧 Версия: Enhanced Architecture\n"
        "📡 Платформа: Railway\n"
        "🎯 Функции: Текст/Excel/Фото/Голос → Excel отчет"
    )

async def initialize_bot():
    """Initialize the Telegram bot application"""
    global application
    if application is None:
        log.info("Initializing Telegram bot application V2...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("help", handle_help))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_v2))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message_v2))
        application.add_handler(MessageHandler(filters.VOICE, handle_message_v2))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_message_v2))
        
        # Add enhanced logging handler
        async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
            message_type = 'unknown'
            if update.effective_message:
                if update.effective_message.text:
                    message_type = 'text'
                elif update.effective_message.photo:
                    message_type = 'photo'
                elif update.effective_message.voice:
                    message_type = 'voice'
                elif update.effective_message.document:
                    message_type = 'document'
                else:
                    message_type = 'other'
            
            # Use enhanced logging
            update_data = update.to_dict()
            log_telegram_message(update_data, message_type)
        
        application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
        
        # Initialize the application
        await application.initialize()
        log.info("Telegram bot application V2 initialized successfully")

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    await initialize_bot()

@app.get('/health')
async def health():
    """Health check endpoint"""
    return {'status': 'ok', 'bot': 'FastenersAI V2', 'version': '2.0.0'}

@app.get('/version')
async def version():
    """Version endpoint"""
    sha = os.getenv('APP_VERSION', os.getenv('RAILWAY_GIT_COMMIT_SHA', 'unknown'))
    return {'version': sha[:7] if sha != 'unknown' else 'dev', 'architecture': 'v2'}

async def handle_update(payload: dict):
    """Process Telegram update"""
    if application is None:
        await initialize_bot()
    
    try:
        # Create Update object from payload
        update = Update.de_json(payload, application.bot)
        if update:
            # Process the update
            await application.process_update(update)
            log.info(f"Processed update {update.update_id}")
        else:
            log.warning("Failed to parse update from payload")
    except Exception as e:
        log.error(f"Error processing update: {e}")

@app.post('/telegram/webhook')
async def telegram_webhook(req: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    """Main webhook endpoint for Telegram"""
    if SECRET and (x_telegram_bot_api_secret_token != SECRET):
        return PlainTextResponse('forbidden', status_code=403)
    
    try:
        payload = await req.json()
        await handle_update(payload)
        return JSONResponse({'ok': True})
    except Exception as e:
        log.error(f"Error in telegram webhook: {e}")
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)

@app.post('/webhook/{token}')
async def telegram_webhook_token(token: str, req: Request, x_telegram_bot_api_secret_token: str | None = Header(default=None)):
    """Backward compatible webhook endpoint with token in URL"""
    if BOT_TOKEN and token != BOT_TOKEN:
        return PlainTextResponse('forbidden', status_code=403)
    if SECRET and (x_telegram_bot_api_secret_token != SECRET):
        return PlainTextResponse('forbidden', status_code=403)
    
    try:
        payload = await req.json()
        await handle_update(payload)
        return JSONResponse({'ok': True})
    except Exception as e:
        log.error(f"Error in webhook with token: {e}")
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)

@app.get('/')
async def root():
    """Root endpoint"""
    return {
        'status': 'FastenersAI Bot V2 is running! 🚀',
        'version': '2.0.0',
        'architecture': 'Enhanced',
        'webhook_url': '/telegram/webhook',
        'health': '/health',
        'version_endpoint': '/version',
        'features': [
            'Text input processing',
            'Excel file processing',
            'Image OCR processing',
            'Voice transcription',
            'Multi-sheet Excel reports',
            'GPT validation for uncertain matches',
            'Comprehensive matching engine'
        ]
    }
