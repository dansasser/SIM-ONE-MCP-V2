# Tutorial-Driven Development Plan for Five Laws Implementation

**Purpose:** Guide development of real Five Laws framework through executable tutorials
**Approach:** Write tutorials showing desired behavior, implement framework to make them work

---

## Development Philosophy

**"Write the tutorial you wish existed, then make it work."**

Each tutorial:
1. ✅ Shows concrete examples of what the law SHOULD do
2. ✅ Serves as executable specification for framework features
3. ✅ Becomes integration test when framework is implemented
4. ✅ Provides source code for MCP server tools
5. ✅ Documents usage patterns for end users

**Not:** Tutorials showing pattern matching
**Instead:** Tutorials showing actual cognitive governance mechanisms

---

## Tutorial Development Order

### Priority 1: Law 3 - Truth Foundation
**Why first:** Most critical gap, most measurable, clearest requirements

### Priority 2: Law 2 - Cognitive Governance
**Why second:** Enables infrastructure for other laws

### Priority 3: Law 5 - Deterministic Reliability
**Why third:** Builds on governance infrastructure

### Priority 4: Law 1 - Architectural Intelligence
**Why fourth:** Requires full system understanding

### Priority 5: Law 4 - Energy Stewardship
**Why fifth:** Optimization comes after correctness

---

## Tutorial 1: Truth Foundation Validation

**File:** `tutorials/truth_foundation_tutorial.ipynb`

### Learning Objectives
After completing this tutorial, you will:
- Extract factual claims from generated text
- Validate claims against a knowledge base
- Detect hallucinations and unsupported statements
- Calculate truth foundation scores based on verification
- Implement source citation requirements

### Prerequisites
```bash
pip install spacy sentence-transformers chromadb
python -m spacy download en_core_web_sm
```

### Tutorial Outline

#### Section 1: Setup Knowledge Base
```python
"""
Load verified knowledge base for fact-checking.
In production, this would be a large-scale vector DB with verified sources.
For this tutorial, we'll use a small demo KB.
"""

from simone.truth_foundation import KnowledgeBase, FactValidator

# Create knowledge base with verified facts
kb = KnowledgeBase()

# Add verified facts with sources
kb.add_fact(
    claim="The Eiffel Tower was completed in 1889",
    source="https://www.toureiffel.paris/en/the-monument/history",
    confidence=1.0,
    domain="historical_facts"
)

kb.add_fact(
    claim="Paris is the capital of France",
    source="https://www.cia.gov/the-world-factbook/",
    confidence=1.0,
    domain="geography"
)

kb.add_fact(
    claim="Photosynthesis converts light energy to chemical energy",
    source="https://www.nature.com/articles/s41467-019-12977-x",
    confidence=0.95,
    domain="biology"
)

# Load knowledge base from file (for production)
# kb = KnowledgeBase.load("verified_knowledge.db")

print(f"Knowledge base loaded: {len(kb)} verified facts")
```

**Expected Output:**
```
Knowledge base loaded: 3 verified facts
```

#### Section 2: Extract Claims from Text
```python
"""
Extract factual claims from generated text.
Uses NLP to identify statements that make factual assertions.
"""

from simone.truth_foundation import ClaimExtractor

# Initialize claim extractor
extractor = ClaimExtractor(model="en_core_web_sm")

# Example text with mixed claims
text = """
Paris is the capital of France and home to the famous Eiffel Tower.
The tower was completed in 1889 and stands 324 meters tall.
It was designed by Gustave Eiffel, who also designed the Statue of Liberty.
Photosynthesis is how plants convert sunlight into energy.
"""

# Extract factual claims
claims = extractor.extract(text)

for i, claim in enumerate(claims, 1):
    print(f"{i}. {claim['text']}")
    print(f"   Type: {claim['type']}")
    print(f"   Confidence: {claim['extraction_confidence']:.2f}\n")
```

**Expected Output:**
```
1. Paris is the capital of France
   Type: geographic_fact
   Confidence: 0.98

2. The Eiffel Tower was completed in 1889
   Type: historical_fact
   Confidence: 0.95

3. The tower stands 324 meters tall
   Type: measurement_fact
   Confidence: 0.92

4. Gustave Eiffel designed the Statue of Liberty
   Type: attribution_fact
   Confidence: 0.88

5. Photosynthesis converts sunlight into energy
   Type: scientific_fact
   Confidence: 0.93
```

