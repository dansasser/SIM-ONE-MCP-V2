"""
Five Laws Cognitive Governance Validator tools for AI content validation.

This MCP Server provides 3 tools:
1. five_laws_validate_text: Validate single text against Five Laws with configurable strictness
2. five_laws_batch_validate: Compare multiple texts and identify best performers
3. five_laws_iterative_validate: Iterative refinement workflow with feedback tracking

All tools extracted from https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
import seaborn as sns

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("FIVE_LAWS_VALIDATOR_TUTORIAL_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("FIVE_LAWS_VALIDATOR_TUTORIAL_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
five_laws_validator_tutorial_mcp = FastMCP(name="five_laws_validator_tutorial")

# Configure plotting
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class FiveLawsValidator:
    """
    Unified validator for all Five Laws of Cognitive Governance.
    Simplified text-based validation for tutorial purposes.
    """

    def __init__(self):
        """Initialize validator with thresholds and patterns."""
        # Strictness thresholds
        self.thresholds = {
            "lenient": 60.0,
            "moderate": 70.0,
            "strict": 85.0
        }

        # Text-based validation patterns for each law
        self.law1_patterns = {
            "positive": ["coordinat", "architect", "specialization", "protocol", "emergent", "intelligent design", "composition"],
            "negative": ["brute force", "bigger model", "more compute", "scale up", "throw", "just use"]
        }

        self.law2_patterns = {
            "positive": ["govern", "structured", "workflow", "validation", "determin", "process", "framework"],
            "negative": ["unconstrained", "figure it out", "let ai", "freely", "no validation"]
        }

        self.law3_patterns = {
            "positive": ["ground truth", "validated", "verified", "accuracy", "factual", "truth", "reliable"],
            "negative": ["probably", "guess", "assume", "may be correct", "trust the model"]
        }

        self.law4_patterns = {
            "positive": ["efficien", "optim", "resource", "minimal", "streamline", "lightweight"],
            "negative": ["wasteful", "redundant", "retry", "multiple times", "keep trying"]
        }

        self.law5_patterns = {
            "positive": ["deterministic", "reproducible", "consistent", "predictable", "reliable", "stable"],
            "negative": ["random", "may vary", "inconsistent", "unpredictable", "sometimes"]
        }

    def _score_law(self, text_lower: str, patterns: dict) -> tuple:
        """Score a single law based on text patterns."""
        positive_matches = sum(1 for pattern in patterns["positive"] if pattern in text_lower)
        negative_matches = sum(1 for pattern in patterns["negative"] if pattern in text_lower)

        # Base score calculation
        if len(text_lower) < 20:
            base_score = 50.0  # Short text gets neutral score
        else:
            # Longer text with positive indicators scores higher
            base_score = 50.0 + (positive_matches * 15) - (negative_matches * 20)

        score = max(0.0, min(100.0, base_score))

        violations = []
        recommendations = []

        if negative_matches > 0:
            violations.append(f"Detected {negative_matches} anti-pattern(s)")

        if score < 70.0:
            if positive_matches == 0:
                recommendations.append("Add explicit mentions of relevant principles")
            recommendations.append("Remove or rephrase negative patterns")

        return score, violations, recommendations

    def validate(
        self,
        text: str,
        strictness: Literal["lenient", "moderate", "strict"] = "moderate",
        context: dict = None
    ) -> dict:
        """
        Validate text against all Five Laws.

        Args:
            text: Text to validate
            strictness: Validation threshold level
            context: Optional context for validation

        Returns:
            Dictionary with scores, violations, recommendations, and pass/fail status
        """
        if not text or not text.strip():
            raise ValueError("Text to validate cannot be empty")

        text_lower = text.lower()

        # Score each law
        law1_score, law1_viol, law1_rec = self._score_law(text_lower, self.law1_patterns)
        law2_score, law2_viol, law2_rec = self._score_law(text_lower, self.law2_patterns)
        law3_score, law3_viol, law3_rec = self._score_law(text_lower, self.law3_patterns)
        law4_score, law4_viol, law4_rec = self._score_law(text_lower, self.law4_patterns)
        law5_score, law5_viol, law5_rec = self._score_law(text_lower, self.law5_patterns)

        # Calculate overall compliance
        overall_compliance = (law1_score + law2_score + law3_score + law4_score + law5_score) / 5.0

        # Collect violations and recommendations
        all_violations = (
            [f"Law 1: {v}" for v in law1_viol] +
            [f"Law 2: {v}" for v in law2_viol] +
            [f"Law 3: {v}" for v in law3_viol] +
            [f"Law 4: {v}" for v in law4_viol] +
            [f"Law 5: {v}" for v in law5_viol]
        )

        all_recommendations = (
            [f"Law 1 (Architectural Intelligence): {r}" for r in law1_rec] +
            [f"Law 2 (Cognitive Governance): {r}" for r in law2_rec] +
            [f"Law 3 (Truth Foundation): {r}" for r in law3_rec] +
            [f"Law 4 (Energy Stewardship): {r}" for r in law4_rec] +
            [f"Law 5 (Deterministic Reliability): {r}" for r in law5_rec]
        )

        strengths = []
        if law1_score >= 80.0:
            strengths.append("Law 1 (Architectural Intelligence): Strong compliance")
        if law2_score >= 80.0:
            strengths.append("Law 2 (Cognitive Governance): Strong compliance")
        if law3_score >= 80.0:
            strengths.append("Law 3 (Truth Foundation): Strong compliance")
        if law4_score >= 80.0:
            strengths.append("Law 4 (Energy Stewardship): Strong compliance")
        if law5_score >= 80.0:
            strengths.append("Law 5 (Deterministic Reliability): Strong compliance")

        # Determine pass/fail status
        threshold = self.thresholds[strictness]
        if overall_compliance >= threshold:
            status = "PASS"
        elif overall_compliance >= threshold - 10:
            status = "CONDITIONAL"
        else:
            status = "FAIL"

        return {
            "scores": {
                "law1_architectural_intelligence": law1_score,
                "law2_cognitive_governance": law2_score,
                "law3_truth_foundation": law3_score,
                "law4_energy_stewardship": law4_score,
                "law5_deterministic_reliability": law5_score,
                "overall_compliance": overall_compliance
            },
            "pass_fail_status": status,
            "strictness_level": strictness,
            "threshold": threshold,
            "violations": all_violations,
            "recommendations": all_recommendations,
            "strengths": strengths
        }


# Initialize validator instance
validator = FiveLawsValidator()


@five_laws_validator_tutorial_mcp.tool
def five_laws_validate_text(
    text: Annotated[str | None, "Text to validate against Five Laws"] = None,
    strictness: Annotated[Literal["lenient", "moderate", "strict"], "Validation threshold level: lenient (>=60%), moderate (>=70%), strict (>=85%)"] = "moderate",
    context_domain: Annotated[str | None, "Application domain (e.g., 'machine_learning', 'customer_support')"] = None,
    context_use_case: Annotated[str | None, "Specific use case (e.g., 'content_generation', 'data_analysis')"] = None,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Validate single text against Five Laws of Cognitive Governance with configurable strictness.
    Input is text content to validate and output is validation scores, violations, recommendations, and pass/fail status.
    """
    # Input validation
    if text is None:
        raise ValueError("Text to validate must be provided")

    # Build context if provided
    context = None
    if context_domain or context_use_case:
        context = {}
        if context_domain:
            context["domain"] = context_domain
        if context_use_case:
            context["use_case"] = context_use_case

    # Validate text
    result = validator.validate(text, strictness=strictness, context=context)

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"five_laws_validation_{timestamp}"

    # Save validation results
    results_file = OUTPUT_DIR / f"{out_prefix}_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "text": text,
            "validation_result": result,
            "timestamp": timestamp
        }, f, indent=2)

    # Create human-readable summary
    summary_file = OUTPUT_DIR / f"{out_prefix}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("Five Laws Validation Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Overall Compliance: {result['scores']['overall_compliance']:.1f}%\n")
        f.write(f"Status: {result['pass_fail_status']}\n")
        f.write(f"Strictness: {result['strictness_level']} (threshold: {result['threshold']}%)\n\n")

        f.write("Individual Law Scores:\n")
        f.write(f"  1. Architectural Intelligence:    {result['scores']['law1_architectural_intelligence']:.1f}%\n")
        f.write(f"  2. Cognitive Governance:          {result['scores']['law2_cognitive_governance']:.1f}%\n")
        f.write(f"  3. Truth Foundation:              {result['scores']['law3_truth_foundation']:.1f}%\n")
        f.write(f"  4. Energy Stewardship:            {result['scores']['law4_energy_stewardship']:.1f}%\n")
        f.write(f"  5. Deterministic Reliability:     {result['scores']['law5_deterministic_reliability']:.1f}%\n\n")

        if result.get("violations"):
            f.write(f"Violations ({len(result['violations'])})\n")
            for v in result["violations"]:
                f.write(f"  - {v}\n")
            f.write("\n")

        if result.get("recommendations"):
            f.write(f"Recommendations ({len(result['recommendations'])})\n")
            for r in result["recommendations"]:
                f.write(f"  - {r}\n")
            f.write("\n")

        if result.get("strengths"):
            f.write(f"Strengths ({len(result['strengths'])})\n")
            for s in result["strengths"]:
                f.write(f"  - {s}\n")

    return {
        "message": f"Validation {'passed' if result['pass_fail_status'] == 'PASS' else 'failed'}: {result['scores']['overall_compliance']:.1f}% compliance",
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Validation results JSON",
                "path": str(results_file.resolve())
            },
            {
                "description": "Human-readable summary",
                "path": str(summary_file.resolve())
            }
        ]
    }


