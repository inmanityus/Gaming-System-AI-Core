"""
API Routes - RESTful endpoints for Story Teller Service.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from .story_manager import StoryManager, StoryNode
from .narrative_generator import NarrativeGenerator
from .choice_processor import ChoiceProcessor, ChoiceValidationError
from .story_branching import StoryBranching, StoryBranch


# Request/Response Models
class StoryNodeCreate(BaseModel):
    """Request schema for creating a story node."""
    node_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    narrative_content: Optional[str] = Field(None, max_length=5000)
    choices: List[Dict[str, Any]] = Field(default_factory=list)
    prerequisites: Optional[Dict[str, Any]] = Field(None)
    consequences: Optional[Dict[str, Any]] = Field(None)


class StoryNodeUpdate(BaseModel):
    """Request schema for updating a story node."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    narrative_content: Optional[str] = Field(None, max_length=5000)
    choices: Optional[List[Dict[str, Any]]] = Field(None)
    status: Optional[str] = Field(None, regex="^(active|completed|deleted)$")
    prerequisites: Optional[Dict[str, Any]] = Field(None)
    consequences: Optional[Dict[str, Any]] = Field(None)


class ChoiceRequest(BaseModel):
    """Request schema for processing a choice."""
    choice_id: str = Field(..., min_length=1, max_length=100)


class NarrativeGenerateRequest(BaseModel):
    """Request schema for generating narrative content."""
    node_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    context_hints: Optional[Dict[str, Any]] = Field(None)


class StoryBranchCreate(BaseModel):
    """Request schema for creating a story branch."""
    to_node_id: UUID
    conditions: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(1.0, ge=0.0, le=10.0)


# Initialize services
story_manager = StoryManager()
narrative_generator = NarrativeGenerator()
choice_processor = ChoiceProcessor()
story_branching = StoryBranching()

# Create router
router = APIRouter(prefix="/story", tags=["story"])


# Story Node Endpoints
@router.post("/nodes", response_model=Dict[str, Any])
async def create_story_node(
    player_id: UUID,
    request: StoryNodeCreate,
) -> Dict[str, Any]:
    """Create a new story node."""
    try:
        node = await story_manager.create_story_node(
            player_id=player_id,
            node_type=request.node_type,
            title=request.title,
            description=request.description,
            narrative_content=request.narrative_content or "",
            choices=request.choices,
            prerequisites=request.prerequisites,
            consequences=request.consequences,
        )
        return {
            "success": True,
            "node": node.to_dict(),
            "message": "Story node created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create story node: {str(e)}"
        )


@router.get("/nodes/{node_id}", response_model=Dict[str, Any])
async def get_story_node(node_id: UUID) -> Dict[str, Any]:
    """Get a story node by ID."""
    try:
        node = await story_manager.get_story_node(node_id)
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story node not found"
            )
        
        return {
            "success": True,
            "node": node.to_dict(),
            "message": "Story node retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get story node: {str(e)}"
        )


