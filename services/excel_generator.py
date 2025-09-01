"""
Сервис для генерации Excel файлов с результатами поиска
"""

import logging
import os
import tempfile
import math
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from config import MAX_EXCEL_ROWS

logger = logging.getLogger(__name__)

class ExcelGenerator:
    """Класс для генерации Excel файлов с результатами поиска"""
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
    
    async def generate_excel(self, search_results: list, user_request: str) -> str:
        """Генерирует Excel файл с результатами поиска"""
        try:
            # Сохраняем запрос пользователя для использования в заполнении данных
            self.user_request = user_request
            
            # Ограничиваем количество строк
            if len(search_results) > MAX_EXCEL_ROWS:
                search_results = search_results[:MAX_EXCEL_ROWS]
                logger.warning(f"Ограничили результаты до {MAX_EXCEL_ROWS} строк")
            
            # Создаем рабочую книгу
            self.workbook = Workbook()
            self.worksheet = self.workbook.active
            self.worksheet.title = "Результаты поиска"
            
            # Настраиваем заголовки
            self._setup_headers()
            
            # Заполняем данными
            self._fill_data(search_results)
            
            # Настраиваем стили
            self._apply_styles()
            
            # Автоматически подгоняем ширину колонок
            self._auto_adjust_columns()
            
            # Создаем временный файл
            temp_file = self._create_temp_file()
            
            # Сохраняем
            self.workbook.save(temp_file)
            logger.info(f"Excel файл создан: {temp_file}")
            
            return temp_file
            
        except Exception as e:
            logger.error(f"Ошибка при создании Excel файла: {e}")
            raise
    
    def _setup_headers(self):
        """Настраивает заголовки таблицы"""
        headers = [
            "№",
            "Позиция в заказе",
            "Исходный запрос пользователя",
            "Поисковый запрос",
            "Кол-во запрашиваемых деталей",
            "Артикул (SKU)",
            "Наименование в каталоге",
            "Тип детали",
            "Размер упаковки",
            "Единица измерения",
            "Релевантность",
            "Вероятность (%)",
            "Вопросы для уточнения",
            "Статус валидации",
            "Улучшенный поиск",
            "Цикл улучшения",
            "Нормализация ИИ"
        ]
        
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def _fill_data(self, search_results: list):
        """Заполняет таблицу данными"""
        probs = [r.get('probability_percent') for r in search_results
                 if isinstance(r.get('probability_percent'), (int, float))]
        if probs:
            logger.info(
                "[EXPORT] prob%% count=%d min=%d max=%d avg=%d",
                len(probs), min(probs), max(probs),
                round(sum(probs) / len(probs))
            )
        else:
            logger.warning("[EXPORT] prob%% no valid values")

        for row, item in enumerate(search_results, 2):
            # Номер строки
            self.worksheet.cell(row=row, column=1, value=row - 1)
            
            # Позиция в заказе
            order_position = item.get('order_position', '')
            self.worksheet.cell(row=row, column=2, value=order_position)
            
            # Исходный запрос пользователя (полный запрос)
            self.worksheet.cell(row=row, column=3, value=self.user_request)
            
            # Поисковый запрос (что искали для этой позиции)
            search_query = item.get('full_query', item.get('search_query', ''))
            if not search_query:
                # Если нет search_query, используем user_intent для создания поискового запроса
                user_intent = item.get('user_intent', {})
                if user_intent:
                    type_part = user_intent.get('type', '')
                    diameter_part = user_intent.get('diameter', '')
                    length_part = user_intent.get('length', '')
                    coating_part = user_intent.get('coating', '')
                    
                    parts = []
                    if type_part: parts.append(type_part)
                    if diameter_part: parts.append(diameter_part)
                    if length_part: parts.append(length_part)
                    if coating_part: parts.append(coating_part)
                    
                    search_query = ' '.join(parts) if parts else 'Поиск по базе'
                else:
                    search_query = 'Поиск по базе'
            
            self.worksheet.cell(row=row, column=4, value=search_query)
            
            # Количество запрашиваемых деталей
            requested_qty = item.get('requested_quantity', 1)
            self.worksheet.cell(row=row, column=5, value=requested_qty)
            
            # Артикул
            self.worksheet.cell(row=row, column=6, value=item.get('sku', ''))
            
            # Наименование
            self.worksheet.cell(row=row, column=7, value=item.get('name', ''))
            
            # Тип детали
            self.worksheet.cell(row=row, column=8, value=item.get('type', ''))
            
            # Размер упаковки
            self.worksheet.cell(row=row, column=9, value=item.get('pack_size', ''))
            
            # Единица измерения
            self.worksheet.cell(row=row, column=10, value=item.get('unit', ''))
            
            # Релевантность (вычисляем на основе позиции в результатах)
            relevance = "Высокая" if row <= 3 else "Средняя" if row <= 8 else "Низкая"
            self.worksheet.cell(row=row, column=11, value=relevance)
            
            # Вероятность (процент уверенности бота)
            prob = item.get('probability_percent')
            if prob is None:
                prob = item.get(
                    'confidence_score',
                    self._calculate_confidence(item, row, len(search_results))
                )
            if not isinstance(prob, (int, float)) or math.isnan(prob):
                raise ValueError('probability_percent is missing or not a number')
            confidence = prob
            cell = self.worksheet.cell(row=row, column=12, value=prob / 100)
            cell.number_format = "0.0%"
            
            # Вопросы для уточнения (если уверенность < 90%)
            clarification_question = ""
            if confidence < 90:
                clarification_question = item.get('clarification_question', self._generate_clarification_question(item, confidence))
            self.worksheet.cell(row=row, column=13, value=clarification_question)
            
            # Статус валидации
            validation_status = item.get('validation_status', '')
            self.worksheet.cell(row=row, column=14, value=validation_status)
            
            # Информация об улучшенном поиске
            if item.get('is_refined_search'):
                improved_info = f"Улучшенный поиск: {item.get('improved_query', '')}"
                self.worksheet.cell(row=row, column=15, value=improved_info)
            else:
                self.worksheet.cell(row=row, column=15, value="")
            
            # Цикл улучшения
            cycle_number = item.get('cycle_number', '')
            self.worksheet.cell(row=row, column=16, value=cycle_number)
            
            # Нормализация ИИ
            if item.get('is_normalized'):
                normalization_info = f"Исходный: {item.get('original_query', '')}\nНормализованный: {item.get('normalized_query', '')}"
                self.worksheet.cell(row=row, column=17, value=normalization_info)
            else:
                self.worksheet.cell(row=row, column=17, value="")
    
    def _apply_styles(self):
        """Применяет стили к таблице"""
        # Границы
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Применяем границы ко всем ячейкам с данными
        for row in self.worksheet.iter_rows(min_row=1, max_row=self.worksheet.max_row, min_col=1, max_col=17):
            for cell in row:
                cell.border = thin_border
                cell.alignment = Alignment(horizontal="left", vertical="center")
        
        # Выравнивание заголовков по центру
        for col in range(1, 18):
            cell = self.worksheet.cell(row=1, column=col)
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def _auto_adjust_columns(self):
        """Автоматически подгоняет ширину колонок"""
        for column in self.worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)  # Максимум 50 символов
            self.worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _create_temp_file(self) -> str:
        """Создает временный файл для Excel"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = tempfile.gettempdir()
        filename = f"search_results_{timestamp}.xlsx"
        return os.path.join(temp_dir, filename)
    
    def _calculate_confidence(self, item: dict, row_position: int, total_results: int) -> int:
        """Рассчитывает процент уверенности бота в результате"""
        try:
            # Базовый балл на основе позиции в результатах
            position_score = max(0, 100 - (row_position - 2) * 8)  # Первый результат = 100%, каждый следующий -8%
            
            # Анализ совпадения названия с запросом
            name = item.get('name', '').lower()
            query = self.user_request.lower()
            
            # Подсчет совпадающих слов
            query_words = [word for word in query.split() if len(word) > 2]
            name_words = name.split()
            
            matching_words = 0
            for q_word in query_words:
                for n_word in name_words:
                    if q_word in n_word or n_word in q_word:
                        matching_words += 1
                        break
            
            # Балл за совпадение слов
            word_match_score = min(30, (matching_words / len(query_words)) * 30) if query_words else 0
            
            # Балл за точность совпадения
            if query in name:
                exact_match_score = 40
            else:
                exact_match_score = 0
            
            # Итоговый балл
            total_confidence = min(100, position_score + word_match_score + exact_match_score)
            
            return int(total_confidence)
            
        except Exception as e:
            # В случае ошибки возвращаем базовый балл
            return max(0, 100 - (row_position - 2) * 8)

    def _generate_clarification_question(self, item: dict, confidence: int) -> str:
        """Генерирует вопрос для уточнения на основе уверенности"""
        try:
            name = item.get('name', '').lower()
            query = self.user_request.lower()
            
            # Простые правила для генерации вопросов
            if confidence < 50:
                return "Это точно то, что вы ищете? Можете уточнить параметры?"
            elif confidence < 70:
                return "Какие характеристики наиболее важны для вас?"
            elif confidence < 90:
                return "Подходит ли этот вариант или нужны другие параметры?"
            else:
                return ""
                
        except Exception as e:
            return "Можете уточнить параметры?"

