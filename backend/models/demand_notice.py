from pydantic import BaseModel
from typing import Optional

class DemandNoticeRequest(BaseModel):
    user_id: str
    session_id: str
    
    # Complainant info
    complainant_name: str
    complainant_address: str
    complainant_contact: str
    
    # Respondent info
    respondent_name: str
    respondent_address: str
    
    # Issue details
    issue_description: str
    amount_claimed: Optional[str] = None
    resolution_sought: str

class DemandNoticeResponse(BaseModel):
    notice_content: str
    case_references: list[str]
    filename: str