"""
Governed Response Composer - Iterative AI refinement with Five Laws governance.

This module implements automated response generation and refinement using:
- Claude CLI (claude -p) for response generation
- Five Laws Validator for governance checking
- SQLite database for iteration persistence
- MCP connector integration for framework documentation

Designed as a modular component imported by five_laws_validator_tutorial.py.

Extracted from: https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb
"""

import subprocess
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Literal, Dict, Any, Tuple
import os

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_DB_DIR = PROJECT_ROOT / "tmp" / "iterations"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

DB_DIR = Path(os.environ.get("GOVERNED_RESPONSE_DB_DIR", DEFAULT_DB_DIR))
OUTPUT_DIR = Path(os.environ.get("GOVERNED_RESPONSE_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Section 1: Claude CLI Interface
# ============================================================================

def check_claude_cli_available() -> Tuple[bool, str]:
    """
    Check if Claude CLI is available and functional.

    Returns:
        (available: bool, message: str)
        - (True, "Claude CLI available: version") if working
        - (False, "error message") if not available
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, f"Claude CLI available: {result.stdout.strip()}"
        else:
            return False, f"Claude CLI error: {result.stderr}"
    except FileNotFoundError:
        return False, "Claude CLI not found. Install with: pip install claude-cli"
    except subprocess.TimeoutExpired:
        return False, "Claude CLI check timed out"
    except Exception as e:
        return False, f"Unexpected error checking Claude CLI: {str(e)}"


def _generate_response(prompt: str, is_initial: bool = True, timeout: int = 120) -> str:
    """
    Generate response using Claude Code CLI.

    Args:
        prompt: The prompt to send to Claude
        is_initial: Whether this is initial generation (adds MCP instruction)
        timeout: Maximum seconds to wait for response

    Returns:
        Generated response text

    Raises:
        RuntimeError: If Claude CLI fails or times out
        FileNotFoundError: If Claude CLI not installed
    """
    # Add MCP connector instruction for initial generation
    if is_initial:
        full_prompt = f"""Before responding, use the SIM-ONE MCP connector to review the latest SIM-ONE Framework documentation, especially the Five Laws of Cognitive Governance.

User request: {prompt}

Generate a response that adheres to the SIM-ONE Framework's Five Laws."""
    else:
        # Refinement prompts already include MCP instruction
        full_prompt = prompt

    try:
        result = subprocess.run(
            ["claude", "-p", full_prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude Code CLI error: {result.stderr}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude Code CLI timed out after {timeout} seconds")
    except FileNotFoundError:
        raise FileNotFoundError(
            "Claude Code CLI not found. Please install and authenticate:\n"
            "  pip install claude-cli\n"
            "  claude auth"
        )


# ============================================================================
# Section 2: SQLite Persistence Layer
# ============================================================================

class IterationDatabase:
    """
    SQLite database for storing iteration history.

    Schema:
        sessions: session_id, prompt, threshold, strictness, created_at
        iterations: iteration_id, session_id, iteration_num, text, score,
                   passed, violations_json, recommendations_json, created_at
    """

    def __init__(self, db_path: Path):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                threshold REAL NOT NULL,
                strictness TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Iterations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iterations (
                iteration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                iteration_num INTEGER NOT NULL,
                text TEXT NOT NULL,
                score REAL NOT NULL,
                passed BOOLEAN NOT NULL,
                violations_json TEXT,
                recommendations_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        self.conn.commit()

    def create_session(self, prompt: str, threshold: float, strictness: str) -> int:
        """
        Create new refinement session.

        Returns:
            session_id (int)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (prompt, threshold, strictness)
            VALUES (?, ?, ?)
        """, (prompt, threshold, strictness))
        self.conn.commit()
        return cursor.lastrowid

    def add_iteration(
        self,
        session_id: int,
        iteration_num: int,
        text: str,
        score: float,
        passed: bool,
        violations: list,
        recommendations: list
    ):
        """Store iteration result."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO iterations
            (session_id, iteration_num, text, score, passed, violations_json, recommendations_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            iteration_num,
            text,
            score,
            passed,
            json.dumps(violations),
            json.dumps(recommendations)
        ))
        self.conn.commit()

    def get_session_history(self, session_id: int) -> list:
        """Retrieve all iterations for a session."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT iteration_num, text, score, passed,
                   violations_json, recommendations_json, created_at
            FROM iterations
            WHERE session_id = ?
            ORDER BY iteration_num
        """, (session_id,))

        rows = cursor.fetchall()
        return [
            {
                "iteration": row["iteration_num"],
                "text": row["text"],
                "score": row["score"],
                "passed": bool(row["passed"]),
                "violations": json.loads(row["violations_json"]),
                "recommendations": json.loads(row["recommendations_json"]),
                "timestamp": row["created_at"]
            }
            for row in rows
        ]

    def close(self):
        """Close database connection."""
        self.conn.close()


# ============================================================================
# Section 3: Refinement Logic
# ============================================================================

def _create_refinement_prompt(
    original_prompt: str,
    previous_response: str,
    validation_result: dict,
    threshold: float
) -> str:
    """
    Create refinement prompt with MCP connector instruction.

    Args:
        original_prompt: The original user prompt
        previous_response: The response that failed validation
        validation_result: Dict with 'scores', 'violations', 'recommendations'
        threshold: The threshold score to achieve

    Returns:
        Refinement prompt for Claude Code
    """
    # Identify which laws failed (score < threshold)
    failed_laws = []
    individual_scores = validation_result.get('individual_scores',
                                             validation_result.get('scores', {}))

    for law_name, score in individual_scores.items():
        if law_name == 'overall_compliance':
            continue
        if score < threshold:
            # Convert law1_architectural_intelligence -> Law 1 (Architectural Intelligence)
            law_num = law_name.split('_')[0].replace('law', 'Law ')
            law_title = ' '.join(law_name.split('_')[1:]).replace('_', ' ').title()
            failed_laws.append(f"{law_num} ({law_title})")

    # Get overall score
    overall_score = validation_result.get('scores', {}).get('overall_compliance',
                    validation_result.get('overall_compliance', 0.0))

    # Get violations and recommendations (limit to top 5 each)
    violations = validation_result.get('violations', [])[:5]
    recommendations = validation_result.get('recommendations', [])[:5]

    prompt = f"""Before responding, use the SIM-ONE MCP connector to review the latest SIM-ONE Framework documentation, especially regarding:
{chr(10).join(f"- {law}" for law in failed_laws) if failed_laws else "- All Five Laws of Cognitive Governance"}

Original user request: {original_prompt}

Previous response:
{previous_response}

Governance validation score: {overall_score:.1f}%
Target threshold: {threshold}%

Issues found:
{chr(10).join(f"- {v}" for v in violations) if violations else "- (No specific violations listed)"}

Recommendations for improvement:
{chr(10).join(f"- {r}" for r in recommendations) if recommendations else "- (No specific recommendations)"}

Please revise the response using the SIM-ONE Framework documentation to address these specific governance issues and improve the score above {threshold}%.
Focus on the laws that scored below threshold: {', '.join(failed_laws) if failed_laws else 'all laws'}."""

    return prompt


def compose_governed_response_impl(
    prompt: Optional[str],
    threshold: float,
    max_iterations: int,
    strictness: Literal["lenient", "moderate", "strict"],
    out_prefix: Optional[str],
    validator_instance
) -> dict:
    """
    Implementation of compose_governed_response tool.

    Args:
        prompt: User's request/prompt
        threshold: Minimum governance score required (0-100)
        max_iterations: Maximum refinement attempts
        strictness: Validation strictness level
        out_prefix: Output file prefix
        validator_instance: FiveLawsValidator instance from parent module

    Returns:
        Dictionary with initial_response, final_response, iterations, passed, improvement
    """
    # === Validation ===
    if prompt is None or not prompt.strip():
        return {
            "error": "Prompt cannot be empty",
            "status": "failed",
            "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb"
        }

    # === Check Claude CLI availability ===
    cli_available, cli_message = check_claude_cli_available()
    if not cli_available:
        return {
            "error": "Claude CLI not available",
            "message": cli_message,
            "status": "unavailable",
            "suggestion": "Use five_laws_validate_text or five_laws_iterative_validate for validation-only workflows",
            "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb"
        }

    # === Setup ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if out_prefix is None:
        out_prefix = f"governed_response_{timestamp}"

    # Initialize database
    db_path = DB_DIR / f"{out_prefix}.db"
    db = IterationDatabase(db_path)
    session_id = db.create_session(prompt, threshold, strictness)

    try:
        # === Step 1: Generate initial response ===
        print(f"[1/3] Generating initial response...")
        initial_text = _generate_response(prompt, is_initial=True)
        print(f"      Generated {len(initial_text)} characters")

        # === Step 2: Validate initial response ===
        print(f"[2/3] Validating initial response...")
        initial_validation = validator_instance.validate(initial_text, strictness=strictness)
        initial_score = initial_validation["scores"]["overall_compliance"]
        initial_passed = initial_validation["pass_fail_status"] == "PASS"
        print(f"      Score: {initial_score:.1f}%")

        # Store initial iteration
        db.add_iteration(
            session_id=session_id,
            iteration_num=0,
            text=initial_text,
            score=initial_score,
            passed=initial_passed,
            violations=initial_validation.get("violations", []),
            recommendations=initial_validation.get("recommendations", [])
        )

        # === Step 3: Check if initial response already passed ===
        if initial_passed:
            print(f"      [PASS] Initial response passes validation!")

            db.close()

            return {
                "initial_response": {
                    "text": initial_text,
                    "score": initial_score,
                    "violations": initial_validation.get("violations", []),
                    "recommendations": initial_validation.get("recommendations", [])
                },
                "final_response": {
                    "text": initial_text,
                    "score": initial_score,
                    "violations": initial_validation.get("violations", []),
                    "recommendations": initial_validation.get("recommendations", [])
                },
                "iterations": 0,
                "passed": True,
                "improvement": 0.0,
                "status": "success",
                "database_path": str(db_path.resolve()),
                "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb"
            }

        # === Step 4: Iterative refinement loop ===
        print(f"[3/3] Refining response...")
        current_text = initial_text
        current_validation = initial_validation
        current_score = initial_score

        for iteration_num in range(1, max_iterations + 1):
            # Check if passed
            if current_validation["pass_fail_status"] == "PASS":
                print(f"      [PASS] Validation passed after {iteration_num - 1} iterations!")
                break

            print(f"      [Iteration {iteration_num}] Score {current_score:.1f}% - refining...")

            # Create refinement prompt
            refinement_prompt = _create_refinement_prompt(
                original_prompt=prompt,
                previous_response=current_text,
                validation_result=current_validation,
                threshold=threshold
            )

            # Generate refined response
            current_text = _generate_response(refinement_prompt, is_initial=False)

            # Validate refined response
            current_validation = validator_instance.validate(current_text, strictness=strictness)
            current_score = current_validation["scores"]["overall_compliance"]

            print(f"      [Iteration {iteration_num}] New score: {current_score:.1f}%")

            # Store iteration
            db.add_iteration(
                session_id=session_id,
                iteration_num=iteration_num,
                text=current_text,
                score=current_score,
                passed=current_validation["pass_fail_status"] == "PASS",
                violations=current_validation.get("violations", []),
                recommendations=current_validation.get("recommendations", [])
            )

        # === Step 5: Calculate results ===
        improvement = current_score - initial_score
        passed = current_validation["pass_fail_status"] == "PASS"

        final_iteration_num = iteration_num if iteration_num > 0 else 0

        print(f"\n[+] Complete! Final score: {current_score:.1f}% | Improvement: {improvement:+.1f}% | Status: {'PASS' if passed else 'FAIL'}\n")

        # === Step 6: Save summary JSON ===
        summary_file = OUTPUT_DIR / f"{out_prefix}_summary.json"
        summary_data = {
            "prompt": prompt,
            "threshold": threshold,
            "strictness": strictness,
            "max_iterations": max_iterations,
            "initial_score": initial_score,
            "final_score": current_score,
            "improvement": improvement,
            "iterations_used": final_iteration_num,
            "passed": passed,
            "timestamp": timestamp
        }
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)

        db.close()

        # === Return results ===
        return {
            "initial_response": {
                "text": initial_text,
                "score": initial_score,
                "violations": initial_validation.get("violations", []),
                "recommendations": initial_validation.get("recommendations", [])
            },
            "final_response": {
                "text": current_text,
                "score": current_score,
                "violations": current_validation.get("violations", []),
                "recommendations": current_validation.get("recommendations", [])
            },
            "iterations": final_iteration_num,
            "passed": passed,
            "improvement": improvement,
            "status": "success" if passed else "partial_success",
            "database_path": str(db_path.resolve()),
            "summary_file": str(summary_file.resolve()),
            "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb"
        }

    except Exception as e:
        db.close()
        return {
            "error": str(e),
            "status": "failed",
            "database_path": str(db_path.resolve()),
            "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/governed_response_composer_tutorial.ipynb"
        }
