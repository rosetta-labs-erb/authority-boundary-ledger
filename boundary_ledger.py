"""
Boundary Ledger - Core State Management

The missing primitive: persistent authority constraints.
"""

from typing import Optional, Dict, List
from boundary_types import Boundary, RingLevel, Action, create_boundary
import time
import threading

class BoundaryLedger:
    """
    Persistent storage for authority boundaries.

    In-memory only (dict) for this reference implementation. 
    Production deployments should replace this with Redis/Postgres.
    
    Implements ring-based hierarchy with bitwise AND for merging.
    Thread-safe for concurrent access.
    """
    
    def __init__(self):
        # conversation_id → {ring_level → boundary}
        self._boundaries: Dict[str, Dict[RingLevel, Boundary]] = {}
        self._events: Dict[str, List[dict]] = {}
        self._lock = threading.RLock()  # Thread safety for production
    
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
        with self._lock:
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
        with self._lock:
            if conversation_id not in self._boundaries:
                return None
            
            boundaries = list(self._boundaries[conversation_id].values())
            
            if not boundaries:
                return None
            
            if len(boundaries) == 1:
                return boundaries[0]
            
            # Merge via bitwise AND
            return self._merge(boundaries)
    
    def get_effective_permissions(self, conversation_id: str) -> Action:
        """
        Get effective permission bitmask for conversation.
        
        Returns:
            Action bitmask (defaults to ALL if no boundaries)
        """
        with self._lock:
            boundary = self.get(conversation_id)
            
            # Default to ALL if no boundary exists
            if not boundary:
                return Action.ALL
            
            return boundary.allowed_actions
    
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
        with self._lock:
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
        with self._lock:
            boundary = self.get(conversation_id)
            
            if not boundary:
                return True  # No boundaries
            
            return boundary.allows(action)
    
    def log_violation(
        self,
        conversation_id: str,
        violation_type: str,
        turn_number: int
    ):
        """
        PATCH 4: Log a security violation to the audit trail.
        
        This is CRITICAL for governance. The system promises to
        "Turn silent failures into explicit, auditable events."
        
        Without this method, security blocks are handled correctly
        (attacks are stopped) but invisibly (admins never know).
        
        Now, when a user attempts a tool injection attack:
        - The attack is blocked (Capacity Gate)
        - The attempt is logged (this method)
        - Admins can review patterns and flag suspicious behavior
        
        Args:
            conversation_id: Conversation ID
            violation_type: Type of violation (e.g., "TOOL_INJECTION_ATTEMPT")
            turn_number: Turn where violation occurred
        """
        with self._lock:
            if conversation_id not in self._events:
                self._events[conversation_id] = []
            
            self._events[conversation_id].append({
                "event": "VIOLATION",
                "turn": turn_number,
                "boundary": "SECURITY_KERNEL",  # System-level security
                "ring": 0,  # Constitutional - cannot be bypassed
                "details": violation_type,
                "timestamp": time.time()
            })
    
    def get_audit_trail(self, conversation_id: str) -> List[dict]:
        """Get audit trail."""
        with self._lock:
            return self._events.get(conversation_id, []).copy()
    
    def _log_event(
        self,
        conversation_id: str,
        event_type: str,
        boundary: Boundary,
        turn_number: int
    ):
        """Log event (must be called within lock)."""
        if conversation_id not in self._events:
            self._events[conversation_id] = []
        
        self._events[conversation_id].append({
            "event": event_type,
            "turn": turn_number,
            "boundary": boundary.type.value,
            "ring": boundary.ring_level.value,
            "timestamp": time.time()
        })
