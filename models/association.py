"""
Association tables for many-to-many relationships.
"""

from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base

# Player-Augmentation many-to-many relationship
player_augmentations = Table(
    'player_augmentations',
    Base.metadata,
    Column('player_id', PGUUID(as_uuid=True), ForeignKey('players.id', ondelete='CASCADE'), primary_key=True),
    Column('augmentation_id', PGUUID(as_uuid=True), ForeignKey('augmentations.id', ondelete='CASCADE'), primary_key=True),
)

