import httpx
from typing import List, Optional
from backend.config.settings import settings
from backend.models.case import LegalCase

class CourtListenerService:
    def __init__(self):
        self.base_url = settings.courtlistener_base_url
        self.api_key = settings.courtlistener_api_key
        self.client = httpx.AsyncClient()
    
    async def search_cases(self, query: str, limit: int = 5) -> List[LegalCase]:
        """Search for NYC/NY state consumer protection cases"""
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Focus on NY state courts and federal courts covering NY
        ny_courts = [
            "ny",          # NY Court of Appeals
            "nyappdiv",    # NY Appellate Division
            "nysupct",     # NY Supreme Court
            "ca2",         # 2nd Circuit (covers NY)
            "nyed",        # Eastern District of NY
            "nynd",        # Northern District of NY  
            "nysd",        # Southern District of NY
            "nywd",        # Western District of NY
        ]
        
        params = {
            "q": f"consumer protection AND New York AND ({query})",
            "type": "o",  # Opinions
            "order_by": "score desc",
            "stat_Precedential": "on",
            "court": " ".join(ny_courts),
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search/",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            cases = []
            
            for result in data.get("results", [])[:limit]:
                case = LegalCase(
                    id=str(result.get("id", "")),
                    case_name=result.get("caseName", ""),
                    court=result.get("court", ""),
                    date_filed=result.get("dateFiled"),
                    snippet=result.get("snippet", ""),
                    url=f"https://www.courtlistener.com{result.get('absolute_url', '')}",
                    relevance_score=result.get("score")
                )
                cases.append(case)
            
            return cases
            
        except httpx.HTTPError as e:
            print(f"CourtListener API error: {e}")
            return []
    
    async def get_case_details(self, case_id: str) -> Optional[dict]:
        """Get detailed case information"""
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/opinions/{case_id}/",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            print(f"Error fetching case details: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()