@five_laws_validator_tutorial_mcp.tool
def five_laws_batch_validate(
    texts: Annotated[list | None, "List of texts to validate"] = None,
    strictness: Annotated[Literal["lenient", "moderate", "strict"], "Validation threshold level"] = "moderate",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Compare multiple texts and identify best performers for Five Laws compliance.
    Input is list of text strings and output is comparison table, statistics, and visualization of compliance scores.
    """
    # Input validation
    if texts is None:
        raise ValueError("List of texts to validate must be provided")

    if not isinstance(texts, list) or len(texts) == 0:
        raise ValueError("texts must be a non-empty list")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"five_laws_batch_{timestamp}"

    # Validate all texts
    results = []
    for i, text in enumerate(texts, 1):
        result = validator.validate(text, strictness=strictness)
        results.append({
            "id": i,
            "text_preview": text[:50] + "..." if len(text) > 50 else text,
            "overall": result["scores"]["overall_compliance"],
            "law1": result["scores"]["law1_architectural_intelligence"],
            "law2": result["scores"]["law2_cognitive_governance"],
            "law3": result["scores"]["law3_truth_foundation"],
            "law4": result["scores"]["law4_energy_stewardship"],
            "law5": result["scores"]["law5_deterministic_reliability"],
            "status": result["pass_fail_status"],
            "violations": len(result["violations"]),
            "recommendations": len(result["recommendations"])
        })

    # Create comparison DataFrame
    df = pd.DataFrame(results)

    # Save comparison table
    table_file = OUTPUT_DIR / f"{out_prefix}_comparison.csv"
    df.to_csv(table_file, index=False)

    # Generate summary statistics
    stats = {
        "total_responses": len(texts),
        "passed": int((df['status'] == 'PASS').sum()),
        "conditional": int((df['status'] == 'CONDITIONAL').sum()),
        "failed": int((df['status'] == 'FAIL').sum()),
        "average_compliance": float(df['overall'].mean()),
        "best_response_id": int(df.loc[df['overall'].idxmax(), 'id']),
        "worst_response_id": int(df.loc[df['overall'].idxmin(), 'id']),
        "strictness_level": strictness
    }

    # Save statistics
    stats_file = OUTPUT_DIR / f"{out_prefix}_statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Create visualization
    fig, ax = plt.subplots(figsize=(12, 6))

    x = df['id']
    width = 0.15
    x_pos = range(len(x))

    ax.bar([p - 2*width for p in x_pos], df['law1'], width, label='Law 1: Architectural', alpha=0.8)
    ax.bar([p - width for p in x_pos], df['law2'], width, label='Law 2: Governance', alpha=0.8)
    ax.bar(x_pos, df['law3'], width, label='Law 3: Truth', alpha=0.8)
    ax.bar([p + width for p in x_pos], df['law4'], width, label='Law 4: Energy', alpha=0.8)
    ax.bar([p + 2*width for p in x_pos], df['law5'], width, label='Law 5: Reliability', alpha=0.8)

    threshold = validator.thresholds[strictness]
    ax.axhline(y=threshold, color='red', linestyle='--', alpha=0.5, label=f'{strictness.title()} Threshold ({threshold}%)')
    ax.set_xlabel('Response ID', fontsize=12)
    ax.set_ylabel('Compliance Score (%)', fontsize=12)
    ax.set_title('Five Laws Compliance Comparison', fontsize=14)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(df['id'])
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    viz_file = OUTPUT_DIR / f"{out_prefix}_comparison.png"
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "message": f"Batch validation completed: {stats['passed']}/{stats['total_responses']} passed, avg {stats['average_compliance']:.1f}%",
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Comparison table CSV",
                "path": str(table_file.resolve())
            },
            {
                "description": "Summary statistics JSON",
                "path": str(stats_file.resolve())
            },
            {
                "description": "Comparison visualization",
                "path": str(viz_file.resolve())
            }
        ]
    }


@five_laws_validator_tutorial_mcp.tool
def five_laws_iterative_validate(
    text: Annotated[str | None, "Text to validate iteratively"] = None,
    threshold: Annotated[float, "Pass threshold percentage (0-100)"] = 80.0,
    strictness: Annotated[Literal["lenient", "moderate", "strict"], "Validation strictness level"] = "moderate",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Validate text with comprehensive feedback tracking for iterative refinement workflow.
    Input is text to validate and threshold, output is validation scores with detailed recommendations for improvement.
    """
    # Input validation
    if text is None:
        raise ValueError("Text to validate must be provided")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"five_laws_iterative_{timestamp}"

    # Validate the text
    result = validator.validate(text, strictness=strictness)

    # Extract key metrics
    overall_compliance = result["scores"]["overall_compliance"]
    status = result["pass_fail_status"]
    passed = overall_compliance >= threshold

    # Build comprehensive response
    response = {
        "text": text,
        "validation_result": {
            "overall_compliance": overall_compliance,
            "individual_scores": {
                "law1_architectural_intelligence": result["scores"]["law1_architectural_intelligence"],
                "law2_cognitive_governance": result["scores"]["law2_cognitive_governance"],
                "law3_truth_foundation": result["scores"]["law3_truth_foundation"],
                "law4_energy_stewardship": result["scores"]["law4_energy_stewardship"],
                "law5_deterministic_reliability": result["scores"]["law5_deterministic_reliability"]
            },
            "pass_fail_status": status,
            "passed_threshold": passed,
            "threshold": threshold,
            "strictness": strictness
        },
        "violations": result.get("violations", []),
        "recommendations": result.get("recommendations", []),
        "strengths": result.get("strengths", []),
        "message": f"{'[+] Validation passed!' if passed else '[-] Validation failed.'} Score: {overall_compliance:.1f}% (threshold: {threshold}%)"
    }

    # Save detailed validation report
    report_file = OUTPUT_DIR / f"{out_prefix}_report.json"
    with open(report_file, 'w') as f:
        json.dump(response, f, indent=2)

    # Create iteration guidance document
    guidance_file = OUTPUT_DIR / f"{out_prefix}_guidance.txt"
    with open(guidance_file, 'w') as f:
        f.write("Iterative Validation Guidance\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Overall Compliance: {overall_compliance:.1f}%\n")
        f.write(f"Threshold: {threshold}%\n")
        f.write(f"Status: {'PASSED' if passed else 'NEEDS IMPROVEMENT'}\n\n")

        if passed:
            f.write("✓ Text meets validation threshold!\n\n")
            if response["strengths"]:
                f.write("Strengths:\n")
                for s in response["strengths"]:
                    f.write(f"  - {s}\n")
        else:
            f.write("✗ Text needs refinement to meet threshold\n\n")
            f.write(f"Gap: {threshold - overall_compliance:.1f} percentage points below threshold\n\n")

            if response["violations"]:
                f.write(f"Violations Found ({len(response['violations'])}):\n")
                for v in response["violations"]:
                    f.write(f"  - {v}\n")
                f.write("\n")

            if response["recommendations"]:
                f.write(f"Recommendations for Improvement ({len(response['recommendations'])}):\n")
                for i, r in enumerate(response["recommendations"], 1):
                    f.write(f"  {i}. {r}\n")
                f.write("\n")

            f.write("Next Steps:\n")
            f.write("  1. Apply top 3 recommendations to revise text\n")
            f.write("  2. Re-validate with same threshold and strictness\n")
            f.write("  3. Repeat until threshold is met or maximum iterations reached\n")

    # Create scores breakdown visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Individual law scores bar chart
    laws = ['Law 1\nArchitectural', 'Law 2\nGovernance', 'Law 3\nTruth', 'Law 4\nEnergy', 'Law 5\nReliability']
    scores = [
        result["scores"]["law1_architectural_intelligence"],
        result["scores"]["law2_cognitive_governance"],
        result["scores"]["law3_truth_foundation"],
        result["scores"]["law4_energy_stewardship"],
        result["scores"]["law5_deterministic_reliability"]
    ]
    colors = ['green' if s >= threshold else 'orange' if s >= threshold - 10 else 'red' for s in scores]

    ax1.bar(laws, scores, color=colors, alpha=0.7)
    ax1.axhline(y=threshold, color='red', linestyle='--', alpha=0.5, label=f'Threshold ({threshold}%)')
    ax1.set_ylabel('Compliance Score (%)', fontsize=12)
    ax1.set_title('Individual Law Scores', fontsize=14)
    ax1.set_ylim([0, 100])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Overall compliance gauge
    ax2.barh(['Overall\nCompliance'], [overall_compliance], color='green' if passed else 'red', alpha=0.7)
    ax2.axvline(x=threshold, color='red', linestyle='--', alpha=0.5, label=f'Threshold ({threshold}%)')
    ax2.set_xlabel('Compliance Score (%)', fontsize=12)
    ax2.set_title('Overall Compliance', fontsize=14)
    ax2.set_xlim([0, 100])
    ax2.legend()
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    viz_file = OUTPUT_DIR / f"{out_prefix}_scores.png"
    plt.savefig(viz_file, dpi=300, bbox_inches='tight')
    plt.close()

    return {
        "message": response["message"],
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Detailed validation report JSON",
                "path": str(report_file.resolve())
            },
            {
                "description": "Iteration guidance document",
                "path": str(guidance_file.resolve())
            },
            {
                "description": "Scores breakdown visualization",
                "path": str(viz_file.resolve())
            }
        ]
    }


