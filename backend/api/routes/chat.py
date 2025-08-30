from fastapi import APIRouter, HTTPException, Depends
from backend.models.chat import ChatRequest, ChatResponse, ChatMessage
from backend.services.ai_service import AIService
from backend.services.court_listener import CourtListenerService
from backend.services.honcho_service import HonchoService
from datetime import datetime
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])

# Dependency injection
async def get_ai_service():
    service = AIService()
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

async def get_honcho_service():
    service = HonchoService()
    try:
        yield service
    finally:
        await service.close()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    ai_service: AIService = Depends(get_ai_service),
    court_service: CourtListenerService = Depends(get_court_service),
    honcho_service: HonchoService = Depends(get_honcho_service)
):
    """Process user message and return AI response with relevant NY case law"""
    
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = await honcho_service.create_session(request.user_id)
        
        # Search for relevant NY cases (done in background, not shown to user)
        relevant_cases = await court_service.search_cases(request.message, limit=3)
        
        # Get chat history for context
        chat_history = await honcho_service.get_chat_history(
            request.user_id, session_id, limit=10
        )
        
        # Generate AI response
        ai_result = await ai_service.generate_response(
            request.message, chat_history, relevant_cases
        )
        
        # Save user message to history
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=datetime.now()
        )
        await honcho_service.add_message(request.user_id, session_id, user_message)
        
        # Save AI response to history
        ai_message = ChatMessage(
            role="assistant",
            content=ai_result["response"],
            timestamp=datetime.now()
        )
        await honcho_service.add_message(request.user_id, session_id, ai_message)
        
        # Return response (no relevant_cases in response since we removed sidebar)
        return ChatResponse(
            response=ai_result["response"],
            session_id=session_id,
            relevant_cases=None,  # Remove sidebar data
            can_generate_demand_notice=ai_result["can_generate_demand_notice"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/history/{user_id}/{session_id}")
async def get_chat_history(
    user_id: str,
    session_id: str,
    honcho_service: HonchoService = Depends(get_honcho_service)
):
    """Get chat history for a session"""
    try:
        history = await honcho_service.get_chat_history(user_id, session_id, limit=50)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")