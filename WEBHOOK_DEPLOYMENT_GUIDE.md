# 🚀 Webhook Deployment Guide for FastenersAI Bot

## Overview

This guide provides step-by-step instructions for deploying the FastenersAI Telegram bot with proper webhook configuration on Railway.

## ✅ What's Fixed

- **404 Webhook Error**: Fixed by creating proper FastAPI webhook app
- **Health/Version Endpoints**: Added `/health` and `/version` endpoints
- **Port Binding**: App now properly binds to `0.0.0.0:$PORT`
- **Backward Compatibility**: Supports both `/telegram/webhook` and `/webhook/<token>` endpoints
- **Fast Response**: Returns HTTP 200 quickly on valid webhook POST

## 🔧 Environment Variables to Set in Railway

Set these environment variables in your Railway project:

```bash
BOT_TOKEN=8204541100:AAFiu2UBskn9fwCQNAIMj_HAHrVi6QrJ3Wk
TG_WEBHOOK_SECRET=test-secret-123
```

## 📋 Post-Deploy Webhook Setup

After your app is deployed on Railway, run these commands to set up the webhook:

### 1. Set Environment Variables
```bash
export TOKEN="8204541100:AAFiu2UBskn9fwCQNAIMj_HAHrVi6QrJ3Wk"
export DOMAIN="https://<YOUR_RAILWAY_DOMAIN>"
export SECRET="test-secret-123"
```

### 2. Set the Webhook
```bash
curl -s -X POST "https://api.telegram.org/bot$TOKEN/setWebhook" \
  -d "url=$DOMAIN/telegram/webhook" \
  -d 'allowed_updates=["message","callback_query"]' \
  -d 'drop_pending_updates=true' \
  -d "secret_token=$SECRET"
```

### 3. Verify Webhook Configuration
```bash
curl -s "https://api.telegram.org/bot$TOKEN/getWebhookInfo"
```

Expected response should show:
- `url`: `https://<YOUR_DOMAIN>/telegram/webhook`
- `last_error_message`: `null` (or empty)

## 🧪 Smoke Tests

After deployment, run these tests to verify everything works:

### 1. Health Check
```bash
curl -s $DOMAIN/health
```
Expected: `{"status":"ok","bot":"FastenersAI"}`

### 2. Version Check
```bash
curl -s $DOMAIN/version
```
Expected: `{"version":"<git_sha>"}`

### 3. Webhook Test
```bash
curl -i -X POST "$DOMAIN/telegram/webhook" \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: $SECRET" \
  --data '{"update_id":123,"message":{"message_id":1,"date":1736313600,"chat":{"id":111111111,"type":"private"},"text":"/start"}}'
```
Expected: HTTP 200 with `{"ok":true}`

## 📊 Acceptance Criteria

✅ **Telegram getWebhookInfo** shows:
- `url` = `$DOMAIN/telegram/webhook`
- `last_error_message` = `null`

✅ **Railway logs** contain:
- POST `/telegram/webhook` entries
- No 404 errors

✅ **Health endpoint** returns:
- HTTP 200
- `{"status":"ok","bot":"FastenersAI"}`

✅ **Version endpoint** returns:
- HTTP 200
- JSON with version/sha

## 🔄 Backward Compatibility

The webhook app supports both endpoint formats:

1. **New format**: `POST /telegram/webhook`
2. **Legacy format**: `POST /webhook/<token>`

Both endpoints:
- Validate the secret token (if set)
- Process updates through the same handler
- Return HTTP 200 on success

## 🚨 Troubleshooting

### Webhook Still Returns 404
- Check that `nixpacks.toml` is using `webhook_app:app`
- Verify the app is binding to `0.0.0.0:$PORT`
- Check Railway logs for startup errors

### Bot Not Responding
- Verify webhook is set correctly with `getWebhookInfo`
- Check Railway logs for processing errors
- Ensure `BOT_TOKEN` environment variable is set

### Health Check Fails
- Verify the app is running on the correct port
- Check that FastAPI is properly initialized
- Review Railway deployment logs

## 📁 Files Modified

- `webhook_app.py` - New FastAPI webhook application
- `nixpacks.toml` - Updated to use uvicorn with webhook app
- `WEBHOOK_DEPLOYMENT_GUIDE.md` - This deployment guide

## 🎯 Next Steps

1. Deploy to Railway
2. Set environment variables
3. Run post-deploy webhook setup
4. Test with smoke tests
5. Verify bot responds to messages

The bot should now work properly with webhooks and provide health/version endpoints for monitoring!
