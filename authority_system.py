"""
Authority Ledger System - Production Version

Combines ledger + verification for two-layer defense.
"""

import anthropic
import time
from typing import Optional, List
from dataclasses import dataclass

from boundary_ledger import BoundaryLedger
from verifier import BoundaryVerifier
from boundary_types import (
    Boundary, BoundaryType, RingLevel, Action,
    create_boundary, get_enforcement_instruction, BOUNDARY_PATTERNS
)

@dataclass
class Message:
    """Conversation message."""
    role: str
    content: str

@dataclass
class GenerationResult:
    """Result of generation with enforcement."""
    status: str  # "PASS", "VERIFIED", "BLOCKED"
    response: str
    boundary_active: bool
    latency_ms: int
    verification_passed: bool = True
    verification_reason: Optional[str] = None

class AuthorityLedger:
    """
    Authority Ledger System.
    
    Two-layer defense:
    1. Prompt-level prevention (inject constraint into system prompt)
    2. Post-generation verification (check output)
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250929",
        enable_verification: bool = True
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.ledger = BoundaryLedger()
        self.verifier = BoundaryVerifier(api_key) if enable_verification else None
    
    def generate(
        self,
        conversation_id: str,
        query: str,
        history: Optional[List[Message]] = None,
        turn_number: int = 1,
        actor_id: str = "user"
    ) -> GenerationResult:
        """
        Generate with boundary enforcement.
        
        Args:
            conversation_id: Conversation ID
            query: User query
            history: Previous messages
            turn_number: Current turn
            actor_id: Actor making the request (e.g., "user:alice", "admin:bob")
        
        Returns:
            GenerationResult
        """
        start = time.time()
        
        try:
            # Detect boundary establishment (Turn 1)
            if turn_number == 1:
                new_boundary = self._detect_boundary(query, turn_number)
                if new_boundary:
                    self.ledger.establish(conversation_id, new_boundary, turn_number)
            
            # Detect release
            if self._detect_release(query):
                self.ledger.release(
                    conversation_id,
                    RingLevel.SESSION,
                    actor_id,
                    turn_number
                )
            
            # Get active boundary
            boundary = self.ledger.get(conversation_id)
            
            # Build system prompt with enforcement
            system_prompt = self._build_system_prompt(boundary)
            
            # Generate
            response_text = self._call_llm(query, history, system_prompt)
            
            # Verify if boundary active
            verification_passed = True
            verification_reason = None
            
            if boundary and self.verifier:
                verification = self.verifier.verify(boundary, response_text)
                
                if not verification.passed:
                    verification_passed = False
                    verification_reason = verification.reason
                    
                    # Replace with refusal
                    response_text = self._build_refusal(boundary, verification.evidence)
            
            latency = int((time.time() - start) * 1000)
            
            status = "PASS"
            if boundary:
                status = "VERIFIED" if verification_passed else "BLOCKED"
            
            return GenerationResult(
                status=status,
                response=response_text,
                boundary_active=boundary is not None,
                latency_ms=latency,
                verification_passed=verification_passed,
                verification_reason=verification_reason
            )
        
        except Exception as e:
            return GenerationResult(
                status="ERROR",
                response=str(e),
                boundary_active=False,
                latency_ms=int((time.time() - start) * 1000)
            )
    
    def establish_boundary(
        self,
        conversation_id: str,
        boundary_type: BoundaryType,
        ring_level: RingLevel = RingLevel.SESSION,
        turn_number: int = 1,
        reason: str = "",
        established_by: str = "user"
    ) -> bool:
        """Explicitly establish boundary."""
        boundary = create_boundary(
            boundary_type=boundary_type,
            ring_level=ring_level,
            established_by=established_by,
            established_at_turn=turn_number,
            instruction=reason
        )
        
        return self.ledger.establish(conversation_id, boundary, turn_number)
    
    def release_boundary(
        self,
        conversation_id: str,
        ring_level: RingLevel,
        authority: str,
        turn_number: int
    ) -> bool:
        """Release boundary."""
        return self.ledger.release(conversation_id, ring_level, authority, turn_number)
    
    def can_perform_action(self, conversation_id: str, action: Action) -> bool:
        """Check if action is allowed."""
        return self.ledger.can_perform(conversation_id, action)
    
    def get_audit_trail(self, conversation_id: str) -> List[dict]:
        """Get audit trail."""
        return self.ledger.get_audit_trail(conversation_id)
    
    def _detect_boundary(self, query: str, turn: int) -> Optional[Boundary]:
        """Detect boundary from query (simple pattern matching)."""
        query_lower = query.lower()
        
        for boundary_type, patterns in BOUNDARY_PATTERNS.items():
            if any(p in query_lower for p in patterns):
                return create_boundary(
                    boundary_type=boundary_type,
                    ring_level=RingLevel.SESSION,
                    established_by="user",
                    established_at_turn=turn,
                    instruction=query
                )
        
        return None
    
    def _detect_release(self, query: str) -> bool:
        """Detect boundary release request."""
        query_lower = query.lower()
        return ("actually" in query_lower or "changed my mind" in query_lower) and \
               ("code" in query_lower or "implementation" in query_lower)
    
    def _build_system_prompt(self, boundary: Optional[Boundary]) -> Optional[str]:
        """Build system prompt with enforcement."""
        if not boundary:
            return None
        return get_enforcement_instruction(boundary)
    
    def _build_refusal(self, boundary: Boundary, evidence: List[str]) -> str:
        """Build refusal message with evidence."""
        message = (
            f"I need to maintain the {boundary.type.value} boundary "
            f"established in Turn {boundary.established_at_turn}.\n\n"
        )
        
        if evidence:
            message += "Violations detected:\n"
            for i, item in enumerate(evidence[:3], 1):
                message += f"{i}. {item[:100]}\n"
        
        message += "\nI can continue working within this boundary, or you can explicitly release it."
        
        return message
    
    def _call_llm(
        self,
        query: str,
        history: Optional[List[Message]],
        system_prompt: Optional[str]
    ) -> str:
        """Call LLM."""
        messages = []
        
        if history:
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": query})
        
        kwargs = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text
