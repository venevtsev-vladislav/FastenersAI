"""
Сервис для работы с OpenAI Assistant
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

class OpenAIAssistantService:
    """Сервис для работы с OpenAI Assistant"""
    
    def __init__(self):
        # Создаем клиент с заголовками для v2 API
        self.client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        self.assistant_id = "asst_HjGYPyU5L7uTWZA8q4mHUhGA"  # Новый Assistant ID
        self.thread_id = None
        
        # Проверяем что заголовки установлены
        logger.info(f"OpenAI клиент создан с заголовками: {self.client.default_headers}")
        
    async def create_thread(self) -> str:
        """Создает новый thread для разговора"""
        try:
            thread = await self.client.beta.threads.create(
                extra_headers={"OpenAI-Beta": "assistants=v2"}
            )
            self.thread_id = thread.id
            logger.info(f"Создан новый thread: {self.thread_id}")
            return self.thread_id
        except Exception as e:
            logger.error(f"Ошибка при создании thread: {e}")
            raise
    
    async def process_user_request(self, user_message: str, thread_id: str = None) -> Dict:
        """Обрабатывает запрос пользователя через Assistant"""
        try:
            # Используем существующий thread или создаем новый
            if not thread_id:
                thread_id = await self.create_thread()
            else:
                self.thread_id = thread_id
            
            # Отправляем сообщение пользователя
            await self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=user_message,
                extra_headers={"OpenAI-Beta": "assistants=v2"}
            )
            
                    # Запускаем Assistant
        run = await self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
            
            # Ждем завершения
            run = await self._wait_for_run_completion(self.thread_id, run.id)
            
            if run.status == "completed":
                # Получаем ответ
                messages = await self.client.beta.threads.messages.list(
                    thread_id=self.thread_id
                )
                
                # Ищем последний ответ Assistant
                for message in messages.data:
                    if message.role == "assistant":
                        content = message.content[0].text.value
                        return await self._parse_assistant_response(content)
            
            elif run.status == "failed":
                logger.error(f"Assistant failed: {run.last_error}")
                raise Exception(f"Assistant failed: {run.last_error}")
            
            else:
                logger.warning(f"Unexpected run status: {run.status}")
                raise Exception(f"Unexpected run status: {run.status}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке через Assistant: {e}")
            raise
    
    async def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: int = 60) -> any:
        """Ждет завершения выполнения Assistant"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
            
            # Проверяем timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Assistant execution timeout")
            
            # Ждем перед следующей проверкой
            await asyncio.sleep(1)
    
    async def _parse_assistant_response(self, content: str) -> Dict:
        """Парсит ответ Assistant в структурированный формат"""
        try:
            # Ищем JSON в ответе
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("JSON не найден в ответе Assistant")
            
            json_str = content[json_start:json_end]
            result = json.loads(json_str)
            
            # Валидируем структуру
            if 'rows' not in result:
                raise ValueError("Отсутствует поле 'rows' в ответе")
            
            logger.info(f"Успешно распарсен ответ Assistant: {len(result['rows'])} строк")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.error(f"Содержимое ответа: {content}")
            raise ValueError(f"Неверный формат JSON: {e}")
        except Exception as e:
            logger.error(f"Ошибка при парсинге ответа Assistant: {e}")
            raise
    
    async def validate_with_supabase(self, assistant_response: Dict) -> Dict:
        """Валидирует ответ Assistant через Supabase"""
        try:
            from database.supabase_client import _supabase_client
            
            if not _supabase_client:
                logger.warning("Supabase не доступен для валидации")
                return assistant_response
            
            validated_rows = []
            
            for row in assistant_response.get('rows', []):
                validated_row = await self._validate_single_row(row)
                validated_rows.append(validated_row)
            
            validated_response = assistant_response.copy()
            validated_response['rows'] = validated_rows
            
            logger.info(f"Валидировано {len(validated_rows)} строк через Supabase")
            return validated_response
            
        except Exception as e:
            logger.error(f"Ошибка при валидации через Supabase: {e}")
            return assistant_response
    
    async def _validate_single_row(self, row: Dict) -> Dict:
        """Валидирует одну строку через Supabase"""
        try:
            from database.supabase_client import _supabase_client
            
            sku = row.get('SKU', '')
            if not sku:
                return row
            
            # Проверяем существование SKU в каталоге
            response = _supabase_client.table('parts_catalog')\
                .select('*')\
                .eq('sku', sku)\
                .limit(1)\
                .execute()
            
            if not response.data:
                # SKU не найден - очищаем поля
                logger.warning(f"SKU {sku} не найден в каталоге")
                row['SKU'] = ''
                row['Наименование'] = ''
                row['Фасовка_шт_уп'] = 0
                row['Вероятность'] = max(0.1, row.get('Вероятность', 0.5) - 0.3)
                row['Вопрос_пользователю'] = f"SKU {sku} не найден в каталоге. Проверьте правильность артикула."
            
            return row
            
        except Exception as e:
            logger.error(f"Ошибка при валидации строки: {e}")
            return row
    
    async def update_vector_store(self, aliases_data: List[Dict] = None):
        """Обновляет Vector Store новыми данными"""
        try:
            # Если не переданы данные, загружаем из Supabase
            if not aliases_data:
                from database.supabase_client import _supabase_client
                if _supabase_client:
                    response = _supabase_client.table('aliases').select('*').execute()
                    aliases_data = response.data if response.data else []
            
            if not aliases_data:
                logger.warning("Нет данных для обновления Vector Store")
                return
            
            # Создаем файл с алиасами для загрузки в Assistant
            aliases_file = await self._create_aliases_file(aliases_data)
            
            # Загружаем файл в Assistant
            file = await self.client.files.create(
                file=aliases_file,
                purpose="assistants"
            )
            
            # Обновляем Assistant с новым файлом
            await self.client.beta.assistants.update(
                assistant_id=self.assistant_id,
                file_ids=[file.id]
            )
            
            logger.info(f"Vector Store обновлен файлом: {file.id}")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении Vector Store: {e}")
            raise
    
    async def _create_aliases_file(self, aliases_data: List[Dict]) -> str:
        """Создает временный файл с алиасами"""
        import tempfile
        import os
        
        # Создаем временный файл
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        
        try:
            # Записываем данные в формате JSONL
            for alias in aliases_data:
                temp_file.write(json.dumps(alias, ensure_ascii=False) + '\n')
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            temp_file.close()
            os.unlink(temp_file.name)
            raise e
