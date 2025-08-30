import asyncio
import json
from typing import Dict, Any, List
from backend.services.court_listener import CourtListenerService
from backend.services.ai_service import AIService

class MCPServer:
    """Model Context Protocol Server for Legal Assistant"""
    
    def __init__(self):
        self.court_service = CourtListenerService()
        self.ai_service = AIService()
        self.tools = {
            "search_cases": self.search_cases,
            "get_case_details": self.get_case_details,
            "generate_legal_advice": self.generate_legal_advice
        }
    
    async def search_cases(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """MCP tool for searching legal cases"""
        try:
            cases = await self.court_service.search_cases(query, limit)
            return {
                "success": True,
                "data": [case.dict() for case in cases]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_case_details(self, case_id: str) -> Dict[str, Any]:
        """MCP tool for getting case details"""
        try:
            details = await self.court_service.get_case_details(case_id)
            return {
                "success": True,
                "data": details
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_legal_advice(
        self, 
        query: str, 
        context: List[Dict] = None
    ) -> Dict[str, Any]:
        """MCP tool for generating legal advice"""
        try:
            # This would integrate with the AI service
            # For now, return a structured response
            return {
                "success": True,
                "data": {
                    "advice": "This is AI-generated legal information. Consult an attorney for official advice.",
                    "relevant_statutes": [],
                    "case_law": context or []
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        tool_name = request.get("tool")
        params = request.get("params", {})
        
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            result = await self.tools[tool_name](**params)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """Clean up resources"""
        await self.court_service.close()
        await self.ai_service.close()