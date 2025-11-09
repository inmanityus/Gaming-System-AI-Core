"""
The Weaver's Loom - Story Teller Portal

Secure communication portal for creator-Story Teller collaboration.

Components:
- Threaded Dialogue (chat)
- Pattern Board (visual whiteboard)
- Inspiration Codex (content repository)
- Version History (session archives)
"""

__version__ = "1.0.0"

from .story_teller_portal import (
    WeaversLoom,
    MessageType,
    NodeType,
    DialogueMessage,
    PatternBoardNode,
    InspirationContent,
)

__all__ = [
    "WeaversLoom",
    "MessageType",
    "NodeType",
    "DialogueMessage",
    "PatternBoardNode",
    "InspirationContent",
]

