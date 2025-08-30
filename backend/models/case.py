from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class LegalCase(BaseModel):
    id: str
    case_name: str
    court: str
    date_filed: Optional[date]
    snippet: str
    url: str
    relevance_score: Optional[float] = None

class CaseSearchRequest(BaseModel):
    query: str
    limit: int = 10
    court_type: Optional[str] = None