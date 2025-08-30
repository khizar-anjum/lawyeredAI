import httpx
from typing import Dict, Any, Optional
from backend.config.settings import settings

class FlowgladService:
    def __init__(self):
        self.secret_key = settings.flowglad_secret_key
        self.base_url = "https://api.flowglad.com"
        self.client = httpx.AsyncClient()
    
    async def create_checkout_session(
        self, 
        user_id: str, 
        user_email: str, 
        success_url: str, 
        cancel_url: str
    ) -> Optional[Dict[str, Any]]:
        """Create a Flowglad checkout session"""
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        # Create product first (or use existing product ID)
        product_data = {
            "name": "NYC Legal Demand Notice",
            "description": "Professional demand notice generation for consumer protection cases"
        }
        
        try:
            # Create or get product
            product_response = await self.client.post(
                f"{self.base_url}/products",
                json=product_data,
                headers=headers
            )
            
            if product_response.status_code not in [200, 201]:
                print(f"Error creating product: {product_response.text}")
                return None
            
            product = product_response.json()
            
            # Create price for the product
            price_data = {
                "product_id": product["id"],
                "unit_amount": int(settings.demand_notice_price * 100),  # Convert to cents
                "currency": "usd",
                "billing_scheme": "per_unit"
            }
            
            price_response = await self.client.post(
                f"{self.base_url}/prices",
                json=price_data,
                headers=headers
            )
            
            if price_response.status_code not in [200, 201]:
                print(f"Error creating price: {price_response.text}")
                return None
            
            price = price_response.json()
            
            # Create checkout session
            checkout_data = {
                "line_items": [{
                    "price_id": price["id"],
                    "quantity": 1
                }],
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "customer_email": user_email,
                "metadata": {
                    "user_id": user_id,
                    "product_type": "demand_notice"
                }
            }
            
            checkout_response = await self.client.post(
                f"{self.base_url}/checkout/sessions",
                json=checkout_data,
                headers=headers
            )
            
            if checkout_response.status_code not in [200, 201]:
                print(f"Error creating checkout session: {checkout_response.text}")
                return None
            
            return checkout_response.json()
            
        except Exception as e:
            print(f"Error in Flowglad service: {e}")
            return None
    
    async def verify_payment(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Verify payment status"""
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/checkout/sessions/{session_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error verifying payment: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()