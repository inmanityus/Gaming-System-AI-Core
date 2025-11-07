# Payment Service Solution
**Service**: Stripe Integration & Monetization  
**Date**: January 29, 2025

---

## SERVICE OVERVIEW

Handles subscriptions, payment processing, coupon codes, and ambassador tracking using Stripe.

---

## ARCHITECTURE

### Technology Stack
- **Payment Provider**: Stripe
- **Backend**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL for subscription tracking
- **Webhooks**: Stripe webhook handlers

### Stripe Integration

**Checkout Session**:
```python
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_checkout_session(user_id, tier):
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': get_tier_price_id(tier),
            'quantity': 1,
        }],
        mode='subscription',
        success_url=f'https://game.com/success?session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url='https://game.com/cancel',
        metadata={
            'user_id': user_id,
            'tier': tier
        },
        allow_promotion_codes=True  # Enable coupon codes
    )
    return session
```

**Subscription Tiers**:
```python
TIER_PRICES = {
    'basic': 'price_basic_monthly',
    'premium': 'price_premium_monthly',
    'vip': 'price_vip_monthly'
}
```

### Coupon System

**Create Ambassador Coupon**:
```python
def create_ambassador_coupon(ambassador_id, discount_percent=20):
    coupon = stripe.Coupon.create(
        id=f'ambassador_{ambassador_id}',
        percent_off=discount_percent,
        duration='forever',  # or 'once', 'repeating'
        max_redemptions=100,
        metadata={
            'ambassador_id': ambassador_id
        }
    )
    return coupon
```

**Track Redemptions**:
```python
def handle_subscription_webhook(event):
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        coupon_code = session.get('discount', {}).get('coupon')
        
        if coupon_code and coupon_code.startswith('ambassador_'):
            ambassador_id = coupon_code.replace('ambassador_', '')
            track_referral(ambassador_id, session['customer'])
```

### Free Tier Enforcement

```python
def check_subscription_access(user_id):
    subscription = get_user_subscription(user_id)
    
    if not subscription or subscription.status != 'active':
        return FreeTierLimits()
    
    return SubscriptionTier(subscription.tier)
```

---

**Next**: Integrates with Game Engine Service for in-game subscription checks.

