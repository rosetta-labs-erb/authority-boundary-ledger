"""
Authority Boundary Ledger

A governance primitive for persistent authority constraints in LLM systems.
"""

from .authority_system import AuthorityLedger, Message, GenerationResult
from .boundary_types import (
    BoundaryType,
    RingLevel,
    Action,
    Boundary,
    VerificationResult,
    create_boundary,
    get_enforcement_instruction,
)
from .boundary_ledger import BoundaryLedger
from .verifier import BoundaryVerifier

__version__ = "0.1.0"
__all__ = [
    "AuthorityLedger",
    "Message",
    "GenerationResult",
    "BoundaryType",
    "RingLevel",
    "Action",
    "Boundary",
    "VerificationResult",
    "create_boundary",
    "get_enforcement_instruction",
    "BoundaryLedger",
    "BoundaryVerifier",
]
