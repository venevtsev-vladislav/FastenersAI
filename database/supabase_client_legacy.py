"""
Supabase client адаптированный под существующую схему
"""

import logging
import json
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, DB_TABLES

logger = logging.getLogger(__name__)

class SupabaseClientLegacy:
    """Supabase client для работы с существующей схемой"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Supabase client"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.warning("Supabase credentials not configured")
                return
            
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Test connection
            response = self.client.table('user_requests').select('count').limit(1).execute()
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            self.client = None
    
    async def create_request(self, chat_id: str, user_id: str, source: str, 
                           storage_uri: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """Create a new request record using existing user_requests table"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            request_data = {
                'user_id': user_id,
                'chat_id': chat_id,
                'request_type': source,
                'original_content': f"Request from {source}",
                'processed_text': '',
                'user_intent': json.dumps({'source': source, 'storage_uri': storage_uri}),
                'created_at': 'now()'
            }
            
            response = self.client.table(DB_TABLES['user_requests']).insert(request_data).execute()
            
            if response.data:
                request_id = str(response.data[0]['id'])
                logger.info(f"Created request {request_id}")
                return request_id
            else:
                raise Exception("Failed to create request")
                
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            raise
    
    async def create_request_line(self, request_id: str, line_no: int, raw_text: str, 
                                normalized_text: Optional[str] = None) -> int:
        """Create a request line record - using user_requests for now"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # For now, we'll store line data in the user_intent JSON
            # In a real implementation, you'd want separate tables
            line_data = {
                'user_id': '0',  # Placeholder
                'chat_id': request_id,
                'request_type': 'line',
                'original_content': raw_text,
                'processed_text': normalized_text or raw_text,
                'user_intent': json.dumps({
                    'line_no': line_no,
                    'raw_text': raw_text,
                    'normalized_text': normalized_text or raw_text
                }),
                'created_at': 'now()'
            }
            
            response = self.client.table(DB_TABLES['user_requests']).insert(line_data).execute()
            
            if response.data:
                line_id = response.data[0]['id']
                logger.info(f"Created request line {line_id}")
                return line_id
            else:
                raise Exception("Failed to create request line")
                
        except Exception as e:
            logger.error(f"Error creating request line: {e}")
            raise
    
    async def add_candidate(self, request_line_id: int, ku: str, name: str, 
                          score: float, pack_qty: Optional[float] = None, 
                          price: Optional[float] = None, explanation: Optional[str] = None,
                          source: str = 'rules') -> int:
        """Add a candidate - using aliases table for now"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            candidate_data = {
                'alias': f"candidate_{request_line_id}_{ku}",
                'maps_to': json.dumps({
                    'ku': ku,
                    'name': name,
                    'score': score,
                    'pack_qty': pack_qty,
                    'price': price,
                    'explanation': explanation,
                    'source': source
                }),
                'confidence': score,
                'notes': f"Candidate for line {request_line_id}",
                'created_at': 'now()'
            }
            
            response = self.client.table(DB_TABLES['aliases']).insert(candidate_data).execute()
            
            if response.data:
                candidate_id = response.data[0]['id']
                logger.debug(f"Added candidate {candidate_id} for line {request_line_id}")
                return candidate_id
            else:
                raise Exception("Failed to add candidate")
                
        except Exception as e:
            logger.error(f"Error adding candidate: {e}")
            raise
    
    async def update_request_line(self, line_id: int, chosen_ku: Optional[str] = None,
                                qty_packs: Optional[float] = None, qty_units: Optional[float] = None,
                                price: Optional[float] = None, total: Optional[float] = None,
                                status: str = 'ok', chosen_method: str = 'rules') -> bool:
        """Update a request line with final results"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Update the user_intent JSON with results
            response = self.client.table(DB_TABLES['user_requests']).select('user_intent').eq('id', line_id).execute()
            
            if response.data:
                current_intent = json.loads(response.data[0]['user_intent'])
                current_intent.update({
                    'chosen_ku': chosen_ku,
                    'qty_packs': qty_packs,
                    'qty_units': qty_units,
                    'price': price,
                    'total': total,
                    'status': status,
                    'chosen_method': chosen_method
                })
                
                update_data = {
                    'user_intent': json.dumps(current_intent, ensure_ascii=False)
                }
                
                response = self.client.table(DB_TABLES['user_requests']).update(update_data).eq('id', line_id).execute()
                
                if response.data:
                    logger.info(f"Updated request line {line_id}")
                    return True
                else:
                    raise Exception("Failed to update request line")
            else:
                raise Exception("Request line not found")
                
        except Exception as e:
            logger.error(f"Error updating request line: {e}")
            raise
    
    async def update_request_status(self, request_id: str, status: str) -> bool:
        """Update request status"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['user_requests']).update({'processed_text': status}).eq('id', request_id).execute()
            
            if response.data:
                logger.info(f"Updated request {request_id} status to {status}")
                return True
            else:
                raise Exception("Failed to update request status")
                
        except Exception as e:
            logger.error(f"Error updating request status: {e}")
            raise
    
    async def get_request_lines(self, request_id: str) -> List[Dict]:
        """Get all request lines for a request"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['user_requests']).select('*').eq('chat_id', request_id).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting request lines: {e}")
            return []
    
    async def get_candidates(self, request_line_id: int) -> List[Dict]:
        """Get all candidates for a request line"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['aliases']).select('*').ilike('alias', f'candidate_{request_line_id}_%').execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting candidates: {e}")
            return []
    
    async def search_items_by_alias(self, alias: str) -> List[Dict]:
        """Search items by exact alias match"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['aliases']).select('*').eq('alias', alias.lower()).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching by alias: {e}")
            return []
    
    async def search_items_fuzzy(self, query: str, limit: int = 10) -> List[Dict]:
        """Fuzzy search items by name and specs"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Search in parts_catalog table
            response = self.client.table(DB_TABLES['parts_catalog']).select('*').ilike('name', f'%{query}%').limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []
    
    async def get_item_by_ku(self, ku: str) -> Optional[Dict]:
        """Get item by KU"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['parts_catalog']).select('*').eq('sku', ku).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error getting item by KU: {e}")
            return None
    
    async def get_all_aliases(self) -> List[Dict]:
        """Get all aliases for local processing"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table(DB_TABLES['aliases']).select('*').execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting aliases: {e}")
            return []

# Global instance
_supabase_client_legacy: Optional[SupabaseClientLegacy] = None

async def get_supabase_client_legacy() -> SupabaseClientLegacy:
    """Get global Supabase client instance"""
    global _supabase_client_legacy
    if _supabase_client_legacy is None:
        _supabase_client_legacy = SupabaseClientLegacy()
    return _supabase_client_legacy