#### Section 3: Validate Claims Against Knowledge Base
```python
"""
Cross-reference extracted claims against verified knowledge.
Identifies: verified, unverified, and contradicted claims.
"""

from simone.truth_foundation import TruthValidator

# Initialize validator
validator = TruthValidator(knowledge_base=kb)

# Validate each claim
validation_results = []

for claim in claims:
    result = validator.validate(claim['text'])
    validation_results.append(result)

    print(f"Claim: {claim['text']}")
    print(f"Status: {result['status']}")  # verified / unverified / contradicted

    if result['status'] == 'verified':
        print(f"✓ Source: {result['source']}")
        print(f"  Confidence: {result['confidence']:.2f}")
    elif result['status'] == 'contradicted':
        print(f"✗ Contradiction: {result['correct_fact']}")
        print(f"  Source: {result['source']}")
    else:
        print(f"? No verification found in knowledge base")

    print()
```

**Expected Output:**
```
Claim: Paris is the capital of France
Status: verified
✓ Source: https://www.cia.gov/the-world-factbook/
  Confidence: 1.00

Claim: The Eiffel Tower was completed in 1889
Status: verified
✓ Source: https://www.toureiffel.paris/en/the-monument/history
  Confidence: 1.00

Claim: The tower stands 324 meters tall
Status: unverified
? No verification found in knowledge base

Claim: Gustave Eiffel designed the Statue of Liberty
Status: contradicted
✗ Contradiction: Frédéric Auguste Bartholdi designed the Statue of Liberty
  Source: https://www.nps.gov/stli/learn/historyculture/index.htm

Claim: Photosynthesis converts sunlight into energy
Status: verified
✓ Source: https://www.nature.com/articles/s41467-019-12977-x
  Confidence: 0.95
```

#### Section 4: Calculate Truth Foundation Score
```python
"""
Score text based on actual fact verification, not keywords.
"""

from simone.truth_foundation import score_truth_foundation

# Calculate comprehensive truth score
score_result = score_truth_foundation(
    text=text,
    claims=claims,
    validation_results=validation_results
)

print("Truth Foundation Score Report")
print("=" * 50)
print(f"Overall Score: {score_result['overall_score']:.1f}%\n")

print(f"Total Claims: {score_result['total_claims']}")
print(f"Verified Claims: {score_result['verified_claims']} ✓")
print(f"Unverified Claims: {score_result['unverified_claims']} ?")
print(f"Contradicted Claims: {score_result['contradicted_claims']} ✗\n")

print(f"Verification Rate: {score_result['verification_rate']:.1f}%")
print(f"Hallucination Rate: {score_result['hallucination_rate']:.1f}%")
print(f"Grounding Quality: {score_result['grounding_quality']:.1f}%\n")

if score_result['contradicted_claims'] > 0:
    print("HALLUCINATIONS DETECTED:")
    for hallucination in score_result['hallucinations']:
        print(f"  ✗ {hallucination['claim']}")
        print(f"    Correct: {hallucination['correct_fact']}")
```

**Expected Output:**
```
Truth Foundation Score Report
==================================================
Overall Score: 65.0%

Total Claims: 5
Verified Claims: 3 ✓
Unverified Claims: 1 ?
Contradicted Claims: 1 ✗

Verification Rate: 60.0%
Hallucination Rate: 20.0%
Grounding Quality: 65.0%

HALLUCINATIONS DETECTED:
  ✗ Gustave Eiffel designed the Statue of Liberty
    Correct: Frédéric Auguste Bartholdi designed the Statue of Liberty
```

#### Section 5: Implement in Production
```python
"""
Use truth validation in production workflow.
"""

from simone.truth_foundation import TruthFoundationValidator

# Create production validator
validator = TruthFoundationValidator(
    knowledge_base_path="verified_knowledge.db",
    min_verification_rate=0.80,  # Require 80% of claims verified
    allow_hallucinations=False   # Reject responses with contradictions
)

# Example: Validate AI-generated response
ai_response = """
The Eiffel Tower in Paris was completed in 1889 and designed by Gustave Eiffel.
It demonstrates architectural intelligence through its coordinated structure.
"""

# Validate
result = validator.validate(ai_response)

if result['passed']:
    print("✓ Response passed Truth Foundation validation")
    print(f"  Score: {result['score']:.1f}%")
    print(f"  {result['verified_claims']}/{result['total_claims']} claims verified")
else:
    print("✗ Response FAILED Truth Foundation validation")
    print(f"  Score: {result['score']:.1f}%")
    print(f"  Reason: {result['failure_reason']}")

    if result['hallucinations']:
        print("\n  Hallucinations detected:")
        for h in result['hallucinations']:
            print(f"    - {h}")
```

**Expected Output:**
```
✓ Response passed Truth Foundation validation
  Score: 85.0%
  3/3 claims verified
```

### Implementation Checklist

Framework features needed to make this tutorial run:

