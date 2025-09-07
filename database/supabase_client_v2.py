"""
Enhanced Supabase client for the new FastenersAI architecture
Based on the comprehensive specification
"""

import logging
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class SupabaseClientV2:
    """Enhanced Supabase client for the new architecture"""
    
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
            logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            self.client = None
    
    async def create_request(self, chat_id: str, user_id: str, source: str, 
                           storage_uri: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """Create a new request record"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            request_data = {
                'chat_id': chat_id,
                'user_id': user_id,
                'source': source,
                'storage_uri': storage_uri,
                'tenant_id': tenant_id,
                'status': 'pending'
            }
            
            response = self.client.table('requests').insert(request_data).execute()
            
            if response.data:
                request_id = response.data[0]['id']
                logger.info(f"Created request {request_id}")
                return request_id
            else:
                raise Exception("Failed to create request")
                
        except Exception as e:
            logger.error(f"Error creating request: {e}")
            raise
    
    async def create_request_line(self, request_id: str, line_no: int, raw_text: str, 
                                normalized_text: Optional[str] = None) -> int:
        """Create a request line record"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            line_data = {
                'request_id': request_id,
                'line_no': line_no,
                'raw_text': raw_text,
                'normalized_text': normalized_text or raw_text,
                'status': 'pending'
            }
            
            response = self.client.table('request_lines').insert(line_data).execute()
            
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
        """Add a candidate for a request line"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            candidate_data = {
                'request_line_id': request_line_id,
                'ku': ku,
                'name': name,
                'score': score,
                'pack_qty': pack_qty,
                'price': price,
                'explanation': explanation,
                'source': source
            }
            
            response = self.client.table('candidates').insert(candidate_data).execute()
            
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
            
            update_data = {
                'status': status,
                'chosen_method': chosen_method
            }
            
            if chosen_ku is not None:
                update_data['chosen_ku'] = chosen_ku
            if qty_packs is not None:
                update_data['qty_packs'] = qty_packs
            if qty_units is not None:
                update_data['qty_units'] = qty_units
            if price is not None:
                update_data['price'] = price
            if total is not None:
                update_data['total'] = total
            
            response = self.client.table('request_lines').update(update_data).eq('id', line_id).execute()
            
            if response.data:
                logger.info(f"Updated request line {line_id}")
                return True
            else:
                raise Exception("Failed to update request line")
                
        except Exception as e:
            logger.error(f"Error updating request line: {e}")
            raise
    
    async def update_request_status(self, request_id: str, status: str) -> bool:
        """Update request status"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table('requests').update({'status': status}).eq('id', request_id).execute()
            
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
            
            response = self.client.table('request_lines').select('*').eq('request_id', request_id).order('line_no').execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting request lines: {e}")
            return []
    
    async def get_candidates(self, request_line_id: int) -> List[Dict]:
        """Get all candidates for a request line"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table('candidates').select('*').eq('request_line_id', request_line_id).order('score', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting candidates: {e}")
            return []
    
    async def search_items_by_alias(self, alias: str) -> List[Dict]:
        """Search items by exact alias match"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table('sku_aliases').select('*, items(*)').eq('alias', alias.lower()).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error searching by alias: {e}")
            return []
    
    async def search_items_fuzzy(self, query: str, limit: int = 10) -> List[Dict]:
        """Fuzzy search items by name and specs"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            # Search in items table
            response = self.client.table('items').select('*').ilike('name', f'%{query}%').limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error in fuzzy search: {e}")
            return []
    
    async def get_item_by_ku(self, ku: str) -> Optional[Dict]:
        """Get item by KU"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table('items').select('*').eq('ku', ku).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            logger.error(f"Error getting item by KU: {e}")
            return None
    
    async def get_all_aliases(self) -> List[Dict]:
        """Get all aliases for local processing"""
        try:
            if not self.client:
                raise Exception("Supabase client not initialized")
            
            response = self.client.table('sku_aliases').select('*').execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error getting aliases: {e}")
            return []
    
    async def create_tables(self):
        """Create database tables using SQL file"""
        try:
            if not self.client:
                logger.warning("Supabase client not initialized, skipping table creation")
                return
            
            # Read and execute SQL file
            with open('database/create_tables.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                try:
                    self.client.rpc('exec_sql', {'sql': statement}).execute()
                    logger.debug(f"Executed SQL statement: {statement[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to execute statement: {e}")
            
            logger.info("Database tables created/verified successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

# Global instance
_supabase_client_v2: Optional[SupabaseClientV2] = None

async def get_supabase_client() -> SupabaseClientV2:
    """Get global Supabase client instance"""
    global _supabase_client_v2
    if _supabase_client_v2 is None:
        _supabase_client_v2 = SupabaseClientV2()
    return _supabase_client_v2
