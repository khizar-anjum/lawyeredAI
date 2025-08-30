import httpx
from typing import List, Optional
from backend.config.settings import settings
from backend.models.chat import ChatMessage

class HonchoService:
    def __init__(self):
        self.api_key = settings.honcho_api_key
        self.app_id = settings.honcho_app_id
        self.base_url = settings.honcho_base_url
        self.client = httpx.AsyncClient()
    
    async def create_session(self, user_id: str) -> str:
        """Create a new chat session for a user"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "user_id": user_id,
            "metadata": {"type": "legal_consultation"}
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/apps/{self.app_id}/users/{user_id}/sessions",
                json=data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()["id"]
            
        except httpx.HTTPError as e:
            print(f"Error creating Honcho session: {e}")
            return f"session_{user_id}"
    
    async def add_message(self, user_id: str, session_id: str, message: ChatMessage):
        """Add a message to the conversation history"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "content": message.content,
            "is_user": message.role == "user",
            "metadata": {"timestamp": str(message.timestamp)}
        }
        
        try:
            await self.client.post(
                f"{self.base_url}/apps/{self.app_id}/users/{user_id}/sessions/{session_id}/messages",
                json=data,
                headers=headers
            )
        except httpx.HTTPError as e:
            print(f"Error adding message to Honcho: {e}")
    
    async def get_chat_history(self, user_id: str, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get recent chat history for context"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/apps/{self.app_id}/users/{user_id}/sessions/{session_id}/messages",
                headers=headers,
                params={"page_size": limit, "reverse": True}
            )
            response.raise_for_status()
            
            messages = []
            for msg in response.json().get("items", []):
                role = "user" if msg["is_user"] else "assistant"
                messages.append(ChatMessage(
                    role=role,
                    content=msg["content"],
                    timestamp=msg.get("created_at")
                ))
            
            return list(reversed(messages))
            
        except httpx.HTTPError as e:
            print(f"Error getting chat history: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()