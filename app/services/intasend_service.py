# backend/app/services/intasend_service.py
import httpx
import os
import uuid

INTASEND_MOCK_MODE = os.getenv("INTASEND_MOCK_MODE", "false").lower() == "true"
INTASEND_SECRET_KEY = os.getenv("INTASEND_SECRET_KEY")
INTASEND_BASE_URL = os.getenv("INTASEND_BASE_URL", "https://sandbox.intasend.com/api/v1/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

PLAN_PRICES = {
    "premium": 999,   
    "family": 1999    
}

async def create_checkout_link(user_id: str, user_email: str, plan: str) -> dict:
    if plan not in PLAN_PRICES:
        raise ValueError("Invalid subscription plan")

    amount = PLAN_PRICES[plan]
    api_ref = f"tailstory_sub_{user_id}_{uuid.uuid4().hex[:8]}"
    
    # --- MOCK MODE: Simulate successful IntaSend response ---
    if INTASEND_MOCK_MODE:
        print("⚠️ MOCK MODE ACTIVE: Simulating successful IntaSend checkout generation...")
        # Return a fake URL that redirects to your success page for testing
        mock_url = f"{FRONTEND_URL}/subscription/success?plan={plan}&ref={api_ref}&mock=true"
        return {"checkout_url": mock_url, "api_ref": api_ref}
    # ---------------------------------------------------------

    payload = {
        "first_name": "TailStory",
        "last_name": "User",
        "email": user_email,
        "amount": amount,
        "currency": "KES", 
        "api_ref": api_ref,
        "comment": f"TailStory {plan.capitalize()} Subscription",
        "redirect_url": f"{FRONTEND_URL}/subscription/success?plan={plan}&ref={api_ref}",
    }

    headers = {
        "Authorization": f"Bearer {INTASEND_SECRET_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INTASEND_BASE_URL}checkout/",
                json=payload,
                headers=headers,
                timeout=15.0
            )
            
            if response.status_code != 200:
                print(f"❌ IntaSend API Error ({response.status_code}): {response.text}")
                
            response.raise_for_status()
            data = response.json()
            
            checkout_url = data.get("url") 
            
            return {"checkout_url": checkout_url, "api_ref": api_ref}
            
    except httpx.HTTPStatusError as e:
        raise Exception(f"IntaSend API rejected the request: {e.response.text}")
    except Exception as e:
        print(f"❌ Python Exception: {str(e)}")
        raise Exception("An unexpected error occurred with the payment gateway")