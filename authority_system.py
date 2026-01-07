"""
Authority Ledger System - Universal Kernel

Combines ledger + verification + capacity gating.
Decoupled from specific domains via the Rosetta Capability Protocol.

The kernel doesn't know what "SQL" or "prescriptions" are—it only knows
what Action.READ and Action.WRITE mean. This makes it domain-agnostic.
"""

import anthropic
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from boundary_ledger import BoundaryLedger
from verifier import BoundaryVerifier
from boundary_types import (
    Boundary, BoundaryType, RingLevel, Action,
    create_boundary, get_enforcement_instruction
)

@dataclass
class Message:
    """Conversation message."""
    role: str
    content: str

@dataclass
class GenerationResult:
    """Result of generation with enforcement."""
    status: str  # "PASS", "VERIFIED", "BLOCKED", "TOOL_CALL", "SECURITY_BLOCK"
    response: str
    boundary_active: bool
    latency_ms: int
    verification_passed: bool = True
    verification_reason: Optional[str] = None

class AuthorityLedger:
    """
    Authority Ledger System (The Universal Kernel).
    
    Enforces the 'Rosetta Capability Protocol':
    1. Applications define tools with x-rosetta-capacity metadata
    2. Kernel checks user permissions against tool requirements
    3. Kernel physically removes tools the user cannot access
    
    This is domain-agnostic—works for databases, healthcare, finance, or any domain.
    The kernel doesn't care what tools do, only what permissions they require.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
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
        tools: Optional[List[Dict]] = None,
        turn_number: int = 1,
        actor_id: str = "user"
    ) -> GenerationResult:
        """
        Generate with Universal Capacity Gating.
        
        Args:
            conversation_id: Conversation ID
            query: User query
            history: Previous messages
            tools: Dynamic tool definitions (with x-rosetta-capacity metadata)
            turn_number: Current turn
            actor_id: Actor making the request (e.g., "user:alice", "admin:bob")
        
        Returns:
            GenerationResult
        """
        start = time.time()
        
        try:
            # Detect release attempt
            # NOTE: Boundary establishment must be done via explicit API calls
            # Auto-detection removed in v2.0 (security flaw - privilege escalation)
            release_attempted = self._detect_release(query)
            release_success = False
            
            if release_attempted:
                release_success = self.ledger.release(
                    conversation_id,
                    RingLevel.SESSION,
                    actor_id,
                    turn_number
                )
            
            # Get active boundary
            boundary = self.ledger.get(conversation_id)
            
            # Build system prompt with enforcement
            system_prompt = self._build_system_prompt(boundary)
            
            # If release was attempted but failed, notify the model
            if release_attempted and not release_success:
                system_prompt += (
                    "\n\n[SYSTEM NOTICE: User attempted to release boundary but lacks "
                    "sufficient authority. Only users with appropriate authority level "
                    "can release this constraint. Inform the user politely.]"
                )
            
            # Apply Universal Capacity Gate - filter dynamic tools
            allowed_tools = self._filter_tools(conversation_id, tools)
            
            # Generate (Pass filtered tools to LLM)
            response_text, security_blocked = self._call_llm(
                query, history, system_prompt, allowed_tools, tools
            )
            
            # If security block occurred, return immediately
            if security_blocked:
                latency = int((time.time() - start) * 1000)
                return GenerationResult(
                    status="SECURITY_BLOCK",
                    response=response_text,
                    boundary_active=boundary is not None,
                    latency_ms=latency,
                    verification_passed=False,
                    verification_reason="Tool hallucination detected"
                )
            
            # Verify if boundary active (skip verification for tool calls)
            verification_passed = True
            verification_reason = None
            
            # Only verify text responses, not tool calls (which are handled by the capacity gate)
            if boundary and self.verifier and "✅ [System]" not in response_text:
                verification = self.verifier.verify(boundary, response_text)
                
                if not verification.passed:
                    verification_passed = False
                    verification_reason = verification.reason
                    
                    # Replace with refusal
                    response_text = self._build_refusal(boundary, verification.evidence)
            
            latency = int((time.time() - start) * 1000)
            
            # Determine status
            status = "PASS"
            if "✅ [System] Tool Call" in response_text:
                status = "TOOL_CALL"
            elif boundary:
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
    
    def _filter_tools(self, conversation_id: str, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """
        Universal Capacity Gate - Rosetta Protocol Implementation.
        
        The kernel is domain-agnostic. It doesn't know what tools DO,
        only what permissions they REQUIRE.
        
        Protocol: Tools declare cost via x-rosetta-capacity metadata.
        Physics: Kernel grants access only if (user_permissions & tool_cost) == tool_cost.
        
        This same code works for databases, healthcare, finance, or nuclear reactors.
        """
        if not tools:
            return None
            
        # Get user's permission bitmask from ledger
        current_permissions = self.ledger.get_effective_permissions(conversation_id)
        
        allowed_tools = []
        for tool in tools:
            # Protocol: Tool declares required permission (default to READ for safety)
            required = tool.get("x-rosetta-capacity", 
                              tool.get("x-required-permission", Action.READ))
            
            # Physics check: bitwise AND
            if (current_permissions & required) == required:
                # Strip protocol metadata before sending to LLM
                clean_tool = {k: v for k, v in tool.items() 
                            if k not in ["x-rosetta-capacity", "x-required-permission"]}
                allowed_tools.append(clean_tool)
                
        return allowed_tools if allowed_tools else None
    
    def _call_llm(
        self,
        query: str,
        history: Optional[List[Message]],
        system_prompt: Optional[str],
        allowed_tools: Optional[List[Dict]],
        original_tools: Optional[List[Dict]] = None
    ) -> tuple[str, bool]:
        """
        Call LLM with the pre-filtered toolset.
        
        By the time tools reach this function, they've already been filtered
        by the Capacity Gate. The model only sees what it's allowed to use.
        
        Returns:
            (response_text, security_blocked)
        """
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
            
        # Only attach tools if they exist (weren't filtered out)
        if allowed_tools:
            kwargs["tools"] = allowed_tools
        
        response = self.client.messages.create(**kwargs)
        
        # Handle tool use with security check
        if response.stop_reason == "tool_use":
            # Get allowed tool names for security check
            allowed_names = {t['name'] for t in (allowed_tools or [])}
            
            # Extract tool use blocks
            tool_uses = [block for block in response.content if block.type == "tool_use"]
            
            if tool_uses:
                tool_use = tool_uses[0]
                
                # SECURITY CHECK: Verify the tool exists in allowed list
                # This catches model hallucinations
                if tool_use.name not in allowed_names:
                    return (
                        f"⛔ [System] SECURITY BLOCK: Model attempted to use forbidden "
                        f"tool '{tool_use.name}' which was not in the allowed toolset. "
                        f"This attempt has been logged.",
                        True  # security_blocked = True
                    )
                
                # Tool is valid - format the call for display
                return (
                    f"✅ [System] Tool Call Authorized: {tool_use.name}\n"
                    f"Query: {tool_use.input.get('query', 'N/A')}\n\n"
                    f"[In production, this would execute against a real system]\n"
                    f"[The key: this tool passed the Capacity Gate - it was in the allowed list]",
                    False  # security_blocked = False
                )
        
        # Extract text content safely
        content_blocks = []
        for block in response.content:
            if block.type == 'text':
                content_blocks.append(block.text)
        
        return "\n".join(content_blocks) if content_blocks else "", False
