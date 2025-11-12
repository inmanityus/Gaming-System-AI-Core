"""
Feedback Collector
==================

Collects player feedback through various triggers and methods.
"""

import logging
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackCategory(Enum):
    """Feedback categories."""
    GAMEPLAY = "gameplay"
    LANGUAGE_QUALITY = "language_quality"
    AUDIO_VIDEO = "audio_video"
    PERFORMANCE = "performance"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    ACCESSIBILITY = "accessibility"
    CONTENT = "content"


class FeedbackType(Enum):
    """Types of feedback."""
    QUICK = "quick"  # Emoji, star rating, single-click
    DETAILED = "detailed"  # Text input, attachments
    CONTEXTUAL = "contextual"  # Context-aware feedback


@dataclass
class Feedback:
    """Feedback data structure."""
    category: FeedbackCategory
    feedback_type: FeedbackType
    rating: Optional[int] = None  # 1-5 stars
    emoji: Optional[str] = None  # 👍 👎 😊 😞
    text: Optional[str] = None
    attachments: List[str] = field(default_factory=list)  # Screenshots, videos
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary."""
        data = asdict(self)
        data["category"] = self.category.value
        data["feedback_type"] = self.feedback_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class FeedbackCollector:
    """Collects player feedback."""
    
    def __init__(self, storage_path: str = "data/feedback"):
        """Initialize feedback collector."""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._feedback_queue: List[Feedback] = []
    
    def collect_quick_feedback(
        self,
        category: FeedbackCategory,
        rating: Optional[int] = None,
        emoji: Optional[str] = None
    ) -> Feedback:
        """
        Collect quick feedback (emoji, rating).
        
        Args:
            category: Feedback category
            rating: 1-5 star rating
            emoji: Emoji reaction
            
        Returns:
            Feedback object
        """
        feedback = Feedback(
            category=category,
            feedback_type=FeedbackType.QUICK,
            rating=rating,
            emoji=emoji,
        )
        
        self._queue_feedback(feedback)
        return feedback
    
    def collect_detailed_feedback(
        self,
        category: FeedbackCategory,
        text: str,
        attachments: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """
        Collect detailed feedback (text, attachments).
        
        Args:
            category: Feedback category
            text: Feedback text
            attachments: Optional screenshot/video paths
            context: Optional context data
            
        Returns:
            Feedback object
        """
        feedback = Feedback(
            category=category,
            feedback_type=FeedbackType.DETAILED,
            text=text,
            attachments=attachments or [],
            context=context or {},
        )
        
        self._queue_feedback(feedback)
        return feedback
    
    def collect_contextual_feedback(
        self,
        context: Dict[str, Any]
    ) -> Feedback:
        """
        Collect contextual feedback (context-aware).
        
        Args:
            context: Context data including category, rating, etc.
            
        Returns:
            Feedback object
        """
        category = FeedbackCategory(context.get("category", "gameplay"))
        feedback_type = FeedbackType(context.get("type", "quick"))
        
        feedback = Feedback(
            category=category,
            feedback_type=feedback_type,
            rating=context.get("rating"),
            emoji=context.get("emoji"),
            text=context.get("text"),
            attachments=context.get("attachments", []),
            context=context,
        )
        
        self._queue_feedback(feedback)
        return feedback
    
    def _queue_feedback(self, feedback: Feedback):
        """Queue feedback for processing."""
        self._feedback_queue.append(feedback)
        
        # Save to file (immediate persistence)
        self._save_feedback(feedback)
        
        # Log feedback
        logger.info(f"Feedback collected: {feedback.category.value} - {feedback.feedback_type.value}")
    
    def _save_feedback(self, feedback: Feedback):
        """Save feedback to file."""
        try:
            # Create filename with timestamp
            timestamp_str = feedback.timestamp.strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp_str}_{feedback.category.value}.json"
            filepath = self.storage_path / filename
            
            # Save feedback
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(feedback.to_dict(), f, indent=2)
            
            logger.debug(f"Feedback saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
    
    def get_pending_feedback(self) -> List[Feedback]:
        """Get pending feedback from queue."""
        return self._feedback_queue.copy()
    
    def clear_queue(self):
        """Clear feedback queue."""
        self._feedback_queue.clear()






