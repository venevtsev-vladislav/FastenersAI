import os
import logging
import json
import pathlib
from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

# Import existing handlers
from handlers.command_handler import handle_start, handle_help
from handlers.message_handler_full import handle_message, handle_rating_callback

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
SECRET = os.getenv('TG_WEBHOOK_SECRET', '')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN must be set")

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('webhook')

# Create FastAPI app
app = FastAPI()

# Global application instance
application = None

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    await update.message.reply_text(
        "✅ **Статус бота:**\n"
        "🟢 Онлайн и готов к работе\n"
        "🌐 Режим: Webhook\n"
        "🔧 Версия: Lightweight (без NumPy/Pandas)\n"
        "📡 Платформа: Railway"
    )

async def initialize_bot():
    """Initialize the Telegram bot application"""
    global application
    if application is None:
        log.info("Initializing Telegram bot application...")
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("help", handle_help))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        application.add_handler(MessageHandler(filters.VOICE, handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
        application.add_handler(CallbackQueryHandler(handle_rating_callback))
        
        # Add logging handler
        async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
            log.info(f"📨 Получено обновление: {update.update_id}, тип: {update.effective_message.content_type if update.effective_message else 'unknown'}")
        
        application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
        
        # Initialize the application
        await application.initialize()
        log.info("Telegram bot application initialized successfully")

@app.on_event("startup")
async def startup_event():
    """Initialize bot on startup"""
    await initialize_bot()

@app.get('/health')
async def health():
    """Health check endpoint"""
    return {'status': 'ok', 'bot': 'FastenersAI'}

@app.get('/version')
async def version():
    """Version endpoint"""
    sha = os.getenv('APP_VERSION', os.getenv('RAILWAY_GIT_COMMIT_SHA', 'unknown'))
    return {'version': sha[:7] if sha != 'unknown' else 'dev'}

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
        'status': 'FastenersAI Bot is running! 🚀',
        'webhook_url': f'/telegram/webhook',
        'health': '/health',
        'version': '/version'
    }
