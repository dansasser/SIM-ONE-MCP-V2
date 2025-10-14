"""
Tests for five_laws_validate_text in five_laws_validator_tutorial.py that reproduce the tutorial exactly.

Tutorial: SIM-ONE-MCP-v2/notebooks/five_laws_validator_tutorial/five_laws_validator_tutorial_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import json

# Add project root to Python path to enable src imports
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# ========= Fixtures =========
@pytest.fixture
def server(test_directories):
    """FastMCP server fixture with the five_laws_validator_tutorial tool."""
    # Force module reload
    module_name = 'src.tools.five_laws_validator_tutorial'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.five_laws_validator_tutorial
    return src.tools.five_laws_validator_tutorial.five_laws_validator_tutorial_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "five_laws_validator_tutorial"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "five_laws_validator_tutorial"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("FIVE_LAWS_VALIDATOR_TUTORIAL_INPUT_DIR")
    old_output_dir = os.environ.get("FIVE_LAWS_VALIDATOR_TUTORIAL_OUTPUT_DIR")

    os.environ["FIVE_LAWS_VALIDATOR_TUTORIAL_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["FIVE_LAWS_VALIDATOR_TUTORIAL_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["FIVE_LAWS_VALIDATOR_TUTORIAL_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("FIVE_LAWS_VALIDATOR_TUTORIAL_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["FIVE_LAWS_VALIDATOR_TUTORIAL_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("FIVE_LAWS_VALIDATOR_TUTORIAL_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========

@pytest.fixture
def five_laws_validate_text_inputs(test_directories) -> dict:
    """Tutorial Example 1 - Compliant text from cell 9"""
    return {
        "text": """
To analyze this dataset, I will use a coordinated multi-protocol approach:

1. ESL protocol will assess emotional context
2. REP protocol will handle logical reasoning
3. Results will be validated against ground truth

This architecture leverages protocol specialization for efficient processing
while maintaining deterministic outcomes through structured workflows.
""",
        "strictness": "moderate",
        "context_domain": None,
        "context_use_case": None,
        "out_prefix": "test_compliant_text"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_five_laws_validate_text(server, five_laws_validate_text_inputs, test_directories):
    """Test validation of compliant text from tutorial Example 1 (cell 9)"""
    async with Client(server) as client:
        result = await client.call_tool("five_laws_validate_text", five_laws_validate_text_inputs)

        # Extract result data - result is a CallToolResult with content list
        assert hasattr(result, 'content'), "Result should have content attribute"
        assert len(result.content) > 0, "Result content should not be empty"

        # Get the text from first content item
        result_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])

        # Parse JSON from result text
        result_data = json.loads(result_text)

        # 1. File Output Verification - Tutorial creates 2 files
        expected_files = ["test_compliant_text_results.json", "test_compliant_text_summary.txt"]
        artifacts = result_data.get("artifacts", [])

        assert len(artifacts) == 2, f"Expected 2 output files, got {len(artifacts)}"

        for expected_file in expected_files:
            file_found = any(expected_file in artifact.get("path", "") for artifact in artifacts)
            assert file_found, f"Expected output file {expected_file} not found in artifacts"

        # 2. Verify files exist on disk
        for artifact in artifacts:
            file_path = pathlib.Path(artifact.get("path", ""))
            assert file_path.exists(), f"Output file should exist: {file_path}"

        # 3. Verify JSON results file content
        results_file = None
        for artifact in artifacts:
            if "results.json" in artifact.get("path", ""):
                results_file = pathlib.Path(artifact["path"])
                break

        assert results_file is not None, "Results JSON file should be in artifacts"

        with open(results_file, 'r') as f:
            saved_results = json.load(f)

        # 4. Verify validation scores match tutorial Example 1 (cell 9) outputs
        # Tutorial shows: overall_compliance: 85.0%
        validation_result = saved_results.get("validation_result", {})
        scores = validation_result.get("scores", {})

        overall_compliance = scores.get("overall_compliance", 0)
        assert overall_compliance == pytest.approx(85.0, rel=0.1), \
            f"Overall compliance {overall_compliance}% differs from tutorial 85.0% by more than 10%"

        # 5. Individual law scores from tutorial
        # Law 1: 100.0%, Law 2: 100.0%, Law 3: 95.0%, Law 4: 65.0%, Law 5: 65.0%
        assert scores.get("law1_architectural_intelligence", 0) == pytest.approx(100.0, rel=0.1), \
            "Law 1 score mismatch (tutorial shows 100.0%)"
        assert scores.get("law2_cognitive_governance", 0) == pytest.approx(100.0, rel=0.1), \
            "Law 2 score mismatch (tutorial shows 100.0%)"
        assert scores.get("law3_truth_foundation", 0) == pytest.approx(95.0, rel=0.1), \
            "Law 3 score mismatch (tutorial shows 95.0%)"
        assert scores.get("law4_energy_stewardship", 0) == pytest.approx(65.0, rel=0.1), \
            "Law 4 score mismatch (tutorial shows 65.0%)"
        assert scores.get("law5_deterministic_reliability", 0) == pytest.approx(65.0, rel=0.1), \
            "Law 5 score mismatch (tutorial shows 65.0%)"

        # 6. Pass/Fail status verification
        assert validation_result.get("pass_fail_status") == "PASS", \
            "Tutorial Example 1 should PASS with moderate strictness"
        assert validation_result.get("strictness_level") == "moderate", \
            "Strictness level should be moderate"
        assert validation_result.get("threshold") == 70.0, \
            "Moderate threshold should be 70.0%"

        # 7. Strengths verification - Tutorial shows 3 strengths (Law 1, 2, 3)
        strengths = validation_result.get("strengths", [])
        assert len(strengths) == 3, f"Expected 3 strengths, got {len(strengths)}"

        # 8. Message verification
        message = result_data.get("message", "")
        assert "passed" in message.lower(), "Message should indicate validation passed"
        assert "85.0%" in message or "85%" in message, "Message should include compliance score"
