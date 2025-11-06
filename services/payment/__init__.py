"""
Payment Service - Stripe Integration
PM-001: Stripe Account Setup
PM-002: Checkout System
PM-003: Coupons System
"""

import os
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Subscription tier price IDs (configure in Stripe dashboard)
TIER_PRICES = {
    'basic': os.getenv("STRIPE_PRICE_BASIC", "price_basic_monthly"),
    'premium': os.getenv("STRIPE_PRICE_PREMIUM", "price_premium_monthly"),
    'vip': os.getenv("STRIPE_PRICE_VIP", "price_vip_monthly")
}

class PaymentService:
    """Stripe payment service integration."""
    
    def __init__(self):
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not set in environment")
    
    def create_checkout_session(self, user_id: str, tier: str, coupon_code: Optional[str] = None) -> dict:
        """
        PM-002: Create Stripe checkout session for subscription.
        
        Args:
            user_id: User ID (Steam ID or internal ID)
            tier: Subscription tier ('basic', 'premium', 'vip')
            coupon_code: Optional coupon code
        
        Returns:
            Checkout session dictionary with URL
        """
        if tier not in TIER_PRICES:
            raise ValueError(f"Invalid tier: {tier}")
        
        price_id = TIER_PRICES[tier]
        
        # Build line items
        line_items = [{
            'price': price_id,
            'quantity': 1,
        }]
        
        # Create checkout session
        session_params = {
            'payment_method_types': ['card'],
            'line_items': line_items,
            'mode': 'subscription',
            'success_url': f'{os.getenv("PAYMENT_SUCCESS_URL", "https://game.com/success")}?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': os.getenv("PAYMENT_CANCEL_URL", "https://game.com/cancel"),
            'metadata': {
                'user_id': user_id,
                'tier': tier
            },
            'allow_promotion_codes': True,  # Enable coupon codes
        }
        
        # Add coupon code if provided
        if coupon_code:
            session_params['discounts'] = [{
                'coupon': coupon_code
            }]
        
        session = stripe.checkout.Session.create(**session_params)
        
        return {
            'session_id': session.id,
            'url': session.url,
            'tier': tier,
            'user_id': user_id
        }
    
    def handle_webhook(self, payload: str, signature: str) -> dict:
        """
        PM-002: Handle Stripe webhook events.
        
        Args:
            payload: Webhook payload (raw bytes or string)
            signature: Webhook signature
        
        Returns:
            Processed event data
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not set")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
        except ValueError as e:
            raise ValueError(f"Invalid payload: {e}")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {e}")
        
        # Handle different event types
        event_type = event['type']
        event_data = event['data']['object']
        
        result = {
            'event_type': event_type,
            'processed': False,
            'data': {}
        }
        
        if event_type == 'checkout.session.completed':
            # Subscription checkout completed
            session = event_data
            user_id = session.get('metadata', {}).get('user_id')
            tier = session.get('metadata', {}).get('tier')
            
            # Track coupon usage if present
            if 'discount' in session and session['discount']:
                coupon_code = session['discount'].get('coupon')
                if coupon_code and coupon_code.startswith('ambassador_'):
                    ambassador_id = coupon_code.replace('ambassador_', '')
                    # TODO: Track referral
                    result['data']['ambassador_id'] = ambassador_id
            
            result['data'] = {
                'user_id': user_id,
                'tier': tier,
                'session_id': session.get('id')
            }
            result['processed'] = True
            
        elif event_type == 'customer.subscription.created':
            # New subscription created
            subscription = event_data
            result['data'] = {
                'subscription_id': subscription.get('id'),
                'customer_id': subscription.get('customer'),
                'status': subscription.get('status')
            }
            result['processed'] = True
            
        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            subscription = event_data
            result['data'] = {
                'subscription_id': subscription.get('id'),
                'status': subscription.get('status')
            }
            result['processed'] = True
            
        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            subscription = event_data
            result['data'] = {
                'subscription_id': subscription.get('id'),
                'status': 'cancelled'
            }
            result['processed'] = True
        
        return result


class CouponService:
    """
    PM-003: Coupon management service.
    Handles ambassador coupons and promotional codes.
    """
    
    def __init__(self):
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not set in environment")
    
    def create_ambassador_coupon(
        self,
        ambassador_id: str,
        discount_percent: float = 20.0,
        duration: str = 'forever',
        max_redemptions: Optional[int] = 100
    ) -> dict:
        """
        PM-003: Create ambassador coupon code.
        
        Args:
            ambassador_id: Ambassador user ID
            discount_percent: Discount percentage (0-100)
            duration: 'once', 'repeating', or 'forever'
            max_redemptions: Maximum number of redemptions
        
        Returns:
            Coupon data
        """
        coupon_id = f'ambassador_{ambassador_id}'
        
        coupon_params = {
            'id': coupon_id,
            'percent_off': discount_percent,
            'duration': duration,
            'metadata': {
                'ambassador_id': ambassador_id,
                'created_at': datetime.now().isoformat()
            }
        }
        
        if max_redemptions:
            coupon_params['max_redemptions'] = max_redemptions
        
        coupon = stripe.Coupon.create(**coupon_params)
        
        return {
            'coupon_id': coupon.id,
            'code': coupon_id,  # Use coupon ID as code
            'discount_percent': coupon.percent_off,
            'duration': coupon.duration,
            'max_redemptions': coupon.max_redemptions,
            'ambassador_id': ambassador_id
        }
    
    def create_promotional_coupon(
        self,
        code: str,
        discount_percent: Optional[float] = None,
        discount_amount: Optional[int] = None,
        currency: str = 'usd',
        duration: str = 'once',
        valid_until: Optional[datetime] = None,
        max_redemptions: Optional[int] = None
    ) -> dict:
        """
        PM-003: Create promotional coupon code.
        
        Args:
            code: Coupon code (e.g., "SUMMER2025")
            discount_percent: Discount percentage (0-100)
            discount_amount: Discount amount in cents (if not using percent)
            currency: Currency code
            duration: 'once', 'repeating', or 'forever'
            valid_until: Expiration date
            max_redemptions: Maximum redemptions
        
        Returns:
            Coupon data
        """
        if discount_percent is None and discount_amount is None:
            raise ValueError("Either discount_percent or discount_amount must be provided")
        
        coupon_params = {
            'id': code,
            'duration': duration,
            'metadata': {
                'created_at': datetime.now().isoformat()
            }
        }
        
        if discount_percent is not None:
            coupon_params['percent_off'] = discount_percent
        else:
            coupon_params['amount_off'] = discount_amount
            coupon_params['currency'] = currency
        
        if valid_until:
            coupon_params['redeem_by'] = int(valid_until.timestamp())
        
        if max_redemptions:
            coupon_params['max_redemptions'] = max_redemptions
        
        coupon = stripe.Coupon.create(**coupon_params)
        
        return {
            'coupon_id': coupon.id,
            'code': code,
            'discount_percent': coupon.percent_off,
            'discount_amount': coupon.amount_off,
            'currency': coupon.currency,
            'duration': coupon.duration,
            'max_redemptions': coupon.max_redemptions,
            'valid_until': datetime.fromtimestamp(coupon.redeem_by) if coupon.redeem_by else None
        }
    
    def get_coupon(self, coupon_id: str) -> Optional[dict]:
        """
        PM-003: Get coupon information.
        
        Args:
            coupon_id: Coupon ID or code
        
        Returns:
            Coupon data or None if not found
        """
        try:
            coupon = stripe.Coupon.retrieve(coupon_id)
            return {
                'coupon_id': coupon.id,
                'discount_percent': coupon.percent_off,
                'discount_amount': coupon.amount_off,
                'currency': coupon.currency,
                'duration': coupon.duration,
                'max_redemptions': coupon.max_redemptions,
                'times_redeemed': coupon.times_redeemed,
                'valid': coupon.valid,
                'metadata': coupon.metadata
            }
        except stripe.error.InvalidRequestError:
            return None
    
    def list_coupons(self, limit: int = 100) -> List[dict]:
        """
        PM-003: List all coupons.
        
        Args:
            limit: Maximum number of coupons to return
        
        Returns:
            List of coupon data
        """
        coupons = stripe.Coupon.list(limit=limit)
        
        return [
            {
                'coupon_id': coupon.id,
                'discount_percent': coupon.percent_off,
                'discount_amount': coupon.amount_off,
                'currency': coupon.currency,
                'duration': coupon.duration,
                'max_redemptions': coupon.max_redemptions,
                'times_redeemed': coupon.times_redeemed,
                'valid': coupon.valid
            }
            for coupon in coupons.data
        ]
    
    def delete_coupon(self, coupon_id: str) -> bool:
        """
        PM-003: Delete coupon.
        
        Args:
            coupon_id: Coupon ID
        
        Returns:
            True if deleted successfully
        """
        try:
            stripe.Coupon.delete(coupon_id)
            return True
        except stripe.error.InvalidRequestError:
            return False

