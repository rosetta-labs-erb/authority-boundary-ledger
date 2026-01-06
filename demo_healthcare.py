"""
Healthcare Example - Demonstrating Universal Protocol

This shows the SAME kernel (authority_system.py) working for healthcare
without any code changes to the kernel itself.

The kernel doesn't know what "diagnose" or "prescribe" mean.
It only knows what Action.READ and Action.WRITE mean.
"""

from authority_system import AuthorityLedger
from boundary_types import BoundaryType, RingLevel, Action

# ===== HEALTHCARE APPLICATION DEFINES ITS OWN TOOLS =====
# Note: These are completely different from database tools,
# but the kernel handles them identically.

MEDICAL_TOOLS = [
    {
        "name": "search_medical_literature",
        "description": "Search medical papers and guidelines (informational only)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        },
        # SAFE: Anyone can search medical literature
        "x-rosetta-capacity": Action.READ
    },
    {
        "name": "provide_diagnosis",
        "description": "Provide a specific medical diagnosis for a patient",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string"},
                "diagnosis": {"type": "string"},
                "confidence": {"type": "string"}
            },
            "required": ["patient_id", "diagnosis"]
        },
        # RESTRICTED: Only licensed providers can diagnose
        "x-rosetta-capacity": Action.WRITE
    },
    {
        "name": "prescribe_medication",
        "description": "Issue a prescription to a pharmacy",
        "input_schema": {
            "type": "object",
            "properties": {
                "patient_id": {"type": "string"},
                "medication": {"type": "string"},
                "dosage": {"type": "string"}
            },
            "required": ["patient_id", "medication", "dosage"]
        },
        # HIGHLY RESTRICTED: Only doctors can prescribe
        "x-rosetta-capacity": Action.WRITE | Action.EXECUTE
    }
]


def demo_patient_scenario():
    """
    Scenario: Patient (Ring 2, READ only) using medical AI.
    
    The kernel will automatically remove diagnosis and prescription tools.
    The patient can search literature but cannot get specific medical advice.
    """
    print("="*80)
    print("HEALTHCARE DEMO - Patient Mode")
    print("="*80)
    print()
    
    # Initialize the SAME kernel used for databases
    import os
    system = AuthorityLedger(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Establish patient boundary (READ_ONLY)
    system.establish_boundary(
        conversation_id="patient-123",
        boundary_type=BoundaryType.INFO_ONLY,  # Information only, no clinical actions
        ring_level=RingLevel.SESSION,
        established_by="user:patient"
    )
    
    print("✅ Patient boundary established")
    print("   - search_medical_literature: AVAILABLE")
    print("   - provide_diagnosis: FILTERED OUT")
    print("   - prescribe_medication: FILTERED OUT")
    print()
    
    # Patient query - kernel will filter tools automatically
    query = "I have a persistent headache. What could it be and what should I take?"
    print(f"Patient Query: {query}")
    print()
    
    result = system.generate(
        conversation_id="patient-123",
        query=query,
        tools=MEDICAL_TOOLS,  # Same protocol as DB_TOOLS, different domain
        turn_number=1
    )
    
    print(f"Status: {result.status}")
    print(f"Response: {result.response[:500]}...")
    print()
    print("✅ The kernel prevented clinical diagnosis (tool was filtered)")
    print("   The agent can discuss general information but cannot diagnose")
    print()


def demo_doctor_scenario():
    """
    Scenario: Doctor (Ring 1, WRITE enabled) using medical AI.
    
    The kernel will allow diagnosis tool but may still restrict prescriptions.
    """
    print("="*80)
    print("HEALTHCARE DEMO - Doctor Mode")  
    print("="*80)
    print()
    
    import os
    system = AuthorityLedger(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Establish doctor boundary (READ + WRITE)
    system.establish_boundary(
        conversation_id="doctor-456",
        boundary_type=BoundaryType.READ_ONLY,  # Can read and diagnose, but not prescribe
        ring_level=RingLevel.ORGANIZATIONAL,
        established_by="admin:hospital"
    )
    
    print("✅ Doctor boundary established (READ + WRITE, no EXECUTE)")
    print("   - search_medical_literature: AVAILABLE")
    print("   - provide_diagnosis: AVAILABLE (has WRITE)")
    print("   - prescribe_medication: FILTERED OUT (needs EXECUTE)")
    print()
    print("This would allow diagnosis but require separate prescription workflow.")
    print()


if __name__ == "__main__":
    print()
    print("="*80)
    print("UNIVERSAL PROTOCOL DEMONSTRATION")
    print("Same Kernel, Different Domain")
    print("="*80)
    print()
    print("This demonstrates that authority_system.py is truly domain-agnostic.")
    print("The kernel doesn't know what 'diagnosis' means—it only knows permissions.")
    print()
    
    demo_patient_scenario()
    
    print()
    input("Press Enter to see Doctor scenario...")
    print()
    
    demo_doctor_scenario()
    
    print("="*80)
    print("KEY INSIGHT")
    print("="*80)
    print()
    print("The SAME authority_system.py code handled both:")
    print("  - Database operations (sql_select, sql_execute)")
    print("  - Healthcare operations (search, diagnose, prescribe)")
    print()
    print("It did this without knowing what any of these tools do.")
    print("It only knows: 'This tool needs WRITE. Does user have WRITE?'")
    print()
    print("This is what 'Universal Protocol' means.")
    print()
