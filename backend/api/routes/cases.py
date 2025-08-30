from fastapi import APIRouter, HTTPException, Depends
from backend.models.case import CaseSearchRequest, LegalCase
from backend.services.court_listener import CourtListenerService
from typing import List

router = APIRouter(prefix="/cases", tags=["cases"])

async def get_court_service():
    service = CourtListenerService()
    try:
        yield service
    finally:
        await service.close()

@router.post("/search", response_model=List[LegalCase])
async def search_cases(
    request: CaseSearchRequest,
    court_service: CourtListenerService = Depends(get_court_service)
):
    """Search for legal cases"""
    try:
        cases = await court_service.search_cases(request.query, request.limit)
        return cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching cases: {str(e)}")

@router.get("/{case_id}")
async def get_case_details(
    case_id: str,
    court_service: CourtListenerService = Depends(get_court_service)
):
    """Get detailed case information"""
    try:
        case_details = await court_service.get_case_details(case_id)
        if not case_details:
            raise HTTPException(status_code=404, detail="Case not found")
        return case_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching case: {str(e)}")