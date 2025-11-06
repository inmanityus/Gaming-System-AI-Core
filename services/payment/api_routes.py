"""
PM-002/PM-003: Payment Service API Routes
FastAPI routes for checkout and coupon management.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel

from . import PaymentService, CouponService

router = APIRouter(prefix="/api/v1/payment", tags=["Payment"])

# Pydantic models
class CheckoutRequest(BaseModel):
    user_id: str
    tier: str  # 'basic', 'premium', 'vip'
    coupon_code: Optional[str] = None


class CheckoutResponse(BaseModel):
    session_id: str
    url: str
    tier: str
    user_id: str


class CreateCouponRequest(BaseModel):
    ambassador_id: Optional[str] = None
    code: Optional[str] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[int] = None
    currency: str = "usd"
    duration: str = "once"  # 'once', 'repeating', 'forever'
    max_redemptions: Optional[int] = None


class CouponResponse(BaseModel):
    coupon_id: str
    code: str
    discount_percent: Optional[float] = None
    discount_amount: Optional[int] = None
    currency: Optional[str] = None
    duration: str
    max_redemptions: Optional[int] = None
    times_redeemed: Optional[int] = None
    valid: Optional[bool] = None


# Dependencies
_payment_service: Optional[PaymentService] = None
_coupon_service: Optional[CouponService] = None

def get_payment_service() -> PaymentService:
    """Get or create payment service instance."""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service


def get_coupon_service() -> CouponService:
    """Get or create coupon service instance."""
    global _coupon_service
    if _coupon_service is None:
        _coupon_service = CouponService()
    return _coupon_service


# Routes
@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """PM-002: Create Stripe checkout session."""
    try:
        result = payment_service.create_checkout_session(
            user_id=request.user_id,
            tier=request.tier,
            coupon_code=request.coupon_code
        )
        return CheckoutResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """PM-002: Handle Stripe webhook events."""
    try:
        payload = await request.body()
        result = payment_service.handle_webhook(
            payload=payload.decode('utf-8'),
            signature=stripe_signature
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coupons", response_model=CouponResponse)
async def create_coupon(
    request: CreateCouponRequest,
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """PM-003: Create coupon (ambassador or promotional)."""
    try:
        if request.ambassador_id:
            # Create ambassador coupon
            result = coupon_service.create_ambassador_coupon(
                ambassador_id=request.ambassador_id,
                discount_percent=request.discount_percent or 20.0,
                duration=request.duration,
                max_redemptions=request.max_redemptions
            )
        elif request.code:
            # Create promotional coupon
            result = coupon_service.create_promotional_coupon(
                code=request.code,
                discount_percent=request.discount_percent,
                discount_amount=request.discount_amount,
                currency=request.currency,
                duration=request.duration,
                max_redemptions=request.max_redemptions
            )
        else:
            raise HTTPException(status_code=400, detail="Either ambassador_id or code must be provided")
        
        return CouponResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coupons/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: str,
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """PM-003: Get coupon information."""
    coupon = coupon_service.get_coupon(coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail=f"Coupon {coupon_id} not found")
    return CouponResponse(**coupon)


@router.get("/coupons", response_model=List[CouponResponse])
async def list_coupons(
    limit: int = 100,
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """PM-003: List all coupons."""
    coupons = coupon_service.list_coupons(limit=limit)
    return [CouponResponse(**coupon) for coupon in coupons]


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(
    coupon_id: str,
    coupon_service: CouponService = Depends(get_coupon_service)
):
    """PM-003: Delete coupon."""
    success = coupon_service.delete_coupon(coupon_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Coupon {coupon_id} not found")
    return {"success": True, "message": f"Coupon {coupon_id} deleted"}

