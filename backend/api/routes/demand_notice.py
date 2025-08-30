from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from backend.models.demand_notice import DemandNoticeRequest, DemandNoticeResponse
from backend.services.demand_notice_generator import DemandNoticeGenerator
from backend.services.honcho_service import HonchoService
from backend.services.court_listener import CourtListenerService
from datetime import datetime

router = APIRouter(prefix="/demand-notice", tags=["demand-notice"])

async def get_honcho_service():
    service = HonchoService()
    try:
        yield service
    finally:
        await service.close()

async def get_court_service():
    service = CourtListenerService()
    try:
        yield service
    finally:
        await service.close()

@router.post("/generate", response_model=DemandNoticeResponse)
async def generate_demand_notice(
    request: DemandNoticeRequest,
    honcho_service: HonchoService = Depends(get_honcho_service),
    court_service: CourtListenerService = Depends(get_court_service)
):
    """Generate a demand notice based on conversation context"""
    
    try:
        # Get recent conversation to understand the legal issue
        chat_history = await honcho_service.get_chat_history(
            request.user_id, request.session_id, limit=20
        )
        
        # Extract key terms from conversation for case search
        conversation_text = " ".join([msg.content for msg in chat_history if msg.role == "user"])
        
        # Search for relevant cases
        relevant_cases = await court_service.search_cases(
            f"{request.issue_description} {conversation_text}", limit=3
        )
        
        # Prepare case references
        case_references = [
            f"{case.case_name} ({case.court})"
            for case in relevant_cases
        ]
        
        # Generate the notice
        generator = DemandNoticeGenerator()
        notice_content = generator.generate_notice(request, case_references)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"demand_notice_{request.user_id}_{timestamp}.txt"
        
        return DemandNoticeResponse(
            notice_content=notice_content,
            case_references=case_references,
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating demand notice: {str(e)}")

@router.post("/download")
async def download_demand_notice(request: DemandNoticeRequest):
    """Download demand notice as text file"""
    try:
        # This would normally generate the notice and return as file
        # For now, return as plain text response
        generator = DemandNoticeGenerator()
        notice_content = generator.generate_notice(request, [])
        
        return PlainTextResponse(
            content=notice_content,
            headers={
                "Content-Disposition": f"attachment; filename=demand_notice_{request.user_id}.txt"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading notice: {str(e)}")