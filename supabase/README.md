# Supabase Edge Functions

Папка содержит Edge Functions для Supabase.

## Структура
```
supabase/
├── functions/
│   └── fastener-search/          # Поиск деталей крепежа
│       ├── index.ts              # Основной код функции
│       ├── deno.json             # Конфигурация Deno
│       └── README.md             # Документация
└── README.md                     # Этот файл
```

## Edge Functions

### fastener-search
- **Назначение**: Умный поиск деталей крепежа
- **Функции**: Поиск, ранжирование, расчет релевантности
- **Статус**: Готов к деплою

## Деплой
1. Откройте [Supabase Dashboard](https://supabase.com)
2. Перейдите в **Edge Functions**
3. Создайте новую функцию с названием из папки
4. Скопируйте код из `index.ts`
5. Нажмите **Deploy**

## Локальная разработка
```bash
cd supabase/functions/[function-name]
deno task dev
```
