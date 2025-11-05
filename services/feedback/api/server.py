"""
Feedback System API Server
==========================

FastAPI server for feedback collection endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from ..feedback_collector import FeedbackCollector, FeedbackCategory, FeedbackType

app = FastAPI(title="Feedback System API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize feedback collector
feedback_collector = FeedbackCollector()


class QuickFeedbackRequest(BaseModel):
    """Request for quick feedback."""
    category: str
    rating: Optional[int] = None  # 1-5
    emoji: Optional[str] = None


class DetailedFeedbackRequest(BaseModel):
    """Request for detailed feedback."""
    category: str
    text: str
    attachments: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None


@app.post("/v1/feedback/quick")
async def submit_quick_feedback(request: QuickFeedbackRequest):
    """Submit quick feedback (emoji, rating)."""
    try:
        category = FeedbackCategory(request.category)
        feedback = feedback_collector.collect_quick_feedback(
            category=category,
            rating=request.rating,
            emoji=request.emoji,
        )
        return {
            "success": True,
            "feedback_id": str(feedback.timestamp),
            "message": "Feedback submitted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@app.post("/v1/feedback/detailed")
async def submit_detailed_feedback(request: DetailedFeedbackRequest):
    """Submit detailed feedback (text, attachments)."""
    try:
        category = FeedbackCategory(request.category)
        feedback = feedback_collector.collect_detailed_feedback(
            category=category,
            text=request.text,
            attachments=request.attachments,
            context=request.context,
        )
        return {
            "success": True,
            "feedback_id": str(feedback.timestamp),
            "message": "Feedback submitted successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category: {e}")


@app.get("/v1/feedback/pending")
async def get_pending_feedback():
    """Get pending feedback (for processing)."""
    pending = feedback_collector.get_pending_feedback()
    return {
        "count": len(pending),
        "feedback": [f.to_dict() for f in pending],
    }


