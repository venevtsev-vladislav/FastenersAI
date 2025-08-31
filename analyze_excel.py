#!/usr/bin/env python3
import pandas as pd
import os

# Получаем список файлов и находим Excel файл
source_dir = "Source"
files = os.listdir(source_dir)
excel_file = None

for file in files:
    if file.endswith('.xlsx'):
        excel_file = file
        break

if excel_file:
    file_path = os.path.join(source_dir, excel_file)
    print(f"Найден Excel файл: {excel_file}")
    print(f"Полный путь: {file_path}")
    print(f"Размер файла: {os.path.getsize(file_path)} байт")
    
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print(f"\nКолонки: {df.columns.tolist()}")
        print(f"Размер таблицы: {df.shape}")
        
        # Показываем строки с 2 по 20 для понимания структуры
        print(f"\nСтроки 2-20 (пропускаем пустые):")
        for i in range(2, min(21, len(df))):
            row = df.iloc[i]
            if pd.notna(row['Unnamed: 1']) and pd.notna(row['Unnamed: 2']):
                print(f"Строка {i}:")
                print(f"  Колонка 1: {row['Unnamed: 1']}")
                print(f"  Колонка 2: {row['Unnamed: 2']}")
                print()
        
        # Статистика по данным
        print(f"\nСтатистика:")
        print(f"Всего строк: {len(df)}")
        print(f"Непустых строк в колонке 1: {df['Unnamed: 1'].notna().sum()}")
        print(f"Непустых строк в колонке 2: {df['Unnamed: 2'].notna().sum()}")
        
        # Примеры уникальных значений
        print(f"\nПримеры уникальных значений в колонке 1:")
        unique_values = df['Unnamed: 1'].dropna().unique()
        for i, val in enumerate(unique_values[:10]):
            print(f"  {i+1}. {val}")
        
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
else:
    print("Excel файл не найден в папке Source")
    print("Доступные файлы:")
    for file in files:
        print(f"  {file}")
