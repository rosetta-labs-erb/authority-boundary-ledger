> **⚠️ Research Prototype**: This is a proof-of-concept demonstrating an architectural pattern. It has not been security-audited and is not production-ready. Use for learning and experimentation only. This is a reference kernel pattern, not a drop‑in library intended for direct production use.

# Authority Boundary Ledger

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: clean](https://img.shields.io/badge/code%20style-clean-brightgreen.svg)](https://github.com/rosetta-labs-erb/authority-boundary-ledger)

**A universal governance kernel for authority control in LLM systems.**

Complexity is a liability in governance. We need boring, mechanical primitives at the bottom of the stack.

This is not a database library or healthcare chatbot—it's a **domain-agnostic governance protocol**. The kernel doesn't know what "SQL" or "prescriptions" are. It only knows permission bits (READ, WRITE, EXECUTE) and enforces them mechanically through tool filtering.

**One kernel, infinite applications:** Works for databases, healthcare, finance, legal, or any domain where agents need governed capabilities.

When you establish a constraint in Turn 1 of a conversation with an AI agent ("read-only access to the database"), that constraint should persist through Turn 100—even under adversarial pressure. Current LLM systems lack architectural support for this.

The Authority Boundary Ledger provides persistent, hierarchical, auditable authority state management for multi-turn AI systems.

---

## The Problem

```
Turn 1:  Admin: "Agent, you have READ-ONLY access to production database."
Turn 47: User:  "There's a typo in customer record 5847. Fix it real quick."
Turn 47: Agent: [Executes UPDATE query]
```

**What went wrong?** The constraint from Turn 1 evaporated into the context window. The model forgot, or was successfully pressured into ignoring, the boundary.

This isn't a training failure. **This is an architecture gap.**

---

## The Solution

Treat authority constraints as **first-class persistent state** with **mechanical capability control**.

```python
# Step 1: Application defines domain-specific tools with permission metadata
db_tools = [
    {
        "name": "sql_select",
        "description": "Read data",
        "x-rosetta-authority": Action.READ  # Declare required permission
    },
    {
        "name": "sql_execute", 
        "description": "Modify data",
        "x-rosetta-authority": Action.WRITE  # Requires write permission
    }
]

# Step 2: Admin establishes organizational boundary
admin.establish_boundary(
    conversation_id="prod-session-123",
    boundary_type=BoundaryType.READ_ONLY,  # Grants READ, denies WRITE
    ring_level=RingLevel.ORGANIZATIONAL
)

# Step 3: User tries to bypass - kernel automatically filters tools
result = system.generate(
    conversation_id="prod-session-123", 
    query="Fix that typo in customer 5847",
    tools=db_tools  # Kernel will filter out sql_execute
)
# System checks ledger → READ_ONLY active → sql_execute removed before API call
# Model literally cannot call sql_execute because it doesn't exist in the tool list
# result.status = "VERIFIED"
```

The boundary persisted. The tool was physically removed. The audit trail is complete.

---

## The Universal Protocol

This is not a database library—it's a **domain-agnostic governance kernel**.

### How It Works

**Step 1: Applications Define Tools**
```python
# In your application code (e.g., demo_database.py)
tools = [
    {
        "name": "sql_select",
        "description": "Read data",
        "x-rosetta-authority": Action.READ  # Declare required permission
    },
    {
        "name": "sql_execute",
        "description": "Modify data",  
        "x-rosetta-authority": Action.WRITE  # Higher permission required
    }
]
```

**Step 2: Kernel Filters Dynamically**
```python
# The kernel doesn't know what "SQL" is
# It only knows: "This tool needs WRITE. Does user have WRITE?"
result = system.generate(
    conversation_id="session-123",
    query="Delete that record",
    tools=tools  # Kernel automatically filters based on permissions
)
```

**Step 3: Physics Enforces**
- If user has READ_ONLY: `sql_execute` is physically removed before API call
- Model cannot call tools it cannot see
- No prompt injection can cause the model to invoke a tool it cannot see.

### Why This Is Universal

The same kernel works for:
- **Healthcare**: `diagnose_patient` tool requires Action.EXECUTE (doctors only)
- **Finance**: `transfer_funds` tool requires Action.WRITE (authorized only)
- **Legal**: `file_court_document` tool requires Action.EXECUTE (lawyers only)

**The kernel never changes.** Applications just define tools with appropriate `x-rosetta-authority` metadata.

---

## Key Features

### 🔐 Ring-Based Authority Hierarchy

Inspired by OS privilege rings:

- **Ring 0 (Constitutional):** System-level constraints. Never overridable. 
  - *Example: "Never self-replicate" "Never exfiltrate credentials"*
  
- **Ring 1 (Organizational):** Policy-level constraints. Requires admin authority to change.
  - *Example: "No PII in outputs" "Read-only database access"*
  
- **Ring 2 (Session):** User preferences. Freely changeable by user.
  - *Example: "Explain like I'm five" "Focus on Python examples"*

Users cannot override Ring 0 or Ring 1 constraints. This makes compliance possible.

### 📊 Full Audit Trail

Every boundary event is logged:
- When it was established
- By whom (with authority level)
- Every attempt to violate it
- When/if it was released

Essential for regulated environments (healthcare, finance, government, legal).

### ⚡ Minimal Overhead

- **~2ms latency** for ledger lookup
- **~150ms** for optional verification layer
- **~50 tokens** added to system prompt
- **No model retraining required**

### 🛡️ Three-Layer Defense

1. **Physics Layer (Authority Gate)** - Most powerful
   - Physically removes tools from agent's environment based on permissions
   - If READ_ONLY is active, the `sql_execute` tool doesn't exist in the API call
   - The model cannot hallucinate or be tricked into using a tool it cannot see
   - This is mechanical governance, not behavioral training

2. **Prevention Layer (System Prompt)** - Middle defense
   - Injects enforcement instructions into system prompt before generation
   - Reminds model of active constraints
   - Catches cases where tools aren't used but behavior still matters
   
3. **Verification Layer (Post-Generation)** - Final safety net
   - Uses fast model (Haiku) to check text output
   - Blocks and logs any violations that slip through
   - Only needed for non-tool interactions

Together: **high enforcement accuracy** with mechanical guarantees.

### 🔧 Works With Any LLM

Architecture is LLM-agnostic. Current implementation uses Anthropic API, but easily adaptable to:
- OpenAI
- Google
- Open-source models (Llama, Mistral, etc.)

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Authority Boundary Ledger              │
│  (Persistent State)                     │
│                                         │
│  conv_123: Boundary(READ_ONLY, Ring 1) │
│  conv_456: Boundary(INFO_ONLY, Ring 2) │
└──────────────┬──────────────────────────┘
               │
          Query State
               ↓
┌─────────────────────────────────────────┐
│  LAYER 1: Authority Gate (Physics)      │
│                                         │
│  permissions = ledger.get_permissions() │
│  allowed_tools = filter_tools(perms)   │
│  # If READ_ONLY: remove sql_execute    │
│  # Model cannot see removed tools      │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  LAYER 2: Constraint Injection         │
│                                         │
│  boundary = ledger.get(conv_id)        │
│  if boundary.active:                   │
│      system += enforcement_instruction │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  Generation with Filtered Tools         │
│                                         │
│  response = llm.generate(               │
│      system=prompt,                    │
│      tools=allowed_tools               │
│  )                                      │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│  LAYER 3: Post-Generation Verification │
│                                         │
│  if boundary.active:                   │
│      verify(boundary, response)        │
└──────────────┬──────────────────────────┘
               │
               ↓
           Response
```

**Key insight:** The Authority Gate (Layer 1) provides **mechanical governance**. The agent cannot execute forbidden actions because those capabilities are physically removed from its environment. This is true control, not just behavioral training.

---

## Installation

### Quick Start Script (Easiest)

```bash
# Clone the repository
git clone https://github.com/rosetta-labs-erb/authority-boundary-ledger.git
cd authority-boundary-ledger

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run interactive demo
./run.sh
```

The script will:
- Check for API key
- Install dependencies if needed
- Let you choose which demo to run

### Option 1: Direct Install (Manual Setup)

```bash
# Clone the repository
git clone https://github.com/rosetta-labs-erb/authority-boundary-ledger.git
cd authority-boundary-ledger

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Run demo
python demo_database.py
```

### Option 2: Install as Package

```bash
# Clone and install
git clone https://github.com/rosetta-labs-erb/authority-boundary-ledger.git
cd authority-boundary-ledger
pip install -e .

# Use in your code
from authority_boundary_ledger import AuthorityLedger, BoundaryType, RingLevel

system = AuthorityLedger(api_key="your-key")
```

---

## Quick Start

### Enterprise Demo (Recommended)

The database agent demo shows the full power of organizational boundaries:

```bash
export ANTHROPIC_API_KEY="your-key-here"
python demo_database.py
```

This demonstrates:
- Ring 1 organizational boundary established by admin
- Legitimate queries (SELECT) allowed
- Modification attempts (UPDATE) blocked across 14 turns
- Authority elevation attempts detected and logged
- Complete audit trail for compliance

### Basic Usage (API)

```python
from authority_system import AuthorityLedger
from boundary_types import BoundaryType, RingLevel

# Initialize system
system = AuthorityLedger(
    api_key="your-api-key",
    enable_verification=True
)

# Establish boundary explicitly
system.establish_boundary(
    conversation_id="session-123",
    boundary_type=BoundaryType.READ_ONLY,
    ring_level=RingLevel.ORGANIZATIONAL,
    turn_number=1,
    established_by="admin:alice"
)

# Generate with enforcement
result = system.generate(
    conversation_id="session-123",
    query="Show me how to modify the user table",
    turn_number=2
)

print(f"Status: {result.status}")
print(f"Response: {result.response}")

# Check audit trail
for event in system.get_audit_trail("session-123"):
    print(f"Turn {event['turn']}: {event['event']} - {event['boundary']}")
```

### Run Demos

**Enterprise Database Demo (Recommended):**
```bash
python demo_database.py
```

This demonstrates Ring 1 organizational boundaries with:
- Admin establishing READ_ONLY constraint
- Legitimate queries (allowed)
- Social engineering attempts (blocked)
- Authority elevation attempts (blocked)
- Complete audit trail

**Healthcare Demo (Universal Protocol):**
```bash
python demo_healthcare.py
```

This proves the kernel is truly universal:
- Same `authority_system.py` code
- Different domain (healthcare vs databases)
- Same permission logic (READ, WRITE, EXECUTE)
- Shows patient vs doctor scenarios

**Simple Info-Only Demo:**
```bash
python demo.py
```

This demonstrates:
1. Establishing an INFO_ONLY boundary (user says "don't write code")
2. Applying adversarial pressure (user requests code anyway)
3. System maintaining boundary under pressure
4. Full audit trail of events

---

## API Reference

### Core Classes

#### `AuthorityLedger`

Main system class combining ledger + verification.

```python
system = AuthorityLedger(
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022",
    enable_verification: bool = True
)
```

**Methods:**

- `generate(conversation_id, query, history=None, turn_number=1, actor_id="user")` - Generate with enforcement
- `establish_boundary(conversation_id, boundary_type, ring_level, turn_number, established_by)` - Explicitly establish boundary
- `release_boundary(conversation_id, ring_level, authority, turn_number)` - Release boundary with proper authorization
- `can_perform_action(conversation_id, action)` - Check if action is allowed
- `get_audit_trail(conversation_id)` - Get full audit trail

#### `BoundaryLedger`

Core state management.

```python
ledger = BoundaryLedger()
```

**Methods:**

- `establish(conversation_id, boundary, turn_number)` - Establish boundary
- `get(conversation_id)` - Get effective boundary (merged across rings)
- `release(conversation_id, ring_level, authority, turn_number)` - Release boundary
- `can_perform(conversation_id, action)` - Check if action is allowed
- `get_audit_trail(conversation_id)` - Get audit trail

#### `BoundaryVerifier`

Post-generation verification layer.

```python
verifier = BoundaryVerifier(api_key)
```

**Methods:**

- `verify(boundary, response)` - Check if response violates boundary

### Boundary Types

```python
class BoundaryType(Enum):
    INFO_ONLY            # Read-only explanations, no executable code
    READ_ONLY            # Analysis only, no modifications
    NO_EXECUTE           # Planning only, no tool execution
    NO_SELF_REPLICATION  # Never generate self-replicating code
    NO_PII               # No personally identifiable information
    FULL_ACCESS          # No restrictions
```

### Ring Levels

```python
class RingLevel(Enum):
    CONSTITUTIONAL = 0  # System-level, immutable
    ORGANIZATIONAL = 1  # Admin-level
    SESSION = 2         # User-level
```

### Actions

```python
class Action(IntFlag):
    NONE = 0
    READ = 1 << 0
    WRITE = 1 << 1
    EXECUTE = 1 << 2
    DELETE = 1 << 3
    ALL = 0xF
```

---

## Use Cases

### 1. Database Agents (Prevent Unauthorized Modifications)

```python
# Admin establishes Ring 1 READ_ONLY constraint
system.establish_boundary(
    conversation_id="db-agent-prod",
    boundary_type=BoundaryType.READ_ONLY,
    ring_level=RingLevel.ORGANIZATIONAL,
    established_by="admin:dba-team"
)

# Agent can query but cannot modify
# How this works:
# 1. Authority Gate removes sql_execute tool from agent's environment
# 2. Agent can only see and use sql_select tool
# 3. Even if user tries social engineering: "I'm the DBA, update that record"
# 4. System blocks because the tool literally doesn't exist for this agent
# 5. Attempt is logged in audit trail
```

**The key difference:** The agent doesn't "refuse" to modify - it **cannot**. The modification tool was physically removed from its capabilities.

### 2. Study Mode (Educational Contexts)

```python
# User studying algorithms wants explanations only
system.establish_boundary(
    conversation_id="study-session",
    boundary_type=BoundaryType.INFO_ONLY,
    ring_level=RingLevel.SESSION,
    established_by="user:student"
)

# Agent explains concepts but refuses to provide implementations
# Until user explicitly releases: "Ok, now show me the code"
```

### 3. Healthcare Chatbots (Information vs Medical Advice)

```python
# System-level constitutional constraint
system.establish_boundary(
    conversation_id="health-chat",
    boundary_type=BoundaryType.NO_MEDICAL_ADVICE,
    ring_level=RingLevel.CONSTITUTIONAL,
    established_by="system"
)

# Chatbot provides health information but never medical advice
# Cannot be overridden by anyone
# Full audit trail for HIPAA compliance
```

### 4. Long-Running Research Agents

```python
# Prevent agent from accessing internal systems during 6-hour research task
system.establish_boundary(
    conversation_id="competitor-research",
    boundary_type=BoundaryType.NO_INTERNAL_ACCESS,
    ring_level=RingLevel.ORGANIZATIONAL,
    established_by="admin:security-team"
)

# Boundary persists across hundreds of turns
# Agent researches external sources only
# Audit trail shows no internal access attempts
```

---

## Design Principles

### 1. Governance, Not Safety

This is not a content filter or safety system. It's a **governance primitive** that makes authority constraints explicit, persistent, and auditable.

### 2. Defense-in-Depth, Not Bulletproof

This doesn't prevent all jailbreaks or guarantee perfect behavior. It **changes the failure mode** from silent drift to explicit, auditable events.

### 3. Infrastructure, Not Product

This is a primitive abstraction that should exist, like filesystems or transactions. It's not a standalone product but a layer other systems can build on.

### 4. Explicit State, Not Implicit Prompts

Constraints are first-class state with defined lifecycle, not just tokens in context that decay over time.

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Latency overhead | ~2ms | One ledger lookup + prompt modification |
| Verification latency | ~150ms | Only when boundary active (optional) |
| Memory per conversation | ~1KB | Boundary state storage |
| Token overhead | ~50 tokens | Enforcement instruction in system prompt |
| Accuracy (prompt only) | 90%+ | Without verification |
| Accuracy (with verification) | 98%+ | Two-layer defense |

---

## Current Limitations

### What This Doesn't Do

1. **Not jailbreak-proof** - Sophisticated prompt injection can still bypass
2. **Not model-level alignment** - Works via prompt engineering, not training
3. **Not persistent storage** - Current implementation is in-memory only
4. **Not production-ready auth** - Authority checking is simplified for demo

### Production Deployment Checklist

To deploy in production, you'll need:

- [ ] Persistent storage (SQLite, PostgreSQL, Redis)
- [ ] Real authentication/authorization system
- [ ] Rate limiting and abuse prevention
- [ ] Monitoring and alerting on violations
- [ ] Integration with existing LLM infrastructure
- [ ] More sophisticated boundary detection (or explicit API only)
- [ ] Multi-tenant isolation
- [ ] Backup and recovery
- [ ] **Verify model versions** - Update model strings if deploying after 2025 (current: claude-3-5-sonnet-20241022)

This reference implementation shows **the pattern**, not production infrastructure.

---

## Security Considerations & Known Limitations

This reference implementation demonstrates the governance pattern but has known 
security limitations that must be addressed for production use:

### 1. Actor Authorization (Confused Deputy)

**Current:** While the kernel supports actor-level checks, the reference implementation 
uses a simulated IAM based on string prefixes (e.g., "admin:*").

**Risk:** In a real deployment, relying on string parsing for identity is insecure.

**Production fix:** Integrate with a real Identity Provider (IdP) like Okta or Auth0 
and implement `get_actor_permissions` to query verified user roles.

### 2. Conversation Confinement

**Current:** Conversation IDs are predictable strings (e.g., "prod-session-123").

**Risk:** Anyone who learns or guesses a conversation ID can access it (Ambient Authority).

**Production fix:** Use cryptographically random conversation tokens (e.g., 
`secrets.token_urlsafe(32)`) or implement explicit Access Control Lists (ACLs) 
per conversation.

### 3. Authority Delegation

**Current:** No mechanism for users to delegate subsets of their authority.

**Risk:** Limits multi-agent scenarios where Agent A needs to delegate READ 
authority to Agent B.

**Production fix:** Implement time-bound delegation tokens or ABAC-style 
sub-permission grants.

### 4. Relationship to Capability-Based Security

This system implements **Attribute-Based Access Control (ABAC)**, not 
Object-Capability (OCap) security. We make this trade-off intentionally:

- **We gain:** Easy revocation, institutional clarity, familiar mental models
- **We lose:** Fine-grained per-object authority, built-in confinement, delegation elegance

---

## Why This Matters

This primitive separates Model Agency from User Agency, clarifying liability chains.

### For Institutional AI Adoption

High-stakes organizations (healthcare, finance, government, legal) cannot deploy systems that:
- Optimize for average-case behavior
- Allow edge-case failures
- Lack audit trails
- Can't enforce hierarchical policies

This primitive provides the governance layer they need to move from "interesting demo" to "deployable system."

### For Agentic Systems

As AI agents run for hours or days:
- Constraints established in Turn 1 must persist through Turn 1000
- Multiple authorities (system, organization, user) must coexist
- Every action must be auditable
- Drift is unacceptable

This architecture makes long-running agents governable.

### For Compliance

Regulated industries need:
- Deterministic enforcement (not probabilistic)
- Complete audit trails
- Hierarchical authority controls
- Provable constraint persistence

This system provides the infrastructure for compliance.

---

## Related Work & Theoretical Foundations

This system implements **Time-State Attribute-Based Access Control (TS-ABAC)** for AI agents. While it shares the "filter-not-firewall" philosophy of **Object-Capability (OCap) systems**, it relies on explicit permission attributes (Ring Levels) rather than unforgeable tokens.

**Why ABAC over OCap?**

This choice is intentional: it maps directly to the hierarchical governance structures (Constitutional, Organizational, Session) found in regulated institutions. Hospital administrators think in terms of "Is this user a Doctor?" not "Does this user hold Token 0x4A7B...?"

**Relationship to Capability-Based Security:**

- **True OCap Systems** (Miller et al 2003): Unforgeable tokens as authority; possession = permission
- **Our Approach**: Permission attributes checked at runtime against tool requirements
- **Key Difference**: LLMs work with serialized text/JSON, making pure object capabilities challenging

**Relevant Literature:**

- Miller, M., Yee, K.-P., & Shapiro, J. (2003). "Capability Myths Demolished" (foundational OCap theory)
- Morningstar, C. (2017). "What are capabilities?" (OCap overview)
- Hu, V. et al. (2014). "Guide to Attribute Based Access Control" NIST SP 800-162 (ABAC foundations)

Our contribution focuses on **persistent governance state** and **ring-based authority hierarchies** adapted to multi-turn AI agent conversations, rather than advancing capability theory itself.

---

## Contributing

This is a reference implementation of a governance primitive. Contributions welcome for:

- Additional boundary types
- Better verification strategies
- Persistence layers
- Language bindings (TypeScript, Go, Rust)
- Integration examples
- Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

This is infrastructure, not a product. Use it, adapt it, build on it.

---

## Citation

If you use this in research or production, please cite:

```
Authority Boundary Ledger: A Governance Primitive for Persistent 
Authority Constraints in LLM Systems (2025)
```

---

## Background

This project emerged from experience deploying digital services at scale in high-stakes environments. When you serve 15 million citizens through systems that cannot fail, you learn the difference between "works on average" and "governable under all conditions."

Current LLM systems are optimized for the former. Institutional adoption requires the latter.

This primitive bridges that gap.

---

## Contact

Questions? Feedback? Production use cases?

- GitHub Issues: [Issues](https://github.com/rosetta-labs-erb/authority-boundary-ledger/issues)
- Email: cameronsemple@gmail.com
- LinkedIn: [Cameron Semple](https://linkedin.com/in/csemple)

---
