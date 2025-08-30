from supabase import create_client, Client
from backend.config.settings import settings
from typing import Optional, Dict, Any
import json

class AuthService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            # Verify the JWT token
            response = self.supabase.auth.get_user(token)
            
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata
                }
            return None
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Supabase"""
        try:
            response = self.supabase.table('profiles').select('*').eq('id', user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return None
    
    async def create_user_profile(self, user_data: Dict[str, Any]) -> bool:
        """Create user profile in Supabase"""
        try:
            response = self.supabase.table('profiles').insert(user_data).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    async def log_payment(self, user_id: str, payment_data: Dict[str, Any]) -> bool:
        """Log payment transaction"""
        try:
            payment_log = {
                "user_id": user_id,
                "amount": payment_data.get("amount", 0),
                "currency": payment_data.get("currency", "usd"),
                "status": payment_data.get("status", "pending"),
                "flowglad_session_id": payment_data.get("session_id"),
                "product_type": "demand_notice",
                "metadata": json.dumps(payment_data.get("metadata", {}))
            }
            
            response = self.supabase.table('payments').insert(payment_log).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error logging payment: {e}")
            return False