@router.get("/players/{player_id}/nodes", response_model=Dict[str, Any])
async def get_player_story_nodes(
    player_id: UUID,
    status: Optional[str] = None,
    node_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get all story nodes for a player."""
    try:
        nodes = await story_manager.get_player_story_nodes(
            player_id=player_id,
            status=status,
            node_type=node_type,
        )
        
        return {
            "success": True,
            "nodes": [node.to_dict() for node in nodes],
            "count": len(nodes),
            "message": "Player story nodes retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get player story nodes: {str(e)}"
        )


@router.put("/nodes/{node_id}", response_model=Dict[str, Any])
async def update_story_node(
    node_id: UUID,
    request: StoryNodeUpdate,
) -> Dict[str, Any]:
    """Update a story node."""
    try:
        node = await story_manager.update_story_node(
            node_id=node_id,
            title=request.title,
            description=request.description,
            narrative_content=request.narrative_content,
            choices=request.choices,
            status=request.status,
            prerequisites=request.prerequisites,
            consequences=request.consequences,
        )
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story node not found"
            )
        
        return {
            "success": True,
            "node": node.to_dict(),
            "message": "Story node updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update story node: {str(e)}"
        )


@router.delete("/nodes/{node_id}", response_model=Dict[str, Any])
async def delete_story_node(node_id: UUID) -> Dict[str, Any]:
    """Delete a story node (soft delete)."""
    try:
        success = await story_manager.delete_story_node(node_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Story node not found"
            )
        
        return {
            "success": True,
            "message": "Story node deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete story node: {str(e)}"
        )


# Narrative Generation Endpoints
@router.post("/generate", response_model=Dict[str, Any])
async def generate_narrative(
    player_id: UUID,
    request: NarrativeGenerateRequest,
) -> Dict[str, Any]:
    """Generate narrative content for a story node."""
    try:
        content = await narrative_generator.generate_narrative(
            player_id=player_id,
            node_type=request.node_type,
            title=request.title,
            description=request.description,
            context_hints=request.context_hints,
        )
        
        return {
            "success": True,
            "content": content,
            "message": "Narrative content generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate narrative: {str(e)}"
        )


# Choice Processing Endpoints
@router.post("/nodes/{node_id}/choices/validate", response_model=Dict[str, Any])
async def validate_choice(
    player_id: UUID,
    node_id: UUID,
    request: ChoiceRequest,
) -> Dict[str, Any]:
    """Validate a player choice."""
    try:
        is_valid, error = await choice_processor.validate_choice(
            player_id=player_id,
            node_id=node_id,
            choice_id=request.choice_id,
        )
        
        return {
            "success": is_valid,
            "valid": is_valid,
            "error": error if not is_valid else None,
            "message": "Choice validation completed"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate choice: {str(e)}"
        )


@router.post("/nodes/{node_id}/choices/process", response_model=Dict[str, Any])
async def process_choice(
    player_id: UUID,
    node_id: UUID,
    request: ChoiceRequest,
) -> Dict[str, Any]:
    """Process a player choice and apply consequences."""
    try:
        result = await choice_processor.process_choice(
            player_id=player_id,
            node_id=node_id,
            choice_id=request.choice_id,
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process choice: {str(e)}"
        )


# Story Branching Endpoints
@router.post("/branches", response_model=Dict[str, Any])
async def create_story_branch(
    from_node_id: UUID,
    request: StoryBranchCreate,
) -> Dict[str, Any]:
    """Create a new story branch."""
    try:
        branch = await story_branching.create_branch(
            from_node_id=from_node_id,
            to_node_id=request.to_node_id,
            conditions=request.conditions,
            weight=request.weight,
        )
        
        return {
            "success": True,
            "branch": branch.to_dict(),
            "message": "Story branch created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create story branch: {str(e)}"
        )


@router.get("/nodes/{node_id}/branches", response_model=Dict[str, Any])
async def get_available_branches(
    player_id: UUID,
    node_id: UUID,
) -> Dict[str, Any]:
    """Get available story branches from a node."""
    try:
        branches = await story_branching.get_available_branches(
            player_id=player_id,
            from_node_id=node_id,
        )
        
        return {
            "success": True,
            "branches": [branch.to_dict() for branch in branches],
            "count": len(branches),
            "message": "Available branches retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available branches: {str(e)}"
        )


@router.get("/nodes/{node_id}/next", response_model=Dict[str, Any])
async def get_next_node(
    player_id: UUID,
    node_id: UUID,
) -> Dict[str, Any]:
    """Get the next story node based on available branches."""
    try:
        next_node_id = await story_branching.select_next_node(
            player_id=player_id,
            from_node_id=node_id,
        )
        
        if not next_node_id:
            return {
                "success": True,
                "next_node_id": None,
                "message": "No available branches from this node"
            }
        
        return {
            "success": True,
            "next_node_id": str(next_node_id),
            "message": "Next node selected successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next node: {str(e)}"
        )


@router.get("/players/{player_id}/path", response_model=Dict[str, Any])
async def get_story_path(
    player_id: UUID,
    start_node_id: UUID,
    max_depth: int = 10,
) -> Dict[str, Any]:
    """Get a complete story path from a starting node."""
    try:
        path = await story_branching.get_story_path(
            player_id=player_id,
            start_node_id=start_node_id,
            max_depth=max_depth,
        )
        
        return {
            "success": True,
            "path": [str(node_id) for node_id in path],
            "length": len(path),
            "message": "Story path generated successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get story path: {str(e)}"
        )


# Health Check
@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "service": "story_teller",
        "message": "Story Teller service is running"
    }
