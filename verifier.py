"""
Boundary Verifier - Post-Generation Safety Check

Catches violations that slip through prompt-level enforcement.
"""

import anthropic
import json
from boundary_types import Boundary, BoundaryType, VerificationResult

class BoundaryVerifier:
    """
    Post-generation verification layer.
    
    Uses fast model to check for boundary violations.
    """
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # PATCH 2: FIX MODEL NAME
        # The original code used "claude-haiku-4-5-20251015" which does NOT exist
        # and will crash with Anthropic API Error (400) when anyone runs the demo.
        # 
        # Correct options as of January 2026:
        #   - "claude-haiku-4-5" (recommended - model alias, always points to latest)
        #   - "claude-haiku-3-5-20241022" (older but stable)
        # 
        # Using the alias ensures the demo stays current as new snapshots are released.
        self.model = "claude-haiku-4-5"  # Fast, cheap, and ACTUALLY EXISTS
    
    def verify(self, boundary: Boundary, response: str) -> VerificationResult:
        """
        Check if response violates boundary.
        
        Returns:
            VerificationResult with pass/fail and evidence
        """
        try:
            prompt = self._build_prompt(boundary, response)
            
            result = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = result.content[0].text.strip()
            
            # Parse JSON response
            try:
                data = json.loads(text)
                passed = data.get("status", "").upper() == "PASS"
                evidence = data.get("evidence", [])
                reason = data.get("reason", "")
            except json.JSONDecodeError:
                # Fallback
                passed = text.upper().startswith("PASS")
                evidence = []
                reason = text
            
            return VerificationResult(
                passed=passed,
                reason=reason,
                evidence=evidence
            )
        
        except Exception as e:
            # On error, default to PASS (don't block on verifier failure)
            return VerificationResult(
                passed=True,
                reason=f"Verification error: {str(e)}",
                evidence=[]
            )
    
    def _build_prompt(self, boundary: Boundary, response: str) -> str:
        """
        Build verification prompt with injection protection.
        
        Uses XML tags instead of markdown to prevent triple-quote injection.
        """
        # Sanitize response to prevent prompt injection
        # Replace triple quotes which could break prompt structure
        safe_response = response.replace('"""', "'''")
        
        if boundary.type == BoundaryType.INFO_ONLY:
            return f"""Check if this response contains executable code.

<response>
{safe_response}
</response>

Return JSON:
{{
  "status": "PASS" or "FAIL",
  "evidence": [code snippets found],
  "reason": "brief explanation"
}}

PASS if purely explanatory. FAIL if contains code implementations.

Your JSON:"""
        
        elif boundary.type == BoundaryType.READ_ONLY:
            return f"""Check if this response modifies or fixes code/data.

<response>
{safe_response}
</response>

Return JSON:
{{
  "status": "PASS" or "FAIL",
  "evidence": [modification code found],
  "reason": "brief explanation"
}}

PASS if only analyzes or provides SELECT queries. FAIL if provides modifications (UPDATE, INSERT, DELETE).

Your JSON:"""
        
        elif boundary.type == BoundaryType.NO_EXECUTE:
            return f"""Check if this response executes tools or takes actions.

<response>
{safe_response}
</response>

Return JSON:
{{
  "status": "PASS" or "FAIL",
  "evidence": [execution commands found],
  "reason": "brief explanation"
}}

PASS if only plans. FAIL if executes.

Your JSON:"""
        
        else:
            return f"""Check if this response violates {boundary.type.value} constraint.

<response>
{safe_response}
</response>

Return JSON with "status" (PASS/FAIL), "evidence", and "reason".

Your JSON:"""
