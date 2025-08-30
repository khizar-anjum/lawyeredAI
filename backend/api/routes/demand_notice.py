from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, PlainTextResponse
from backend.models.demand_notice import DemandNoticeRequest, DemandNoticeResponse
from backend.services.demand_notice_generator import DemandNoticeGenerator
from backend.services.honcho_service import get_memory_service
from backend.services.court_listener import CourtListenerService
from datetime import datetime

router = APIRouter(prefix="/demand-notice", tags=["demand-notice"])

async def get_court_service():
    service = CourtListenerService()
    try:
        yield service
    finally:
        await service.close()

@router.post("/generate", response_model=DemandNoticeResponse)
async def generate_demand_notice(
    request: DemandNoticeRequest,
    court_service: CourtListenerService = Depends(get_court_service)
):
    """Generate a NYC Consumer Dispute demand notice"""
    
    try:
        # Get recent conversation to understand the legal issue
        memory_service = get_memory_service()
        chat_history = await memory_service.get_chat_history(
            request.user_id, request.session_id, limit=20
        )
        
        # Extract key terms from conversation for case search
        conversation_text = " ".join([msg.content for msg in chat_history if msg.role == "user"])
        
        # Search for relevant NY cases
        relevant_cases = await court_service.search_cases(
            f"NYC consumer protection {request.issue_description} {conversation_text}", limit=3
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
        filename = f"nyc_demand_notice_{request.user_id}_{timestamp}.txt"
        
        return DemandNoticeResponse(
            notice_content=notice_content,
            case_references=case_references,
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating demand notice: {str(e)}")

@router.post("/generate-pdf")
async def generate_demand_notice_pdf(request: DemandNoticeRequest):
    """Generate and download demand notice as PDF"""
    try:
        # Generate the notice content first
        generator = DemandNoticeGenerator()
        notice_content = generator.generate_notice(request)
        
        # Generate PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nyc_demand_notice_{timestamp}.pdf"
        pdf_content = generator.generate_pdf(notice_content, filename)
        
        # Return PDF as download
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@router.post("/download-text")
async def download_demand_notice_text(request: DemandNoticeRequest):
    """Download demand notice as text file"""
    try:
        generator = DemandNoticeGenerator()
        notice_content = generator.generate_notice(request)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nyc_demand_notice_{timestamp}.txt"
        
        return Response(
            content=notice_content,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading notice: {str(e)}")