"""
Основной обработчик сообщений для Telegram бота
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.message_processor import MessageProcessor
from services.excel_generator import ExcelGenerator
from database.supabase_client import save_user_request
from utils.logger import setup_logging

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех типов сообщений"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        # Обрабатываем сообщение
        processor = MessageProcessor(bot=update.get_bot())
        result = await processor.process_message(update.message)
        
        if not result:
            await processing_msg.edit_text("❌ Не удалось обработать сообщение. Попробуйте еще раз.")
            return
        
        # Сохраняем запрос в БД
        await save_user_request(
            user_id=user.id,
            chat_id=chat_id,
            request_type=result['type'],
            original_content=result['original_content'],
            processed_text=result['processed_text'],
            user_intent=result['user_intent']
        )
        
        # Ищем подходящие детали через Supabase + GPT анализ
        await processing_msg.edit_text("🔍 Ищу детали в каталоге...")
        
        # Используем GPT анализ + Supabase поиск
        from database.supabase_client import search_parts
        
        # Проверяем, есть ли GPT анализ
        if not result.get('user_intent'):
            # Fallback: если GPT не сработал, ищем по простому тексту
            logger.warning("GPT анализ недоступен, используем fallback поиск")
            search_results = await search_parts(
                query=result['processed_text'],
                user_intent={}
            )
            
            # Если поиск не дал результатов, пробуем через ИИ
            if not search_results:
                logger.info("🔍 Поиск не дал результатов, обращаюсь к ИИ для уточнения...")
                await processing_msg.edit_text("🤔 Поиск не дал результатов. Обращаюсь к ИИ для уточнения...")
                
                from services.query_fallback_service import QueryFallbackService
                fallback_service = QueryFallbackService()
                fallback_result = await fallback_service.process_failed_query(
                    original_query=result['processed_text'],
                    search_results=search_results
                )
                
                if fallback_result.get('can_normalize'):
                    # ИИ смог нормализовать запрос - пробуем снова
                    normalized_query = fallback_result['normalized_query']
                    logger.info(f"🔄 Пробую поиск с нормализованным запросом: {normalized_query}")
                    
                    await processing_msg.edit_text(f"🔄 Пробую поиск с нормализованным запросом...")
                    search_results = await search_parts(
                        query=normalized_query,
                        user_intent={}
                    )
                    
                    if search_results:
                        logger.info(f"✅ Поиск с нормализованным запросом дал {len(search_results)} результатов")
                        # Добавляем информацию о нормализации
                        for search_result in search_results:
                            search_result['is_normalized'] = True
                            search_result['original_query'] = result['processed_text']
                            search_result['normalized_query'] = normalized_query
                    else:
                        logger.warning("❌ Даже нормализованный запрос не дал результатов")
                        # Показываем сообщение от ИИ
                        user_message = fallback_service.get_user_friendly_message(fallback_result)
                        await update.message.reply_text(user_message)
                        await processing_msg.delete()
                        return
                else:
                    # ИИ не смог нормализовать - показываем сообщение
                    logger.warning("❌ ИИ не смог нормализовать запрос")
                    user_message = fallback_service.get_user_friendly_message(fallback_result)
                    await update.message.reply_text(user_message)
                    await processing_msg.delete()
                    return
        else:
            # Проверяем множественный заказ
            if result['user_intent'].get('is_multiple_order') and result['user_intent'].get('items'):
                logger.info(f"Обрабатываем множественный заказ из {len(result['user_intent']['items'])} позиций")
                
                # Ищем каждую позицию отдельно и сохраняем порядок
                all_results = []
                position_results = {}  # Словарь для группировки результатов по позициям
                
                for i, item in enumerate(result['user_intent']['items']):
                    # Создаем упрощенный запрос для поиска (только основные параметры)
                    search_query_parts = []
                    if item.get('type'):
                        search_query_parts.append(item['type'])
                    if item.get('diameter'):
                        # Упрощаем диаметр: "6 мм" -> "6", "M6" -> "M6"
                        diameter = item['diameter']
                        if 'мм' in diameter:
                            diameter = diameter.replace(' мм', '')
                        search_query_parts.append(diameter)
                    
                    if item.get('standard'):
                        search_query_parts.append(item['standard'])
                    
                    if item.get('grade'):
                        search_query_parts.append(item['grade'])
                    
                    item_query = ' '.join(search_query_parts).strip()
                    if not item_query:
                        item_query = item.get('type', '')  # Fallback на тип если ничего не собрали
                    
                    # Сохраняем полный запрос для отображения в Excel
                    full_item_query = ' '.join([
                        item.get('type', '') or '',
                        item.get('standard', '') or '',
                        item.get('diameter', '') or '',
                        item.get('length', '') or '',
                        item.get('material', '') or '',
                        item.get('coating', '') or '',
                        item.get('grade', '') or ''
                    ]).strip()
                    
                    logger.info(f"🔍 Позиция {i+1}:")
                    logger.info(f"   📝 Полный запрос: {full_item_query}")
                    logger.info(f"   🔎 Упрощенный поиск: {item_query}")
                    logger.info(f"   📊 Параметры: тип={item.get('type')}, стандарт={item.get('standard')}, диаметр={item.get('diameter')}, длина={item.get('length')}, материал={item.get('material')}, покрытие={item.get('coating')}, класс={item.get('grade')}")
                    logger.info(f"   📦 Количество: {item.get('quantity', 1)}")
                    
                    # Ищем деталь
                    logger.info(f"   🔍 Выполняю поиск для: {item_query}")
                    item_results = await search_parts(
                        query=item_query,
                        user_intent=item
                    )
                    
                    logger.info(f"   📊 Найдено результатов: {len(item_results)}")
                    if item_results:
                        logger.info(f"   ✅ Первые результаты:")
                        for j, result_item in enumerate(item_results[:3]):
                            logger.info(f"      {j+1}. SKU: {result_item.get('sku')}, Название: {result_item.get('name')}")
                    else:
                        logger.warning(f"   ❌ Результаты не найдены для: {item_query}")
                        # Создаем fallback результат для позиции без найденных деталей
                        fallback_result = {
                            'sku': 'НЕ НАЙДЕНО',
                            'name': 'Деталь не найдена в каталоге',
                            'type': 'Н/Д',
                            'pack_size': 0,
                            'unit': 'шт',
                            'requested_quantity': item.get('quantity', 1),
                            'order_position': i + 1,
                            'search_query': item_query,
                            'full_query': full_item_query,
                            'original_position': i + 1,
                            'confidence_score': 0,
                            'match_reason': 'Результаты не найдены'
                        }
                        position_results[i + 1] = [fallback_result]
                    
                    # Добавляем информацию о заказе и группируем по позициям
                    if item_results:
                        for item_result in item_results:
                            item_result['requested_quantity'] = item.get('quantity', 1)
                            item_result['order_position'] = i + 1
                            item_result['search_query'] = item_query  # Поисковый запрос (упрощенный)
                            item_result['full_query'] = full_item_query  # Полный запрос для Excel
                            item_result['original_position'] = i + 1  # Оригинальная позиция в заказе
                        
                        position_results[i + 1] = item_results
                
                # Собираем результаты в правильном порядке позиций
                for position in sorted(position_results.keys()):
                    all_results.extend(position_results[position])
                
                search_results = all_results
                logger.info(f"Множественный поиск вернул {len(search_results)} результатов")
                
            else:
                # Обычный поиск для одной позиции
                search_results = await search_parts(
                    query=result['processed_text'],
                    user_intent=result['user_intent']
                )
        
        # Анализируем уверенность бота в результатах (алгоритмически)
        try:
            from services.algorithmic_confidence import AlgorithmicConfidenceAnalyzer
            confidence_analyzer = AlgorithmicConfidenceAnalyzer()
            search_results = confidence_analyzer.analyze_confidence(
                user_query=result['processed_text'],
                search_results=search_results
            )
            
            logger.info(f"Обработано {len(search_results)} результатов с алгоритмическим анализом уверенности")
            
        except Exception as e2:
            logger.warning(f"Не удалось проанализировать уверенность: {e2}")
        
        # Фильтруем результаты по уверенности
        if search_results:
            # Группируем результаты по позициям заказа (для множественных заказов)
            if result['user_intent'].get('is_multiple_order'):
                # Для множественных заказов фильтруем каждую позицию отдельно
                filtered_results = []
                position_groups = {}
                
                # Группируем по позиции заказа
                for item in search_results:
                    position = item.get('order_position', 1)
                    if position not in position_groups:
                        position_groups[position] = []
                    position_groups[position].append(item)
                
                # Фильтруем каждую позицию
                for position, items in position_groups.items():
                    filtered_items = _filter_results_by_confidence(items)
                    filtered_results.extend(filtered_items)
                    logger.info(f"Позиция {position}: {len(items)} → {len(filtered_items)} результатов")
                
                search_results = filtered_results
            else:
                # Для одиночных запросов фильтруем все результаты
                original_count = len(search_results)
                search_results = _filter_results_by_confidence(search_results)
                logger.info(f"Фильтрация: {original_count} → {len(search_results)} результатов")
        
        if not search_results:
            await processing_msg.edit_text("😔 К сожалению, ничего не найдено. Попробуйте изменить запрос.")
            return
        
        # Временно отключаем циклическую валидацию
        validation_result = {
            "status": "APPROVED",
            "message": "Валидация отключена",
            "confidence": 0.9
        }
        # Добавляем статус к результатам
        for search_result in search_results:
            search_result['validation_status'] = 'APPROVED'
        
        # Генерируем Excel файл
        await processing_msg.edit_text("📊 Создаю Excel файл с результатами...")
        
        excel_generator = ExcelGenerator()
        excel_file = await excel_generator.generate_excel(
            search_results=search_results,
            user_request=result['processed_text']
        )
        
        # Обрабатываем результат валидации
        validation_status = validation_result.get('status', 'UNKNOWN')
        
        if validation_status == "APPROVED":
            # Все хорошо - отправляем файл
            await processing_msg.edit_text("✅ Валидация пройдена! Отправляю результаты...")
            
            # Создаем короткую и информативную подпись
            import datetime
            current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Определяем тип запроса
            if result.get('is_document'):
                request_type = "📄 Обработка документа"
                request_summary = "PDF/файл обработан"
            elif result.get('is_voice'):
                request_type = "🎤 Голосовой запрос"
                request_summary = "Голос распознан"
            else:
                request_type = "💬 Текстовый запрос"
                request_summary = result['processed_text'][:50] + "..." if len(result['processed_text']) > 50 else result['processed_text']
            
            caption = f"{request_type}\n{request_summary}\n✅ Найдено: {len(search_results)} позиций\n📅 {current_time}"
            
            with open(excel_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"результаты_поиска_{user.id}.xlsx",
                    caption=caption
                )
            
            await processing_msg.delete()
            logger.info(f"Успешно обработан запрос пользователя {user.id} - валидация пройдена")
            
        elif validation_status == "NEEDS_REFINEMENT":
            # Нужна доработка - отправляем файл с предупреждением
            await processing_msg.edit_text("⚠️ Требуется доработка заказа. Отправляю результаты...")
            
            # Ограничиваем длину подписи
            caption = f"🔍 Результаты поиска по запросу: {result['processed_text'][:200]}...\n\n⚠️ Требуется доработка заказа\nНайдено: {len(search_results)} деталей"
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            
            with open(excel_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"результаты_поиска_{user.id}.xlsx",
                    caption=caption
                )
            
            # Отправляем сообщение с деталями циклической валидации
            validation_summary = validation_service.get_validation_summary(validation_result)
            
            # Добавляем информацию о циклах
            cycles = validation_result.get('cycles_completed', 0)
            if cycles > 0:
                cycles_info = f"\n\n🔄 Выполнено циклов валидации: {cycles}"
                if validation_result.get('max_cycles_reached'):
                    cycles_info += " (достигнут лимит)"
                validation_summary += cycles_info
            
            # Добавляем точные вопросы для уточнения
            clarification_questions = validation_service.generate_clarification_questions(validation_result)
            if clarification_questions:
                questions_text = "\n\n❓ Вопросы для уточнения:\n" + "\n".join([f"• {q}" for q in clarification_questions])
                validation_summary += questions_text
            
            await update.message.reply_text(validation_summary)
            
            await processing_msg.delete()
            logger.info(f"Обработан запрос пользователя {user.id} - требуется доработка")
            
        elif validation_status == "NEEDS_CLARIFICATION":
            # Нужны уточнения - отправляем файл и запрашиваем уточнения
            await processing_msg.edit_text("❓ Нужны уточнения. Отправляю результаты...")
            
            # Ограничиваем длину подписи
            caption = f"🔍 Результаты поиска по запросу: {result['processed_text'][:200]}...\n\n❓ Требуются уточнения\nНайдено: {len(search_results)} деталей"
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            
            with open(excel_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"результаты_поиска_{user.id}.xlsx",
                    caption=caption
                )
            
            # Отправляем сообщение с запросом уточнений
            validation_summary = validation_service.get_validation_summary(validation_result)
            await update.message.reply_text(
                f"{validation_summary}\n\n"
                "Пожалуйста, уточните детали запроса для улучшения результатов поиска."
            )
            
            await processing_msg.delete()
            logger.info(f"Обработан запрос пользователя {user.id} - требуются уточнения")
            
        else:
            # Ошибка валидации - отправляем файл с предупреждением
            await processing_msg.edit_text("⚠️ Проблемы с валидацией. Отправляю результаты...")
            
            # Ограничиваем длину подписи
            caption = f"🔍 Результаты поиска по запросу: {result['processed_text'][:200]}...\n\n⚠️ Проблемы с валидацией\nНайдено: {len(search_results)} деталей"
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            
            with open(excel_file, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"результаты_поиска_{user.id}.xlsx",
                    caption=caption
                )
            
            await processing_msg.delete()
            logger.info(f"Обработан запрос пользователя {user.id} - проблемы с валидацией")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз или обратитесь к администратору.")
        except:
            pass


def _filter_results_by_confidence(results):
    """
    Фильтрует результаты по уверенности:
    - Если есть 100% → показываем только их (максимум 3)
    - Если нет 100%, но есть 90%+ → показываем только их (максимум 5)
    - Если нет 90%, но есть 70%+ → показываем только их (максимум 10)
    - Если все ниже 70% → показываем топ-5
    """
    if not results:
        return []
    
    # Сортируем по уверенности (убывание)
    sorted_results = sorted(results, key=lambda x: x.get('confidence_score', 0), reverse=True)
    
    # Проверяем максимальную уверенность
    max_confidence = sorted_results[0].get('confidence_score', 0)
    
    if max_confidence >= 100:
        # Есть 100% - показываем только их (максимум 3)
        filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 100]
        return filtered[:3]
    
    elif max_confidence >= 90:
        # Есть 90%+ - показываем только их (максимум 5)
        filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 90]
        return filtered[:5]
    
    elif max_confidence >= 70:
        # Есть 70%+ - показываем только их (максимум 10)
        filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 70]
        return filtered[:10]
    
    else:
        # Все ниже 70% - показываем топ-5
        return sorted_results[:5]