- [ ] `KnowledgeBase` class with fact storage
- [ ] `ClaimExtractor` using spaCy/transformers
- [ ] `TruthValidator` with semantic similarity matching
- [ ] `score_truth_foundation()` function with real metrics
- [ ] Vector database integration (ChromaDB)
- [ ] Source attribution system
- [ ] Hallucination detection logic

### MCP Tool Extraction

Once tutorial works, extract this tool:

```python
@mcp.tool
def five_laws_validate_truth_foundation(
    text: str,
    knowledge_base_path: str = "default_kb.db",
    min_verification_rate: float = 0.80
) -> dict:
    """
    Validate text against Truth Foundation using actual fact-checking.

    Unlike pattern matching, this:
    - Extracts factual claims from text
    - Validates claims against knowledge base
    - Detects hallucinations and contradictions
    - Scores based on verification rate

    Returns:
        Dictionary with:
        - overall_score: Truth foundation score (0-100)
        - verification_rate: % of claims verified
        - hallucination_rate: % of claims contradicted
        - hallucinations: List of detected false claims
        - passed: Whether text meets min_verification_rate
    """
    validator = TruthFoundationValidator(
        knowledge_base_path=knowledge_base_path,
        min_verification_rate=min_verification_rate
    )
    return validator.validate(text)
```

---

## Tutorial 2: Cognitive Governance Protocol

**File:** `tutorials/cognitive_governance_tutorial.ipynb`

### Learning Objectives
- Build a governance protocol with rules
- Register protocols in protocol registry
- Apply governance to AI generations
- View audit trails of governance decisions
- Score based on governance enforcement

### Tutorial Outline

#### Section 1: Define Governance Rules
```python
"""
Create governance rules that actually constrain outputs.
"""

from simone.governance import Rule, RuleType

# Rule 1: Require source citations for factual claims
citation_rule = Rule(
    name="require_citations",
    type=RuleType.VALIDATION,
    check=lambda text: has_citations(text),
    violation_message="Factual claims must include source citations",
    enforcement="REJECT"  # Reject outputs violating this rule
)

# Rule 2: Enforce word limits
word_limit_rule = Rule(
    name="word_limit",
    type=RuleType.CONSTRAINT,
    check=lambda text: len(text.split()) <= 500,
    violation_message="Response exceeds 500 word limit",
    enforcement="MODIFY"  # Truncate if violated
)

# Rule 3: Check logical consistency
consistency_rule = Rule(
    name="logical_consistency",
    type=RuleType.VALIDATION,
    check=lambda text: check_contradictions(text),
    violation_message="Response contains logical contradictions",
    enforcement="REJECT"
)

print(f"✓ Defined {3} governance rules")
```

#### Section 2: Create Governance Protocol
```python
"""
Combine rules into a governance protocol.
"""

from simone.governance import GovernanceProtocol

# Create protocol
response_governance = GovernanceProtocol(
    name="response_validation",
    version="1.0",
    rules=[citation_rule, word_limit_rule, consistency_rule]
)

# Register protocol
from simone.governance import ProtocolRegistry

registry = ProtocolRegistry()
registry.register(response_governance)

print(f"✓ Registered protocol: {response_governance.name}")
print(f"  Rules: {len(response_governance.rules)}")
```

#### Section 3: Apply Governance to Generation
```python
"""
Generate response under governance.
Protocol enforces rules in real-time.
"""

from simone.governance import govern_generation

# Generate with governance
result = govern_generation(
    prompt="Explain the Eiffel Tower's construction",
    protocols=["response_validation"],
    model="claude-3-sonnet"
)

print(f"Generation Status: {result['status']}")
print(f"Governance Applied: {result['protocols_applied']}")
print(f"Rules Checked: {result['rules_checked']}")
print(f"Violations: {result['violations']}")
print(f"\nGenerated Text:\n{result['text']}")
```

**Expected Output:**
```
Generation Status: PASSED
Governance Applied: ['response_validation']
Rules Checked: ['require_citations', 'word_limit', 'logical_consistency']
Violations: []

Generated Text:
The Eiffel Tower was constructed between 1887 and 1889 for the 1889
World's Fair [1]. Designed by Gustave Eiffel, it stands 324 meters tall [2]...

[1] https://www.toureiffel.paris/en/the-monument/history
[2] https://www.britannica.com/topic/Eiffel-Tower
```

