import httpx
from typing import List, Optional, Dict
from backend.config.settings import settings
from backend.models.chat import ChatMessage
from backend.models.case import LegalCase

class AIService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.ai_model
        self.client = httpx.AsyncClient()
    
    def _create_system_prompt(self, cases: List[LegalCase]) -> str:
        """Create system prompt with relevant NYC/NY state case law"""
        case_context = ""
        if cases:
            case_context = "\n\nRELEVANT NEW YORK CASE LAW:\n"
            for case in cases:
                case_context += f"""
Case: {case.case_name}
Court: {case.court}
Summary: {case.snippet}
---
"""
        
        return f"""You are a specialized AI legal assistant focused on New York State consumer protection law, with particular expertise in NYC regulations.

IMPORTANT GUIDELINES:
1. Focus ONLY on New York State and NYC consumer protection laws
2. Reference NY General Business Law, NYC Consumer Protection Law, and relevant state statutes
3. Provide helpful legal information based on NY case law and consumer protection statutes
4. Always include disclaimers that this is not legal advice
5. Reference specific NY cases when relevant
6. Be clear, concise, and practical in your advice
7. If user's situation warrants it, suggest they may need a demand notice
8. Stay focused on consumer protection issues within NY jurisdiction

{case_context}

JURISDICTION: New York State & New York City
FOCUS: Consumer Protection Law, NYC Consumer Protection Law (Subchapter 2 of Chapter 5 of Title 6), NY General Business Law

Remember: Always remind users to consult with a qualified New York attorney for official legal advice."""

    async def generate_response(
        self, 
        user_message: str, 
        chat_history: List[ChatMessage], 
        relevant_cases: List[LegalCase]
    ) -> Dict:
        """Generate AI response with NY case law context"""
        
        messages = [
            {"role": "system", "content": self._create_system_prompt(relevant_cases)}
        ]
        
        # Add chat history
        for msg in chat_history[-5:]:  # Last 5 messages for context
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_message})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "NYC Legal Assistant AI"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1200
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # Check if response suggests demand notice
            demand_notice_keywords = [
                "demand notice", "demand letter", "formal demand", 
                "written notice", "legal notice", "demand for payment"
            ]
            can_generate_demand = any(keyword in ai_response.lower() for keyword in demand_notice_keywords)
            
            return {
                "response": ai_response,
                "can_generate_demand_notice": can_generate_demand,
                "usage": result.get("usage", {})
            }
            
        except httpx.HTTPError as e:
            print(f"OpenRouter API error: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again later.",
                "can_generate_demand_notice": False
            }
    
    async def close(self):
        await self.client.aclose()