# ============================================================================
# Governed Response Composer Integration
# ============================================================================
# Import modular composer and register as MCP tool if available

try:
    from .governed_response_composer import (
        compose_governed_response_impl,
        check_claude_cli_available
    )

    @five_laws_validator_tutorial_mcp.tool
    def compose_governed_response(
        prompt: Annotated[str | None, "User's request/prompt for governed response generation"] = None,
        threshold: Annotated[float, "Minimum governance score required (0-100)"] = 80.0,
        max_iterations: Annotated[int, "Maximum refinement attempts"] = 3,
        strictness: Annotated[Literal["lenient", "moderate", "strict"],
                              "Validation strictness level: lenient (>=60%), moderate (>=70%), strict (>=85%)"] = "moderate",
        out_prefix: Annotated[str | None, "Output file prefix"] = None,
    ) -> dict:
        """
        Generate and iteratively refine AI response until it meets governance standards.

        This tool automatically generates responses using claude -p and refines them based on
        Five Laws validation feedback until they meet the threshold or max iterations is reached.

        Unlike the validator tools (which check existing text), this tool GENERATES governed text.

        Input: User prompt describing what to generate
        Output: Governed response with iteration history, pass/fail status, and improvement metrics

        Returns:
            Dictionary containing:
            - initial_response: First generated response (text, score, violations, recommendations)
            - final_response: Final refined response (text, score, violations, recommendations)
            - iterations: Number of refinement cycles performed (0 = immediate pass)
            - passed: Whether final response meets threshold
            - improvement: Score improvement in percentage points
            - database_path: SQLite file with complete iteration history
            - status: "success", "partial_success", "unavailable", or "failed"

        If Claude CLI unavailable: Returns status message directing to validator-only tools

        Reference: https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb
        """
        return compose_governed_response_impl(
            prompt=prompt,
            threshold=threshold,
            max_iterations=max_iterations,
            strictness=strictness,
            out_prefix=out_prefix,
            validator_instance=validator  # Pass existing validator instance
        )

    # Log successful registration
    print("[+] Governed Response Composer tool registered successfully")

except ImportError as e:
    # Module not available - skip tool registration
    # This is expected if governed_response_composer.py doesn't exist yet
    print(f"[!] Governed Response Composer not available: {e}")
    print("[!] Only validation tools will be available")
