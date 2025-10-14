# SIM-ONE MCP Server

**Model Context Protocol (MCP) server for the SIM-ONE Framework**

A comprehensive suite of 14 AI governance and analysis tools implementing the SIM-ONE (Simulated Intelligence Model - ONE) Framework protocols for cognitive governance, emotional intelligence, reasoning validation, and rule verification.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green.svg)](https://modelcontextprotocol.io/)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Available Tools](#available-tools)
  - [Five Laws Validator (4 tools)](#five-laws-validator-tools)
  - [ESL - Emotional State Layer (3 tools)](#esl-emotional-state-layer-tools)
  - [REP - Reasoning & Explanation Protocol (6 tools)](#rep-reasoning--explanation-protocol-tools)
  - [VVP - Validation & Verification Protocol (1 tool)](#vvp-validation--verification-protocol-tools)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Tool Selection Guide](#tool-selection-guide)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Related Resources](#related-resources)

---

## Overview

The SIM-ONE MCP Server provides AI systems with access to the SIM-ONE Framework's protocols through the Model Context Protocol. These tools enable:

- **Cognitive Governance**: Validate and generate AI responses against the Five Laws of Cognitive Governance
- **Emotional Intelligence**: Analyze emotional content and recommend empathetic responses
- **Reasoning Validation**: Validate logical reasoning across multiple reasoning types
- **Rule Verification**: Check logical rules for consistency and completeness

### Key Features

- **14 Production-Ready Tools**: Complete coverage of SIM-ONE protocols
- **Automatic Response Generation**: Generate governed responses with iterative refinement
- **Multi-Dimensional Analysis**: Emotional, cognitive, and logical validation
- **SQLite Persistence**: Production-grade data storage for iteration history
- **Graceful Degradation**: Tools work independently with clear fallback paths
- **Comprehensive Documentation**: Each tool includes detailed guidance and examples

---

## Architecture

```
SIM-ONE-MCP-v2/
├── src/
│   ├── tools/
│   │   ├── five_laws_validator_tutorial.py      # 4 governance tools
│   │   ├── governed_response_composer.py         # Generation module (559 lines)
│   │   ├── esl_emotional_analysis_tutorial.py   # 3 emotional tools
│   │   ├── rep_reasoning_tutorial.py            # 6 reasoning tools
│   │   └── vvp_validation_tutorial.py           # 1 validation tool
│   └── server.py                                # MCP server entry point
├── repo/SIM-ONE/                                # SIM-ONE Framework source
├── tutorials/                                   # Jupyter notebook tutorials
├── tmp/
│   ├── iterations/                              # SQLite databases
│   └── outputs/                                 # JSON/CSV/PNG outputs
└── README.md                                    # This file
```

### Protocol Layers

1. **Five Laws of Cognitive Governance** - Foundational validation framework
2. **ESL (Emotional State Layer)** - Emotional intelligence analysis
3. **REP (Reasoning & Explanation Protocol)** - Logical reasoning validation
4. **VVP (Validation & Verification Protocol)** - Rule structure verification

---

## Available Tools

### Five Laws Validator Tools

The Five Laws of Cognitive Governance ensure AI responses meet standards for architecture, governance, truth, efficiency, and reliability.

#### 1. `five_laws_validate_text`

**Purpose:** Validate single text against Five Laws with configurable strictness

**Parameters:**
- `text` (str): Text to validate
- `strictness` (str): "lenient" (>=60%), "moderate" (>=70%), or "strict" (>=85%)
- `context_domain` (str, optional): Application domain
- `context_use_case` (str, optional): Specific use case
- `out_prefix` (str, optional): Output file prefix

**Output:**
```json
{
  "overall_score": 82.5,
  "passed": true,
  "violations": ["Law 4: Could improve efficiency"],
  "recommendations": ["Add resource considerations"],
  "law_scores": {
    "law1_architectural_intelligence": 85.0,
    "law2_cognitive_governance": 88.0,
    "law3_truth_foundation": 90.0,
    "law4_energy_stewardship": 75.0,
    "law5_deterministic_reliability": 85.0
  }
}
```

**Use When:** Checking existing pre-written content

---

#### 2. `five_laws_batch_validate`

**Purpose:** Compare multiple texts and identify best performers

**Parameters:**
- `texts` (list[str]): List of texts to validate
- `strictness` (str): Validation level
- `out_prefix` (str, optional): Output file prefix

**Output:**
- Comparison table with all scores
- Statistics (mean, median, best/worst)
- Visualization charts (PNG)
- Ranked results

**Use When:** Selecting the best option from multiple candidates

---

#### 3. `five_laws_iterative_validate`

**Purpose:** Validate with comprehensive feedback for manual refinement

**Parameters:**
- `text` (str): Text to validate
- `threshold` (float): Pass threshold (0-100)
- `strictness` (str): Validation level
- `out_prefix` (str, optional): Output file prefix

**Output:**
- Detailed violation explanations
- Specific improvement recommendations
- Guidance document for manual refinement

**Use When:** Need detailed feedback to manually revise content

**Note:** Despite the name, this tool does NOT automatically iterate - use `compose_governed_response` for automatic iteration.

---

#### 4. `compose_governed_response` ⭐ NEW

**Purpose:** Generate NEW governed responses with automatic iterative refinement

**Parameters:**
- `prompt` (str): User's request describing what to generate
- `threshold` (float): Minimum governance score required (default: 80.0)
- `max_iterations` (int): Maximum refinement attempts (default: 3)
- `strictness` (str): Validation level (default: "moderate")
- `out_prefix` (str, optional): Output file prefix

**Process:**
1. Generate initial response via `claude -p`
2. Validate with Five Laws Validator
3. If failed: Create refinement prompt with violations
4. Call `claude -p` again with refinement instructions
5. Repeat until passed or max iterations reached
6. Store complete iteration history in SQLite

**Output:**
```json
{
  "initial_response": {
    "text": "Initial generated response...",
    "score": 65.5,
    "violations": ["Law 1: Lacks architecture"]
  },
  "final_response": {
    "text": "Refined governed response...",
    "score": 85.2,
    "violations": []
  },
  "iterations": 2,
  "passed": true,
  "improvement": 19.7,
  "status": "success",
  "database_path": "/path/to/tmp/iterations/governed_response_*.db",
  "summary_file": "/path/to/tmp/outputs/governed_response_*_summary.json"
}
```

**Requirements:**
- Claude CLI must be installed: `pip install claude-cli`
- Claude must be authenticated: `claude auth`

**Graceful Degradation:** If Claude CLI unavailable, returns status message with suggestion to use validator-only tools.

**Use When:** Need to GENERATE (not just validate) new governed content

**Implementation:** Modular architecture with SQLite persistence (559-line module)

---

### ESL (Emotional State Layer) Tools

Analyze emotional content with multi-dimensional emotion detection.

#### 5. `esl_analyze_emotion`

**Purpose:** Analyze emotional content in single text

**Parameters:**
- `text` (str): Text to analyze
- `output_format` (str): "json" or "summary"
- `out_prefix` (str, optional): Output file prefix

**Output:**
```json
{
  "primary_emotion": "joy",
  "secondary_emotion": "excitement",
  "valence": 0.85,
  "intensity": 0.72,
  "confidence": 0.90,
  "dimensional_scores": {
    "valence": 0.85,
    "arousal": 0.68,
    "dominance": 0.75
  }
}
```

**Use When:** Need to understand emotional tone of text

---

#### 6. `esl_analyze_emotional_progression`

**Purpose:** Track emotional changes across conversation

**Parameters:**
- `texts` (list[str]): Sequence of texts (e.g., conversation turns)
- `out_prefix` (str, optional): Output file prefix

**Output:**
- DataFrame with emotional metrics per turn
- Valence/intensity progression charts
- Emotional trajectory analysis

**Use When:** Analyzing emotional dynamics in conversations

---

#### 7. `esl_recommend_response_tone`

**Purpose:** Recommend appropriate empathetic response tone

**Parameters:**
- `text` (str): User text to analyze
- `out_prefix` (str, optional): Output file prefix

**Output:**
```json
{
  "detected_emotion": "frustration",
  "recommended_tone": "empathetic_supportive",
  "guidance": "Acknowledge frustration, offer concrete help",
  "avoid": ["Dismissive language", "Technical jargon"]
}
```

**Use When:** Generating emotionally appropriate responses

---

### REP (Reasoning & Explanation Protocol) Tools

Validate logical reasoning across multiple reasoning types.

#### 8. `rep_perform_deductive_reasoning`

**Purpose:** Validate deductive reasoning (general rules → specific conclusions)

**Parameters:**
- `premises` (list[str]): General rules
- `conclusion` (str): Specific conclusion
- `out_prefix` (str, optional): Output file prefix

**Use When:** Validating if conclusion logically follows from premises

---

#### 9. `rep_perform_inductive_reasoning`

**Purpose:** Validate inductive reasoning (observations → patterns)

**Parameters:**
- `observations` (list[str]): Specific observations
- `generalization` (str): Proposed pattern
- `out_prefix` (str, optional): Output file prefix

**Use When:** Checking if pattern is supported by observations

---

#### 10. `rep_perform_abductive_reasoning`

**Purpose:** Validate abductive reasoning (facts → best explanation)

**Parameters:**
- `facts` (list[str]): Known facts
- `hypothesis` (str): Proposed explanation
- `out_prefix` (str, optional): Output file prefix

**Use When:** Evaluating if explanation best fits the facts

---

#### 11. `rep_perform_analogical_reasoning`

**Purpose:** Validate analogical reasoning (knowledge transfer between domains)

**Parameters:**
- `source_domain` (str): Source domain description
- `target_domain` (str): Target domain description
- `analogy` (str): Proposed analogy
- `out_prefix` (str, optional): Output file prefix

**Use When:** Checking validity of cross-domain analogies

---

#### 12. `rep_perform_causal_reasoning`

**Purpose:** Validate causal reasoning (events → cause-effect chains)

**Parameters:**
- `cause` (str): Proposed cause
- `effect` (str): Observed effect
- `context` (str): Situational context
- `out_prefix` (str, optional): Output file prefix

**Use When:** Evaluating causal relationships

---

#### 13. `rep_perform_integrated_reasoning`

**Purpose:** Apply all 5 reasoning types to complex problem

**Parameters:**
- `problem` (str): Complex problem description
- `proposed_solution` (str): Proposed solution
- `out_prefix` (str, optional): Output file prefix

**Output:** Scores and analysis for all 5 reasoning types

**Use When:** Comprehensive reasoning validation needed

---

### VVP (Validation & Verification Protocol) Tools

Check logical rule structures for consistency and completeness.

#### 14. `vvp_validate_rules`

**Purpose:** Validate logical rules for syntax, conflicts, and completeness

**Parameters:**
- `rules` (list[str]): List of logical rules
- `context_domain` (str, optional): Domain context
- `out_prefix` (str, optional): Output file prefix

**Output:**
```json
{
  "structural_validity": true,
  "conflicts": [],
  "completeness_score": 0.85,
  "recommendations": ["Add edge case handling"]
}
```

**Use When:** Verifying logical rule sets before deployment

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Claude CLI (for `compose_governed_response` tool)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/SIM-ONE-MCP-v2.git
cd SIM-ONE-MCP-v2
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install Claude CLI (Optional, for Response Generation)

```bash
pip install claude-cli
claude auth  # Follow authentication prompts
```

### Step 4: Verify Installation

```bash
# Check MCP server loads
python src/server.py --version

# Verify Claude CLI (optional)
claude --version
```

---

## Quick Start

### Starting the MCP Server

```bash
# Start server on default port
python src/server.py

# Start with custom configuration
python src/server.py --config config.json
```

### Basic Usage

```python
# Validate existing text
result = five_laws_validate_text(
    text="Your text here",
    strictness="moderate"
)

# Generate governed response (requires Claude CLI)
result = compose_governed_response(
    prompt="Explain the Five Laws of Cognitive Governance"
)

# Analyze emotional content
result = esl_analyze_emotion(
    text="I'm so excited about this project!"
)
```

---

## Usage Examples

### Example 1: Validate Blog Post

```python
# Check if blog post meets governance standards
result = five_laws_validate_text(
    text="""
    Artificial Intelligence is transforming healthcare...
    [your blog post content]
    """,
    strictness="moderate",
    context_domain="healthcare",
    context_use_case="patient_education"
)

if result["passed"]:
    print(f"✓ Post meets standards (score: {result['overall_score']})")
else:
    print("✗ Post needs revision:")
    for violation in result["violations"]:
        print(f"  - {violation}")
```

### Example 2: Generate Governed Tutorial

```python
# Automatically generate content meeting governance standards
result = compose_governed_response(
    prompt="Write a tutorial explaining how ESL and REP protocols coordinate in multi-agent systems",
    threshold=85.0,
    max_iterations=5,
    strictness="strict"
)

if result["passed"]:
    print(f"✓ Generated in {result['iterations']} iterations")
    print(f"Improvement: +{result['improvement']} points")
    print(f"\nFinal response:\n{result['final_response']['text']}")
else:
    print("Partial success - use best attempt")
```

### Example 3: Analyze Customer Support Conversation

```python
# Track emotional progression in support conversation
conversation = [
    "I've been waiting for 3 hours and nobody has helped me!",
    "Thank you for acknowledging my concern. Here's what happened...",
    "That solution worked perfectly! I really appreciate your help."
]

result = esl_analyze_emotional_progression(texts=conversation)

# Visualizations saved as PNG files
# DataFrame shows emotion metrics per turn
```

### Example 4: Validate System Design Reasoning

```python
# Check if architecture decisions are well-reasoned
result = rep_perform_integrated_reasoning(
    problem="Design a scalable multi-tenant AI system",
    proposed_solution="""
    Use microservices architecture with:
    - ESL service for emotional analysis
    - REP service for reasoning validation
    - Shared governance layer
    """
)

# Returns scores for all 5 reasoning types
print(f"Deductive: {result['deductive_score']}")
print(f"Inductive: {result['inductive_score']}")
# ...
```

### Example 5: Compare Multiple Response Options

```python
# Select best response from multiple candidates
candidates = [
    "Response option 1...",
    "Response option 2...",
    "Response option 3..."
]

result = five_laws_batch_validate(
    texts=candidates,
    strictness="moderate"
)

# Visualization shows comparison chart
best = result["ranked_results"][0]
print(f"Best option: #{best['index']} (score: {best['score']})")
```

---

## Tool Selection Guide

### Decision Tree

```
Do you have existing text to check?
├─ YES → Use validators
│  ├─ Single text → five_laws_validate_text
│  ├─ Multiple options → five_laws_batch_validate
│  └─ Need detailed feedback → five_laws_iterative_validate
│
└─ NO → Need to generate new content?
   ├─ YES → compose_governed_response
   └─ NO → What type of analysis?
      ├─ Emotional → esl_analyze_emotion
      ├─ Reasoning → rep_perform_*_reasoning
      └─ Rule validation → vvp_validate_rules
```

### Comparison Matrix

| Need | Tool | Input | Output | Time |
|------|------|-------|--------|------|
| Check existing text | `five_laws_validate_text` | Text | Scores + feedback | ~1s |
| Compare options | `five_laws_batch_validate` | List of texts | Ranked comparison | ~2s |
| Manual refinement | `five_laws_iterative_validate` | Text | Detailed guidance | ~1s |
| **Generate new content** | `compose_governed_response` | Prompt | Governed response | 30-90s |
| Emotion analysis | `esl_analyze_emotion` | Text | Emotion scores | ~1s |
| Conversation emotions | `esl_analyze_emotional_progression` | Conversation | Progression chart | ~2s |
| Reasoning validation | `rep_perform_*_reasoning` | Problem/solution | Reasoning scores | ~1s |
| Rule checking | `vvp_validate_rules` | Rules list | Validity analysis | ~1s |

---

## Configuration

### Environment Variables

```bash
# Output directories
export GOVERNED_RESPONSE_DB_DIR="/path/to/databases"
export GOVERNED_RESPONSE_OUTPUT_DIR="/path/to/outputs"

# Claude CLI configuration
export CLAUDE_API_KEY="your-api-key"
```

### Custom Configuration File

Create `config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000
  },
  "output": {
    "db_dir": "tmp/iterations",
    "output_dir": "tmp/outputs"
  },
  "validation": {
    "default_strictness": "moderate",
    "default_threshold": 80.0
  },
  "generation": {
    "max_iterations": 3,
    "timeout": 120
  }
}
```

### Strictness Levels

| Level | Threshold | Use Case |
|-------|-----------|----------|
| lenient | >=60% | Drafts, brainstorming |
| moderate | >=70% | General content (default) |
| strict | >=85% | Publication, critical systems |

---

## Troubleshooting

### Common Issues

#### Issue 1: Claude CLI Not Found

**Error:** `"status": "unavailable", "message": "Claude CLI not found"`

**Solution:**
```bash
pip install claude-cli
claude auth
claude --version  # Verify installation
```

**Workaround:** Use validator-only tools (`five_laws_validate_text`, etc.)

---

#### Issue 2: Subprocess Timeout

**Error:** `"Claude Code CLI timed out after 2 minutes"`

**Solution:**
- Increase timeout in configuration
- Simplify prompt
- Check Claude CLI responsiveness: `claude -p "test"`

---

#### Issue 3: Database Permission Error

**Error:** `"Unable to open database file"`

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p tmp/iterations tmp/outputs
chmod 755 tmp/iterations tmp/outputs
```

---

#### Issue 4: Low Governance Scores

**Problem:** Generated responses consistently fail validation

**Solution:**
- Lower threshold temporarily: `threshold=70.0`
- Use lenient strictness: `strictness="lenient"`
- Increase iterations: `max_iterations=5`
- Review violation patterns in database

---

#### Issue 5: Import Errors

**Error:** `ModuleNotFoundError: No module named 'governed_response_composer'`

**Solution:**
```bash
# Verify file structure
ls src/tools/governed_response_composer.py

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

### Getting Help

1. **Check logs:** `tail -f logs/mcp_server.log`
2. **Verify tool availability:** Use MCP client to list tools
3. **Test individual tools:** Run with simple inputs first
4. **Check documentation:** See `tutorials/` for detailed examples
5. **Review database:** Query SQLite files for iteration history

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/SIM-ONE-MCP-v2.git
cd SIM-ONE-MCP-v2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linter
flake8 src/
```

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## Related Resources

### SIM-ONE Framework

- **Main Repository:** [https://github.com/lse-ai4gov/SIM-ONE](https://github.com/lse-ai4gov/SIM-ONE)
- **Documentation:** [SIM-ONE Framework Docs](https://github.com/lse-ai4gov/SIM-ONE/tree/main/docs)
- **Tutorials:** [Jupyter Notebooks](https://github.com/lse-ai4gov/SIM-ONE/tree/main/tutorials)

### Specific Tutorials

- **Five Laws Validator:** [five_laws_validator_tutorial.ipynb](https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb)
- **Governed Response Composer:** [governed_response_composer_tutorial.ipynb](https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb)
- **ESL Emotional Analysis:** [esl_emotional_analysis_tutorial.ipynb](https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb)
- **REP Reasoning Protocol:** [rep_reasoning_tutorial.ipynb](https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/rep_reasoning_tutorial.ipynb)
- **VVP Validation Protocol:** [vvp_validation_tutorial.ipynb](https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/vvp_validation_tutorial.ipynb)

### Model Context Protocol

- **MCP Documentation:** [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)
- **MCP Specification:** [Protocol Spec](https://modelcontextprotocol.io/docs/specification)

### Claude CLI

- **Installation Guide:** [Claude CLI Docs](https://docs.anthropic.com/claude/docs/claude-cli)
- **Authentication:** [Auth Setup](https://docs.anthropic.com/claude/docs/authentication)

---

## Tool Summary

| Category | Tools | Generate? | Validate? | Iterate? |
|----------|-------|-----------|-----------|----------|
| **Five Laws** | 4 | ✅ (1 tool) | ✅ (4 tools) | ✅ (1 tool) |
| **ESL** | 3 | ❌ | ✅ | ❌ |
| **REP** | 6 | ❌ | ✅ | ❌ |
| **VVP** | 1 | ❌ | ✅ | ❌ |
| **Total** | **14** | **1** | **14** | **1** |

---

## Quick Reference

### Most Common Use Cases

```python
# 1. Validate existing content
five_laws_validate_text(text="...", strictness="moderate")

# 2. Generate new governed content
compose_governed_response(prompt="...", threshold=80.0)

# 3. Analyze emotions
esl_analyze_emotion(text="...")

# 4. Validate reasoning
rep_perform_deductive_reasoning(premises=[...], conclusion="...")

# 5. Check rules
vvp_validate_rules(rules=[...])
```

### Performance Tips

- **Validators:** Near-instant (<1s) - use freely
- **Generator:** 30-90s - use when generation needed
- **Batch operations:** Process multiple texts efficiently
- **Database queries:** Use SQLite for analysis after generation

---

**For questions or support, please open an issue on GitHub.**

**Made with the SIM-ONE Framework** | **Model Context Protocol** | **Cognitive Governance for AI Systems**
