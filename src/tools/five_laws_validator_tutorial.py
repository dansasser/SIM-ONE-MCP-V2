"""
Five Laws Cognitive Governance Validator tools for AI content validation.

This MCP Server provides 3 tools:
1. five_laws_validate_text: Validate single text against Five Laws with configurable strictness
2. five_laws_batch_validate: Compare multiple texts and identify best performers
3. five_laws_iterative_validate: Iterative refinement workflow with feedback tracking

All tools extracted from https://github.com/dansasser/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb
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

# Logging
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from logging_config import setup_logger

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

# Initialize logger
logger = setup_logger("five_laws_validator", "five_laws_validator.log")

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
        # Log validation start
        logger.debug(f"[CORE] validator.validate() called | strictness={strictness} | text_length={len(text) if text else 0}")

        if not text or not text.strip():
            logger.error("[CORE] Validation failed: empty text provided")
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

        # Log validation completion
        logger.debug(f"[CORE] validator.validate() completed | overall_score={overall_compliance:.1f}% | status={status} | violations={len(all_violations)} | recommendations={len(all_recommendations)}")

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
    import time
    start_time = time.time()

    # Log invocation
    logger.info(f"[START] five_laws_validate_text invoked | strictness={strictness} | text_length={len(text) if text else 0} | context_domain={context_domain} | context_use_case={context_use_case}")

    # Input validation
    if text is None:
        logger.error("Validation failed: Text to validate must be provided")
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
    logger.debug(f"Validating text with validator instance | strictness={strictness}")
    result = validator.validate(text, strictness=strictness, context=context)

    # Log validation results
    overall_score = result['scores']['overall_compliance']
    status = result['pass_fail_status']
    violations_count = len(result.get('violations', []))
    recommendations_count = len(result.get('recommendations', []))

    logger.info(f"Validation completed | overall_score={overall_score:.1f}% | status={status} | violations={violations_count} | recommendations={recommendations_count}")
    logger.debug(f"Individual scores | law1={result['scores']['law1_architectural_intelligence']:.1f} | law2={result['scores']['law2_cognitive_governance']:.1f} | law3={result['scores']['law3_truth_foundation']:.1f} | law4={result['scores']['law4_energy_stewardship']:.1f} | law5={result['scores']['law5_deterministic_reliability']:.1f}")

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

    # Log performance metrics
    duration = time.time() - start_time
    logger.info(f"[SUCCESS] five_laws_validate_text completed | duration={duration:.3f}s | output_files=2")
    logger.debug(f"Output files | results={results_file.name} | summary={summary_file.name}")

    return {
        "message": f"Validation {'passed' if result['pass_fail_status'] == 'PASS' else 'failed'}: {result['scores']['overall_compliance']:.1f}% compliance",
        "reference": "https://github.com/dansasser/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
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
    import time
    start_time = time.time()

    # Log invocation
    logger.info(f"[START] five_laws_batch_validate invoked | batch_size={len(texts) if texts else 0} | strictness={strictness}")

    # Input validation
    if texts is None:
        logger.error("Batch validation failed: List of texts to validate must be provided")
        raise ValueError("List of texts to validate must be provided")

    if not isinstance(texts, list) or len(texts) == 0:
        logger.error(f"Batch validation failed: texts must be a non-empty list | type={type(texts)} | length={len(texts) if isinstance(texts, list) else 'N/A'}")
        raise ValueError("texts must be a non-empty list")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"five_laws_batch_{timestamp}"

    # Validate all texts
    logger.debug(f"Starting batch validation loop for {len(texts)} texts")
    results = []
    for i, text in enumerate(texts, 1):
        result = validator.validate(text, strictness=strictness)
        score = result["scores"]["overall_compliance"]
        status = result["pass_fail_status"]

        logger.debug(f"Text {i}/{len(texts)} validated | score={score:.1f}% | status={status}")

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

    # Log statistics
    logger.info(f"Batch statistics | passed={stats['passed']}/{stats['total_responses']} | avg_score={stats['average_compliance']:.1f}% | best_id={stats['best_response_id']} | worst_id={stats['worst_response_id']}")

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

    # Log visualization creation
    logger.debug(f"Visualization created | file={viz_file.name} | chart_type=grouped_bar | laws=5")

    # Log performance metrics
    duration = time.time() - start_time
    logger.info(f"[SUCCESS] five_laws_batch_validate completed | duration={duration:.3f}s | batch_size={len(texts)} | passed_ratio={stats['passed']}/{stats['total_responses']} | output_files=3")
    logger.debug(f"Output files | table={table_file.name} | stats={stats_file.name} | viz={viz_file.name}")

    return {
        "message": f"Batch validation completed: {stats['passed']}/{stats['total_responses']} passed, avg {stats['average_compliance']:.1f}%",
        "reference": "https://github.com/dansasser/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
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
    import time
    start_time = time.time()

    # Log invocation
    logger.info(f"[START] five_laws_iterative_validate invoked | threshold={threshold} | strictness={strictness} | text_length={len(text) if text else 0}")

    # Input validation
    if text is None:
        logger.error("Iterative validation failed: Text to validate must be provided")
        raise ValueError("Text to validate must be provided")

    # Set output prefix
    if out_prefix is None:
        out_prefix = f"five_laws_iterative_{timestamp}"

    # Validate the text
    logger.debug(f"Validating text iteratively | strictness={strictness} | threshold={threshold}")
    result = validator.validate(text, strictness=strictness)

    # Extract key metrics
    overall_compliance = result["scores"]["overall_compliance"]
    status = result["pass_fail_status"]
    passed = overall_compliance >= threshold

    # Log validation results
    violations_count = len(result.get("violations", []))
    recommendations_count = len(result.get("recommendations", []))
    gap = threshold - overall_compliance if not passed else 0.0

    logger.info(f"Iterative validation completed | overall_score={overall_compliance:.1f}% | threshold={threshold}% | passed={passed} | gap={gap:.1f} | violations={violations_count} | recommendations={recommendations_count}")
    logger.debug(f"Individual scores | law1={result['scores']['law1_architectural_intelligence']:.1f} | law2={result['scores']['law2_cognitive_governance']:.1f} | law3={result['scores']['law3_truth_foundation']:.1f} | law4={result['scores']['law4_energy_stewardship']:.1f} | law5={result['scores']['law5_deterministic_reliability']:.1f}")

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
    logger.debug(f"Report file created | file={report_file.name} | size={report_file.stat().st_size} bytes")

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

    logger.debug(f"Guidance file created | file={guidance_file.name} | size={guidance_file.stat().st_size} bytes | passed={passed}")

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

    # Log visualization creation
    logger.debug(f"Visualization created | file={viz_file.name} | chart_type=dual_chart | laws=5")

    # Log performance metrics
    duration = time.time() - start_time
    logger.info(f"[SUCCESS] five_laws_iterative_validate completed | duration={duration:.3f}s | passed={passed} | gap={gap:.1f} | output_files=3")
    logger.debug(f"Output files | report={report_file.name} | guidance={guidance_file.name} | viz={viz_file.name}")

    return {
        "message": response["message"],
        "reference": "https://github.com/dansasser/SIM-ONE/blob/main/tutorials/five_laws_validator_tutorial.ipynb",
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
            Dictionary with standardized structure across all status values:

            Common fields (always present):
            - status (str): "success", "partial_success", "unavailable", or "failed"
            - message (str): Human-readable description of result
            - passed (bool): Whether response meets threshold (False for errors)
            - iterations (int): Number of refinement cycles (0 for errors)
            - reference (str): Tutorial reference URL

            Success/partial_success additional fields:
            - final_score (float): Final governance score percentage
            - initial_score (float): Initial governance score percentage
            - improvement (float): Score improvement in percentage points
            - database_path (str): SQLite file with complete iteration history
            - summary_file (str): JSON summary file path

            Error additional fields:
            - error (str): Error message describing what went wrong
            - suggestion (str): Suggested alternative actions (for "unavailable" status)
            - database_path (str): May be present for "failed" status

        Reference: https://github.com/dansasser/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb
        """
        # Log wrapper invocation
        logger.info(f"[WRAPPER] compose_governed_response invoked | threshold={threshold} | max_iterations={max_iterations} | strictness={strictness} | prompt_length={len(prompt) if prompt else 0}")

        # Call implementation (which has comprehensive logging)
        result = compose_governed_response_impl(
            prompt=prompt,
            threshold=threshold,
            max_iterations=max_iterations,
            strictness=strictness,
            out_prefix=out_prefix,
            validator_instance=validator  # Pass existing validator instance
        )

        # Log wrapper completion
        status = result.get("status", "unknown")
        passed = result.get("passed", False)
        iterations = result.get("iterations", 0)
        logger.info(f"[WRAPPER] compose_governed_response completed | status={status} | passed={passed} | iterations={iterations}")

        # Standardize return structure for all status values
        if status in ["success", "partial_success"]:
            # Success case - extract metrics and format message
            final_score = result.get("final_response", {}).get("score", 0)
            initial_score = result.get("initial_response", {}).get("score", 0)
            improvement = result.get("improvement", 0)

            message = f"""✅ Governed Response Generated Successfully

**Status:** {'PASSED' if passed else 'NEEDS IMPROVEMENT'}
**Final Score:** {final_score:.1f}%
**Initial Score:** {initial_score:.1f}%
**Improvement:** {improvement:+.1f}%
**Refinement Iterations:** {iterations}

**Generated Response:**
{result.get('final_response', {}).get('text', '')[:500]}...

**Artifacts:**
- Database: {result.get('database_path', 'N/A')}
- Summary: {result.get('summary_file', 'N/A')}

Reference: {result.get('reference', '')}
"""
            return {
                "status": status,
                "message": message,
                "passed": passed,
                "iterations": iterations,
                "final_score": final_score,
                "initial_score": initial_score,
                "improvement": improvement,
                "database_path": result.get("database_path"),
                "summary_file": result.get("summary_file"),
                "reference": result.get("reference")
            }
        else:
            # Error cases - normalize structure to match documented schema
            error_msg = result.get("error", "Unknown error")

            # Build consistent error message
            if status == "unavailable":
                message = f"❌ {error_msg}\n\n{result.get('message', '')}"
                if result.get("suggestion"):
                    message += f"\n\nSuggestion: {result['suggestion']}"
            elif status == "failed":
                message = f"❌ Governed response generation failed: {error_msg}"
            else:
                message = f"❌ Error: {error_msg}"

            # Return normalized error structure
            response = {
                "status": status,
                "message": message,
                "passed": False,
                "iterations": 0,
                "error": error_msg,
                "reference": result.get("reference", "https://github.com/dansasser/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb")
            }

            # Add optional fields if present
            if "suggestion" in result:
                response["suggestion"] = result["suggestion"]
            if "database_path" in result:
                response["database_path"] = result["database_path"]

            return response

    # Log successful registration
    logger.info("Governed Response Composer tool registered successfully")

except ImportError as e:
    # Module not available - skip tool registration
    # This is expected if governed_response_composer.py doesn't exist yet
    logger.warning(f"Governed Response Composer not available: {e}")
    logger.warning("Only validation tools will be available")
