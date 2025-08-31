#!/usr/bin/env python3
import json

# Анализируем файл с алиасами
with open('Source/aliases.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Всего алиасов: {len(lines)}")

# Анализируем первые 10 записей
print("\nПервые 10 алиасов:")
for i, line in enumerate(lines[:10]):
    data = json.loads(line.strip())
    print(f"{i+1}. Алиас: '{data['alias']}'")
    print(f"   Маппится на: {data['maps_to']}")
    print(f"   Уверенность: {data['confidence']}")
    print()

# Анализируем структуру данных
print("Структура данных:")
sample = json.loads(lines[0].strip())
for key, value in sample.items():
    print(f"  {key}: {type(value).__name__}")

# Статистика по типам
types = {}
for line in lines:
    data = json.loads(line.strip())
    item_type = data['maps_to'].get('type', 'Неизвестно')
    if item_type not in types:
        types[item_type] = 0
    types[item_type] += 1

print(f"\nТоп-10 типов по алиасам:")
sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
for i, (item_type, count) in enumerate(sorted_types[:10]):
    print(f"  {i+1}. {item_type}: {count}")

# Анализируем уверенность
confidence_levels = {}
for line in lines:
    data = json.loads(line.strip())
    confidence = data['confidence']
    if confidence not in confidence_levels:
        confidence_levels[confidence] = 0
    confidence_levels[confidence] += 1

print(f"\nРаспределение по уверенности:")
for confidence in sorted(confidence_levels.keys()):
    print(f"  {confidence}: {confidence_levels[confidence]}")

# Примеры сложных алиасов
print(f"\nПримеры сложных алиасов (с дополнительными признаками):")
complex_aliases = []
for line in lines:
    data = json.loads(line.strip())
    maps_to = data['maps_to']
    if len(maps_to) > 1:  # Есть дополнительные признаки
        complex_aliases.append(data)

for i, alias in enumerate(complex_aliases[:10]):
    print(f"  {i+1}. '{alias['alias']}' -> {alias['maps_to']}")

