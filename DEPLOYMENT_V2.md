# FastenersAI Bot V2 - Deployment Guide

## Overview

This is the enhanced version of the FastenersAI bot based on the comprehensive specification. It includes:

- **Multi-input support**: Text, Excel, images (OCR), voice (STT)
- **Advanced matching engine**: Rules-based + vector search + GPT validation
- **Multi-sheet Excel reports**: Summary, candidates, input, errors
- **Comprehensive database schema**: Items, aliases, requests, candidates
- **Enhanced processing pipeline**: Normalization, scoring, validation

## Architecture

```
Telegram Bot (webhook) → FastAPI → Processing Pipeline → Supabase → Excel Generation
```

### Components

1. **Text Parser**: Normalizes input text with regex rules and synonyms
2. **Matching Engine**: Finds candidates using exact matches, fuzzy search, and scoring
3. **GPT Validator**: Validates uncertain matches using GPT-4o-mini
4. **Excel Generator**: Creates multi-sheet reports with formatting
5. **Database**: Supabase with PostgreSQL + pgvector (optional)

## Database Setup

### 1. Create Tables

Run the SQL script to create the database schema:

```sql
-- Execute database/create_tables.sql in your Supabase project
```

### 2. Sample Data

The script includes sample data for testing:

- Items: Bolts, anchors with specifications
- Aliases: Common variations and synonyms
- RLS policies for multi-tenant support

### 3. Environment Variables

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key

# Optional
TG_WEBHOOK_SECRET=your_webhook_secret
APP_VERSION=git_sha
```

## Deployment

### Railway Deployment

1. **Update Procfile**:
```
web: uvicorn webhook_app_v2:app --host 0.0.0.0 --port $PORT
```

2. **Update requirements.txt**:
```
fastapi==0.104.1
uvicorn==0.24.0
python-telegram-bot==21.0
supabase==2.0.0
openpyxl==3.1.2
openai==1.3.0
python-dotenv==1.0.0
aiohttp==3.9.0
```

3. **Deploy**:
```bash
git add .
git commit -m "Deploy FastenersAI V2"
git push origin main
```

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export TELEGRAM_BOT_TOKEN=your_token
export SUPABASE_URL=your_url
export SUPABASE_KEY=your_key
export OPENAI_API_KEY=your_key
```

3. **Run locally**:
```bash
uvicorn webhook_app_v2:app --host 0.0.0.0 --port 8000
```

4. **Test**:
```bash
python test_integration_v2.py
```

## Configuration

### Matching Thresholds

```python
# In pipeline/matching_engine.py
AUTO_ACCEPT_SCORE = 0.75
MIN_GAP_TO_SECOND = 0.1
GPT_ACCEPT_CONFIDENCE = 0.8
```

### Excel Formatting

```python
# In services/excel_generator_v2.py
CURRENCY_FORMAT = '#,##0.00'
SCORE_FORMAT = '0.000'
MAX_COLUMN_WIDTH = 50
```

## API Endpoints

- `GET /` - Root endpoint with status
- `GET /health` - Health check
- `GET /version` - Version information
- `POST /telegram/webhook` - Main webhook endpoint

## Testing

### Unit Tests

```bash
python test_integration_v2.py
```

### Sample Input

```
Анкер двухраспорный 8х100х12 с крюком
Анкер забиваемый латунный М10
Болт DIN 933 кл.пр.8.8 М10х30, цинк
Винт DIN 7985 М4х40, цинк
```

### Expected Output

Excel file with 4 sheets:
1. **Итог**: Final results with chosen items
2. **Кандидаты**: All search candidates with scores
3. **Вход**: Original input data
4. **Ошибки**: Items that couldn't be matched

## Monitoring

### Logs

The bot logs all processing steps:
- Input parsing
- Candidate matching
- GPT validation
- Excel generation
- Database operations

### Metrics

Track these metrics:
- Processing time per request
- Match success rate
- GPT validation usage
- Error rates by input type

## Troubleshooting

### Common Issues

1. **Database Connection**: Check Supabase credentials
2. **GPT API**: Verify OpenAI API key and limits
3. **File Processing**: Ensure proper file permissions
4. **Memory Usage**: Monitor for large Excel files

### Debug Mode

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Phase 2
- [ ] Vector search with pgvector
- [ ] OCR integration (PaddleOCR/Tesseract)
- [ ] Voice transcription (Whisper)
- [ ] Multi-tenant RLS policies

### Phase 3
- [ ] Dashboard for statistics
- [ ] Batch processing
- [ ] API for external integrations
- [ ] Advanced reporting features

## Support

For issues or questions:
1. Check logs for error details
2. Verify database schema
3. Test with sample data
4. Review configuration settings
