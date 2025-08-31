# 🚀 Быстрое исправление Edge Function

## ❌ Проблема:
Edge Function не находит существующую запись "Болты DIN603 М6х40, цинк (тыс.шт)" по запросу "болт с грибком М6 на 40, цинкованный"

## ✅ Решение:
Изменили логику поиска - теперь ищем в полях `name` и `type`, а не только в `type`

## 🔧 Что исправлено:

### 1. Поиск по типу:
```typescript
// БЫЛО:
query = query.ilike('type', `%${safeType}%`)

// СТАЛО:
query = query.or(`type.ilike.%${safeType}%,name.ilike.%${safeType}%`)
```

### 2. Поиск по подтипу:
```typescript
// БЫЛО:
query = query.or(`name.ilike.%${safeSubtype}%,type.ilike.%${safeSubtype}%`)

// СТАЛО:
query = query.or(`name.ilike.%${safeSubtype}%`)
```

### 3. Поиск по стандарту:
```typescript
// БЫЛО:
query = query.ilike('standard', `%${safeStandard}%`)

// СТАЛО:
query = query.or(`standard.ilike.%${safeStandard}%,name.ilike.%${safeStandard}%`)
```

### 4. Добавлена отладка SQL:
```typescript
console.log('🔍 Edge Function: SQL запрос:', query.toSQL())
```

## 🚀 Как развернуть:

1. **Откройте Supabase Dashboard**
2. **Edge Functions → fastener-search**
3. **Замените содержимое `index.ts`** на исправленную версию
4. **Нажмите "Deploy"**

## 🧪 Тест после исправления:

Отправьте боту: "болт с грибком М6 на 40, цинкованный"

**Ожидаемый результат:** Edge Function найдет "Болты DIN603 М6х40, цинк (тыс.шт)"

## 📊 Логи должны показать:

```
🔍 Edge Function: Структурированный поиск вернул: 1 результатов
🔍 Edge Function: Первые результаты: [{ name: "Болты DIN603 М6х40, цинк (тыс.шт)", sku: "12-0015020" }]
```

Исправление должно решить проблему! 🎯
