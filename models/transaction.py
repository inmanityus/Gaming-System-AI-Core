"""
Transaction Model
Represents payment and economy tracking.
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Transaction(Base):
    """
    Payment and economy tracking model.
    
    Tracks all financial transactions including:
    - Subscription payments (Stripe)
    - In-game purchases
    - Currency exchanges
    - Refunds
    
    Attributes:
        id: Unique transaction identifier
        player_id: Foreign key to players table
        transaction_type: Type of transaction (payment, purchase, refund)
        stripe_payment_intent_id: Stripe payment intent ID (if applicable)
        amount: Transaction amount
        currency: Currency code (USD, etc.)
        status: Transaction status (pending, completed, failed, refunded)
        description: Transaction description
        meta_data: Additional transaction meta_data as JSONB
        created_at: Transaction creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "transactions"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    player_id = Column(PGUUID(as_uuid=True), ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # payment, purchase, refund, exchange
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Financial details
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed, refunded
    
    # Description
    description = Column(String(500), nullable=True)
    
    # Additional meta_data (items purchased, subscription tier, etc.)
    meta_data = Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="transactions")
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "player_id": str(self.player_id),
            "transaction_type": self.transaction_type,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "description": self.description,
            "meta_data": self.meta_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_json(self) -> str:
        """Convert transaction to JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, player_id={self.player_id}, type={self.transaction_type}, amount={self.amount}, status={self.status})>"

