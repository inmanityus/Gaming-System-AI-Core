"""
Conflict Resolver - Optimistic Locking and Conflict Resolution
Handles concurrent update conflicts using version-based optimistic locking.
"""

import asyncio
from typing import Callable, Optional
from uuid import UUID

from .state_operations import ConflictResolutionError, StateOperations


class ConflictResolver:
    """
    Resolves conflicts using optimistic locking with exponential backoff retry.
    """
    
    def __init__(self, max_retries: int = 3, initial_backoff: float = 0.1):
        """
        Initialize conflict resolver.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff delay in seconds (exponential backoff)
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.state_ops = StateOperations()
    
    async def update_with_retry(
        self,
        state_id: UUID,
        update_fn: Callable,
        *args,
        **kwargs
    ) -> dict:
        """
        Execute update with automatic conflict resolution retry.
        
        Args:
            state_id: Game state UUID
            update_fn: Update function that takes (state_id, expected_version, ...)
            *args: Additional positional arguments for update_fn
            **kwargs: Additional keyword arguments for update_fn
        
        Returns:
            Updated game state dict
        
        Raises:
            ConflictResolutionError: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Get current state to get version
                current_state = await self.state_ops.get_game_state(state_id)
                if not current_state:
                    raise ValueError(f"Game state {state_id} not found")
                
                expected_version = current_state["version"]
                
                # Attempt update
                result = await update_fn(state_id, expected_version, *args, **kwargs)
                return result
                
            except ConflictResolutionError as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    backoff_time = self.initial_backoff * (2 ** attempt)
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    # All retries exhausted
                    raise ConflictResolutionError(
                        f"Failed to update game state {state_id} after {self.max_retries} attempts: {str(e)}"
                    ) from e
        
        # Should never reach here, but for type safety
        if last_error:
            raise last_error
        raise ConflictResolutionError(f"Unexpected error updating game state {state_id}")

