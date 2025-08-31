#!/usr/bin/env python3
import json

# Анализируем файл с нормализованными SKU
with open('Source/normalized_skus.jsonl', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Всего SKU: {len(lines)}")

# Анализируем первые 10 записей
print("\nПервые 10 SKU:")
for i, line in enumerate(lines[:10]):
    data = json.loads(line.strip())
    print(f"{i+1}. SKU: {data['sku']}")
    print(f"   Название: {data['name']}")
    print(f"   Тип: {data['type']}")
    print(f"   Размер упаковки: {data['pack_size']} {data['unit']}")
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
    item_type = data.get('type', 'Неизвестно')
    if item_type not in types:
        types[item_type] = 0
    types[item_type] += 1

print(f"\nТоп-10 типов деталей:")
sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
for i, (item_type, count) in enumerate(sorted_types[:10]):
    print(f"  {i+1}. {item_type}: {count}")

# Анализируем размеры упаковок
pack_sizes = {}
for line in lines:
    data = json.loads(line.strip())
    pack_size = data.get('pack_size', 0)
    if pack_size not in pack_sizes:
        pack_sizes[pack_size] = 0
    pack_sizes[pack_size] += 1

print(f"\nТоп-10 размеров упаковок:")
sorted_pack_sizes = sorted(pack_sizes.items(), key=lambda x: x[1], reverse=True)
for i, (size, count) in enumerate(sorted_pack_sizes[:10]):
    print(f"  {i+1}. {size}: {count}")

