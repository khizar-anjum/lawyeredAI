"""
Fixed Honcho Service Implementation
Based on the latest Honcho v2 API using the peer-based model
"""

from typing import List, Optional
from backend.config.settings import settings
from backend.models.chat import ChatMessage
from datetime import datetime

try:
    from honcho import Honcho
    HONCHO_AVAILABLE = True
except ImportError:
    HONCHO_AVAILABLE = False
    print("Warning: honcho-ai package not installed. Using fallback memory service.")

class HonchoService:
    def __init__(self):
        self.client = None
        self.workspace_id = "legal-assistant-workspace"
        
        if HONCHO_AVAILABLE:
            try:
                self.client = Honcho(
                    api_key=settings.honcho_api_key if hasattr(settings, 'honcho_api_key') else None,
                    environment="demo"  # Use demo for now, change to "production" with real API key
                )
                print("✅ Honcho client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Honcho client: {e}")
                self.client = None
        
        # Fallback in-memory storage
        self.fallback_sessions = {}
        self.fallback_messages = {}
    
    async def create_session(self, user_id: str) -> str:
        """Create a new chat session for a user"""
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        if self.client:
            try:
                # Create a peer for the user
                user_peer = self.client.peer(user_id)
                
                # Create a session
                session = self.client.session(session_id)
                
                # Add the user peer to the session
                session.add_peers([user_peer])
                
                print(f"✅ Created Honcho session: {session_id}")
                return session_id
                
            except Exception as e:
                print(f"❌ Error creating Honcho session: {e}")
                # Fall back to local storage
                self.fallback_sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now()
                }
                return session_id
        
        # Fallback: store locally
        self.fallback_sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now()
        }
        return session_id
    
    async def add_message(self, user_id: str, session_id: str, message: ChatMessage):
        """Add a message to the conversation history"""
        if self.client:
            try:
                # Get the user peer and session
                user_peer = self.client.peer(user_id)
                session = self.client.session(session_id)
                
                # Create message content
                if message.role == "user":
                    # Add user message
                    session.add_messages([user_peer.message(message.content)])
                else:
                    # Add assistant message (create assistant peer if needed)
                    assistant_peer = self.client.peer("assistant")
                    session.add_messages([assistant_peer.message(message.content)])
                
                print(f"✅ Added message to Honcho session: {session_id}")
                return
                
            except Exception as e:
                print(f"❌ Error adding message to Honcho: {e}")
                # Fall back to local storage
        
        # Fallback: store locally
        if session_id not in self.fallback_messages:
            self.fallback_messages[session_id] = []
        
        self.fallback_messages[session_id].append({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp or datetime.now()
        })
    
    async def get_chat_history(self, user_id: str, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get recent chat history for context"""
        if self.client:
            try:
                session = self.client.session(session_id)
                
                # Get recent messages from the session
                messages = session.get_messages()
                
                # Convert to ChatMessage objects
                chat_history = []
                for msg in messages:
                    # Determine role based on peer
                    role = "assistant" if msg.peer_id == "assistant" else "user"
                    
                    chat_history.append(ChatMessage(
                        role=role,
                        content=msg.content,
                        timestamp=msg.created_at if hasattr(msg, 'created_at') else None
                    ))
                
                # Return most recent messages
                return chat_history[-limit:] if len(chat_history) > limit else chat_history
                
            except Exception as e:
                print(f"❌ Error getting chat history from Honcho: {e}")
                # Fall back to local storage
        
        # Fallback: get from local storage
        if session_id in self.fallback_messages:
            messages = self.fallback_messages[session_id][-limit:]
            return [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                )
                for msg in messages
            ]
        
        return []
    
    async def get_user_context(self, user_id: str, query: str = "") -> str:
        """Get context about a user using Honcho's dialectic API"""
        if self.client:
            try:
                user_peer = self.client.peer(user_id)
                
                # Use dialectic API to understand user better
                if query:
                    response = user_peer.chat(query)
                else:
                    response = user_peer.chat("What are this user's communication preferences and needs?")
                
                return response
                
            except Exception as e:
                print(f"❌ Error getting user context from Honcho: {e}")
                return "No additional context available."
        
        return "No additional context available."
    
    async def close(self):
        """Clean up resources"""
        # Honcho client doesn't need explicit closing
        pass


# Alternative simple memory service if Honcho is not available
class SimpleMemoryService:
    """Fallback memory service when Honcho is not available"""
    
    def __init__(self):
        self.sessions = {}
        self.messages = {}
    
    async def create_session(self, user_id: str) -> str:
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now()
        }
        return session_id
    
    async def add_message(self, user_id: str, session_id: str, message: ChatMessage):
        if session_id not in self.messages:
            self.messages[session_id] = []
        
        self.messages[session_id].append({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp or datetime.now()
        })
    
    async def get_chat_history(self, user_id: str, session_id: str, limit: int = 10) -> List[ChatMessage]:
        if session_id in self.messages:
            messages = self.messages[session_id][-limit:]
            return [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg["timestamp"]
                )
                for msg in messages
            ]
        return []
    
    async def get_user_context(self, user_id: str, query: str = "") -> str:
        return "Using simple memory service - no advanced context available."
    
    async def close(self):
        pass


# Export the appropriate service
def get_memory_service():
    """Factory function to get the appropriate memory service"""
    if HONCHO_AVAILABLE:
        return HonchoService()
    else:
        return SimpleMemoryService()