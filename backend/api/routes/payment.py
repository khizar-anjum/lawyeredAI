from fastapi import APIRouter, HTTPException, Depends
from backend.services.payment_service import FlowgladService
from backend.services.auth_service import AuthService
from backend.api.routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/payment", tags=["payment"])

class PaymentRequest(BaseModel):
    success_url: str = "http://localhost:8000/payment/success"
    cancel_url: str = "http://localhost:8000/payment/cancel"

async def get_payment_service():
    service = FlowgladService()
    try:
        yield service
    finally:
        await service.close()

async def get_auth_service():
    service = AuthService()
    try:
        yield service
    finally:
        pass

@router.post("/create-checkout")
async def create_checkout_session(
    request: PaymentRequest,
    current_user: dict = Depends(get_current_user),
    payment_service: FlowgladService = Depends(get_payment_service)
):
    """Create Flowglad checkout session for demand notice"""
    
    try:
        session = await payment_service.create_checkout_session(
            user_id=current_user["user_id"],
            user_email=current_user["email"],
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create payment session")
        
        return {
            "checkout_url": session.get("url"),
            "session_id": session.get("id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")

@router.get("/verify/{session_id}")
async def verify_payment(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    payment_service: FlowgladService = Depends(get_payment_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify payment and return success status"""
    
    try:
        payment_data = await payment_service.verify_payment(session_id)
        
        if not payment_data:
            raise HTTPException(status_code=404, detail="Payment session not found")
        
        # Log payment
        await auth_service.log_payment(current_user["user_id"], {
            "session_id": session_id,
            "amount": 0.0,  # $0 for now
            "currency": "usd",
            "status": payment_data.get("status", "unknown"),
            "metadata": {"product": "demand_notice"}
        })
        
        return {
            "payment_status": payment_data.get("status"),
            "paid": payment_data.get("status") == "complete",
            "session_id": session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")