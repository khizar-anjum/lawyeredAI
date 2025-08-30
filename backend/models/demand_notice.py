from pydantic import BaseModel
from typing import Optional, List

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
    
    # Additional NYC template fields
    incident_date: Optional[str] = None
    item_service: Optional[str] = None
    contact_method: Optional[str] = "email / phone"

class DemandNoticeResponse(BaseModel):
    notice_content: str
    case_references: List[str]
    filename: str

class DemandNoticePDFResponse(BaseModel):
    pdf_content: bytes
    filename: str
    content_type: str = "application/pdf"