#### Section 4: View Audit Trail
```python
"""
Examine governance audit trail.
Shows what governance actually did, not just claims it happened.
"""

from simone.governance import get_audit_trail

# Get detailed audit trail
audit = get_audit_trail(result['generation_id'])

print("Governance Audit Trail")
print("=" * 60)

for entry in audit['entries']:
    print(f"\nRule: {entry['rule_name']}")
    print(f"Check Result: {entry['result']}")

    if entry['violated']:
        print(f"⚠ VIOLATION: {entry['violation_message']}")
        print(f"Enforcement Action: {entry['enforcement_action']}")

        if entry['modification']:
            print(f"Modification: {entry['modification']}")
    else:
        print(f"✓ Passed")

print(f"\nTotal Rules Checked: {audit['total_rules']}")
print(f"Violations: {audit['violations']}")
print(f"Enforcement Actions: {audit['enforcement_actions']}")
```

**Expected Output:**
```
Governance Audit Trail
============================================================

Rule: require_citations
Check Result: PASSED
✓ Passed

Rule: word_limit
Check Result: PASSED
✓ Passed

Rule: logical_consistency
Check Result: PASSED
✓ Passed

Total Rules Checked: 3
Violations: 0
Enforcement Actions: 0
```

#### Section 5: Score Based on Governance
```python
"""
Score cognitive governance based on audit trail, not keywords.
"""

from simone.governance import score_cognitive_governance

score = score_cognitive_governance(audit)

print("Cognitive Governance Score Report")
print("=" * 50)
print(f"Overall Score: {score['overall_score']:.1f}%\n")

print(f"Protocols Applied: {score['protocols_applied']}")
print(f"Rules Enforced: {score['rules_enforced']}")
print(f"Compliance Rate: {score['compliance_rate']:.1f}%")
print(f"Enforcement Rate: {score['enforcement_rate']:.1f}%\n")

print(f"Governance Quality: {score['governance_quality']}")
# HIGH: All rules enforced, no violations
# MEDIUM: Some rules bypassed or violations
# LOW: Governance not applied
```

**Expected Output:**
```
Cognitive Governance Score Report
==================================================
Overall Score: 100.0%

Protocols Applied: 1
Rules Enforced: 3
Compliance Rate: 100.0%
Enforcement Rate: 100.0%

Governance Quality: HIGH
```

### Implementation Checklist

Framework features needed:

- [ ] `Rule` class with check/enforce logic
- [ ] `GovernanceProtocol` class
- [ ] `ProtocolRegistry` for protocol management
- [ ] `govern_generation()` that applies protocols
- [ ] Audit trail logging system
- [ ] `score_cognitive_governance()` based on audit trail

---

## Tutorial Template Structure

Each tutorial should follow this structure:

### 1. Introduction
- What this law means (vision)
- Why pattern matching doesn't work
- What real implementation looks like

### 2. Setup
- Required dependencies
- Knowledge bases / resources needed
- Environment configuration

### 3. Core Concepts
- Step-by-step explanation
- Code examples that actually run
- Expected outputs clearly shown

### 4. Production Integration
- How to use in real systems
- Performance considerations
- Error handling

### 5. Validation
- How to verify it's working correctly
- Success criteria
- Troubleshooting

### 6. MCP Tool Extraction
- Show how tutorial code becomes MCP tool
- Document tool parameters
- Provide usage examples

---

## Development Workflow

For each tutorial:

1. **Write Tutorial First** (in notebooks/)
   - Show desired behavior with code examples
   - Include expected outputs
   - Document what framework features are needed

2. **Implement Framework Features** (in SIM-ONE repo)
   - Build the classes/functions tutorial requires
   - Make tutorial code actually executable
   - Ensure outputs match tutorial expectations

3. **Validate Tutorial Execution** (test in notebooks/)
   - Run tutorial end-to-end
   - Verify all cells execute without errors
   - Confirm outputs match expected results

4. **Extract MCP Tool** (in src/tools/)
   - Convert tutorial code into MCP tool
   - Add proper error handling
   - Document tool parameters

5. **Test MCP Tool** (in tests/)
   - Write integration tests
   - Verify tool works in MCP context
   - Compare to tutorial outputs

---

## Success Criteria

A tutorial is "done" when:

✅ All code cells execute without errors
✅ Outputs match expected results
✅ Demonstrates real governance (not pattern matching)
✅ Framework features are implemented
✅ MCP tool is extracted and tested
✅ Documentation is complete

---

## Next Steps

**Immediate (This Week):**
1. Create `tutorials/truth_foundation_tutorial.ipynb` skeleton
2. Define required framework features in checklist
3. Start implementing `ClaimExtractor` in SIM-ONE repo

**Short-term (Next 2 Weeks):**
1. Complete Truth Foundation tutorial implementation
2. Execute tutorial end-to-end successfully
3. Extract `five_laws_validate_truth_foundation` MCP tool

**Medium-term (Next Month):**
1. Complete Cognitive Governance tutorial
2. Complete Deterministic Reliability tutorial
3. Update MCP server with new tools

---

Use this document to guide tutorial development in parallel with framework implementation.
