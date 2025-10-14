"""
Tests for five_laws_iterative_validate in five_laws_validator_tutorial.py that reproduce the tutorial exactly.

Tutorial: SIM-ONE-MCP-v2/notebooks/five_laws_validator_tutorial/five_laws_validator_tutorial_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import json
from PIL import Image
import imagehash

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
def five_laws_iterative_validate_inputs(test_directories) -> dict:
    """Tutorial Example 8 - Iterative validation from cell 22"""
    return {
        "text": """
To solve this problem, I'll use a coordinated multi-protocol architecture:
1. ESL analyzes emotional context
2. REP handles logical reasoning with deductive inference
3. VVP validates rule structures before reasoning
4. Results validated against ground truth

This approach ensures deterministic outcomes through structured workflows
while maintaining computational efficiency through protocol specialization.
""",
        "threshold": 70.0,
        "strictness": "moderate",
        "out_prefix": "test_iterative_validation"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_five_laws_iterative_validate(server, five_laws_iterative_validate_inputs, test_directories):
    """Test iterative validation from tutorial Example 8 (cell 22)"""
    async with Client(server) as client:
        result = await client.call_tool("five_laws_iterative_validate", five_laws_iterative_validate_inputs)

        # Extract result data
        assert hasattr(result, 'content'), "Result should have content attribute"
        assert len(result.content) > 0, "Result content should not be empty"

        result_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
        result_data = json.loads(result_text)

        # 1. File Output Verification - Tutorial creates 3 files
        expected_files = ["test_iterative_validation_report.json",
                         "test_iterative_validation_guidance.txt",
                         "test_iterative_validation_scores.png"]
        artifacts = result_data.get("artifacts", [])

        assert len(artifacts) == 3, f"Expected 3 output files, got {len(artifacts)}"

        for expected_file in expected_files:
            file_found = any(expected_file in artifact.get("path", "") for artifact in artifacts)
            assert file_found, f"Expected output file {expected_file} not found in artifacts"

        # 2. Verify files exist on disk
        report_file = None
        guidance_file = None
        viz_file = None

        for artifact in artifacts:
            file_path = pathlib.Path(artifact.get("path", ""))
            assert file_path.exists(), f"Output file should exist: {file_path}"

            if "report.json" in artifact.get("path", ""):
                report_file = file_path
            elif "guidance.txt" in artifact.get("path", ""):
                guidance_file = file_path
            elif "scores.png" in artifact.get("path", ""):
                viz_file = file_path

        # 3. Verify detailed report JSON
        assert report_file is not None, "Report JSON file should exist"
        with open(report_file, 'r') as f:
            report = json.load(f)

        # Verify report structure
        assert "text" in report, "Report should include validated text"
        assert "validation_result" in report, "Report should include validation result"
        assert "violations" in report, "Report should include violations"
        assert "recommendations" in report, "Report should include recommendations"
        assert "strengths" in report, "Report should include strengths"
        assert "message" in report, "Report should include message"

        validation_result = report["validation_result"]
        assert "overall_compliance" in validation_result, "Should have overall compliance score"
        assert "individual_scores" in validation_result, "Should have individual law scores"
        assert "pass_fail_status" in validation_result, "Should have pass/fail status"
        assert "passed_threshold" in validation_result, "Should have passed threshold flag"
        assert validation_result["threshold"] == 70.0, "Threshold should be 70.0%"
        assert validation_result["strictness"] == "moderate", "Strictness should be moderate"

        # 4. Verify validation scores match tutorial Example 1 (cell 22)
        # Tutorial shows this text passes with score: 84.0%
        overall_compliance = validation_result["overall_compliance"]
        assert overall_compliance == pytest.approx(84.0, rel=0.1), \
            f"Overall compliance {overall_compliance}% differs from tutorial 84.0% by more than 10%"

        assert validation_result["passed_threshold"] is True, \
            "Text should pass 70.0% threshold (tutorial shows 84.0%)"

        # 5. Individual scores verification
        individual_scores = validation_result["individual_scores"]
        assert "law1_architectural_intelligence" in individual_scores
        assert "law2_cognitive_governance" in individual_scores
        assert "law3_truth_foundation" in individual_scores
        assert "law4_energy_stewardship" in individual_scores
        assert "law5_deterministic_reliability" in individual_scores

        # 6. Verify guidance file content
        assert guidance_file is not None and guidance_file.exists(), "Guidance file should exist"
        with open(guidance_file, 'r') as f:
            guidance_content = f.read()

        assert "Iterative Validation Guidance" in guidance_content, "Guidance should have title"
        assert "Overall Compliance:" in guidance_content, "Guidance should show overall compliance"
        assert "Threshold:" in guidance_content, "Guidance should show threshold"
        assert "Status:" in guidance_content, "Guidance should show status"

        # Since this text passes, guidance should indicate success
        assert "PASSED" in guidance_content or "meets" in guidance_content.lower(), \
            "Guidance should indicate validation passed"

        # 7. Message verification
        message = result_data.get("message", "")
        assert "[+] Validation passed!" in message or "passed" in message.lower(), \
            "Message should indicate validation passed"
        assert "84.0%" in message or "84%" in message, "Message should include compliance score"
        assert "70" in message, "Message should reference threshold"

        # 8. Image Verification - scores breakdown visualization should exist
        assert viz_file is not None and viz_file.exists(), "Scores visualization file should exist"

        # Verify the image is a valid PNG
        try:
            img = Image.open(viz_file)
            assert img.format == 'PNG', "Visualization should be PNG format"
            assert img.size[0] > 0 and img.size[1] > 0, "Image should have valid dimensions"
        except Exception as e:
            pytest.fail(f"Failed to open or validate visualization image: {e}")
