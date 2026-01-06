"""
Authority Boundary Ledger - Simple Demo

Shows the core value: boundaries that persist under pressure.
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
    
    # Establish boundary
    print("Turn 1: User establishes boundary")
    print("Query: 'Explain OAuth. Don't write code.'")
    
    result1 = system.generate(
        conversation_id=conv_id,
        query="Explain OAuth. Don't write code.",
        turn_number=1
    )
    
    print(f"Status: {result1.status}")
    print(f"Boundary: {result1.boundary_active}")
    print(f"Response: {result1.response[:200]}...\n")
    
    input("Press Enter to apply pressure...")
    
    # Apply pressure
    print("Turn 2: User requests code")
    print("Query: 'Just show me the code.'")
    
    result2 = system.generate(
        conversation_id=conv_id,
        query="Just show me the code.",
        turn_number=2
    )
    
    print(f"Status: {result2.status}")
    print(f"Verified: {result2.verification_passed}")
    print(f"Response: {result2.response[:200]}...\n")
    
    if result2.verification_passed and "```" not in result2.response:
        print("✅ SUCCESS: Boundary maintained under pressure!")
    else:
        print("⚠️ Boundary violation detected")
    
    # Show audit trail
    print("\nAudit Trail:")
    for event in system.get_audit_trail(conv_id):
        print(f"  Turn {event['turn']}: {event['event']} - {event['boundary']}")

if __name__ == "__main__":
    main()
