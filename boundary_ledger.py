"""
Boundary Ledger - Core State Management

The missing primitive: persistent authority constraints.
"""

from typing import Optional, Dict, List
from boundary_types import Boundary, RingLevel, Action, create_boundary
import time

class BoundaryLedger:
    """
    Persistent storage for authority boundaries.
    
    Implements ring-based hierarchy with bitwise AND for merging.
    """
    
    def __init__(self):
        # conversation_id → {ring_level → boundary}
        self._boundaries: Dict[str, Dict[RingLevel, Boundary]] = {}
        self._events: Dict[str, List[dict]] = {}
    
    def establish(
        self,
        conversation_id: str,
        boundary: Boundary,
        turn_number: int
    ) -> bool:
        """
        Establish boundary.
        
        Returns:
            True if established, False if conflict
        """
        if conversation_id not in self._boundaries:
            self._boundaries[conversation_id] = {}
        
        rings = self._boundaries[conversation_id]
        
        # Check for conflicts with higher rings
        for ring, existing in rings.items():
            if ring.value < boundary.ring_level.value:
                # Higher ring exists - check conflict
                if (existing.allowed_actions & boundary.allowed_actions) == Action.NONE:
                    return False  # Incompatible
        
        # No conflict - establish
        rings[boundary.ring_level] = boundary
        
        self._log_event(conversation_id, "establish", boundary, turn_number)
        
        return True
    
    def get(self, conversation_id: str) -> Optional[Boundary]:
        """
        Get effective boundary (merged across all rings).
        
        Returns:
            Merged boundary or None
        """
        if conversation_id not in self._boundaries:
            return None
        
        boundaries = list(self._boundaries[conversation_id].values())
        
        if not boundaries:
            return None
        
        if len(boundaries) == 1:
            return boundaries[0]
        
        # Merge via bitwise AND
        return self._merge(boundaries)
    
    def _merge(self, boundaries: List[Boundary]) -> Boundary:
        """Merge boundaries using bitwise AND."""
        effective_actions = Action.ALL
        
        for b in boundaries:
            effective_actions &= b.allowed_actions
        
        highest_ring = min(b.ring_level for b in boundaries)
        
        return Boundary(
            type=boundaries[0].type,
            ring_level=highest_ring,
            allowed_actions=effective_actions,
            established_at_turn=min(b.established_at_turn for b in boundaries),
            established_by="merged",
            instruction="Merged boundary",
            timestamp=time.time()
        )
    
    def release(
        self,
        conversation_id: str,
        ring_level: RingLevel,
        authority: str,
        turn_number: int
    ) -> bool:
        """
        Release boundary at ring level.
        
        Returns:
            True if released, False if insufficient authority
        """
        if conversation_id not in self._boundaries:
            return False
        
        rings = self._boundaries[conversation_id]
        
        if ring_level not in rings:
            return False
        
        boundary = rings[ring_level]
        
        # Check authority
        if not boundary.can_be_released_by(authority):
            return False
        
        # Release
        del rings[ring_level]
        
        self._log_event(conversation_id, "release", boundary, turn_number)
        
        return True
    
    def can_perform(self, conversation_id: str, action: Action) -> bool:
        """Check if action is allowed."""
        boundary = self.get(conversation_id)
        
        if not boundary:
            return True  # No boundaries
        
        return boundary.allows(action)
    
    def get_audit_trail(self, conversation_id: str) -> List[dict]:
        """Get audit trail."""
        return self._events.get(conversation_id, [])
    
    def _log_event(
        self,
        conversation_id: str,
        event_type: str,
        boundary: Boundary,
        turn_number: int
    ):
        """Log event."""
        if conversation_id not in self._events:
            self._events[conversation_id] = []
        
        self._events[conversation_id].append({
            "event": event_type,
            "turn": turn_number,
            "boundary": boundary.type.value,
            "ring": boundary.ring_level.value,
            "timestamp": time.time()
        })
