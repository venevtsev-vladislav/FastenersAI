# Fastener Search Edge Function

## Описание
Edge Function для умного поиска деталей крепежа в Supabase.

## Функциональность
- 🔍 Умный поиск по названию и типу
- 📊 Ранжирование результатов по релевантности
- 🎯 Расчет confidence score
- 💡 Объяснение причин совпадения

## Использование

### POST запрос:
```json
{
  "search_query": "болт м20",
  "user_intent": {
    "type": "болт",
    "diameter": "20 мм",
    "material": "металл"
  }
}
```

### Ответ:
```json
{
  "results": [
    {
      "id": 1,
      "name": "Болт М20х100",
      "type": "болт",
      "diameter": "20 мм",
      "relevance_score": 0.95,
      "match_reason": "Точное совпадение"
    }
  ]
}
```

## Деплой
1. Скопируйте код в Supabase Dashboard → Edge Functions
2. Создайте функцию `fastener-search`
3. Вставьте код из `index.ts`
4. Нажмите Deploy

## Локальная разработка
```bash
cd supabase/functions/fastener-search
deno task dev
```
