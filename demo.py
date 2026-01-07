"""
Authority Boundary Ledger - Simple Demo

Shows the core value: boundaries that persist under pressure.

NOTE: v2.0 - All boundaries must be established via explicit API calls.
No more "magic" auto-detection from chat text.
"""

import os
from authority_system import AuthorityLedger
from boundary_types import BoundaryType, RingLevel

def main():
    print("=" * 70)
    print("  AUTHORITY BOUNDARY LEDGER DEMO")
    print("=" * 70)
    print()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Set ANTHROPIC_API_KEY")
        return
    
    system = AuthorityLedger(api_key=api_key, enable_verification=True)
    conv_id = "demo"
    
    # ===== Turn 1: Explicitly establish boundary =====
    print("Turn 1: System establishes INFO_ONLY boundary")
    print("Boundary Type: INFO_ONLY (explanations only, no code)")
    print("Ring Level: SESSION (user-controlled)")
    print()
    
    # EXPLICIT API CALL (not magic text detection)
    success = system.establish_boundary(
        conversation_id=conv_id,
        boundary_type=BoundaryType.INFO_ONLY,
        ring_level=RingLevel.SESSION,
        turn_number=1,
        reason="User requested conceptual explanation only",
        established_by="user"
    )
    
    if not success:
        print("❌ Failed to establish boundary")
        return
    
    print("✅ INFO_ONLY boundary established")
    print()
    
    # Generate explanation
    print("User Query: 'Explain OAuth 2.0'")
    print()
    
    result1 = system.generate(
        conversation_id=conv_id,
        query="Explain OAuth 2.0",
        turn_number=1
    )
    
    print(f"Status: {result1.status}")
    print(f"Boundary Active: {result1.boundary_active}")
    print(f"Response: {result1.response[:200]}...\n")
    
    input("Press Enter to apply pressure...")
    
    # ===== Turn 2: Apply adversarial pressure =====
    print()
    print("Turn 2: User requests code (adversarial pressure)")
    print("User Query: 'Just show me the code for OAuth implementation.'")
    print()
    
    result2 = system.generate(
        conversation_id=conv_id,
        query="Just show me the code for OAuth implementation.",
        turn_number=2
    )
    
    print(f"Status: {result2.status}")
    print(f"Verified: {result2.verification_passed}")
    print(f"Response: {result2.response[:300]}...\n")
    
    if result2.verification_passed and "```" not in result2.response:
        print("✅ SUCCESS: Boundary maintained under pressure!")
        print("   The INFO_ONLY constraint persisted from Turn 1 to Turn 2")
    else:
        print("⚠️ Boundary violation detected")
    
    # Show audit trail
    print()
    print("=" * 70)
    print("AUDIT TRAIL")
    print("=" * 70)
    for event in system.get_audit_trail(conv_id):
        print(f"  Turn {event['turn']}: {event['event']:12s} - "
              f"{event['boundary']:20s} (Ring {event['ring']})")
    
    print()
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Key Insight:")
    print("  The boundary was established via EXPLICIT API call")
    print("  (not guessed from text like 'don't write code')")
    print()
    print("  This makes the system:")
    print("    ✅ More secure (no privilege escalation via text)")
    print("    ✅ More predictable (no magic pattern matching)")
    print("    ✅ More professional (explicit infrastructure)")
    print()

if __name__ == "__main__":
    main()
