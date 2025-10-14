"""
Tests for five_laws_batch_validate in five_laws_validator_tutorial.py that reproduce the tutorial exactly.

Tutorial: SIM-ONE-MCP-v2/notebooks/five_laws_validator_tutorial/five_laws_validator_tutorial_execution_final.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import json
import pandas as pd
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
def five_laws_batch_validate_inputs(test_directories) -> dict:
    """Tutorial Example 7 - Batch validation from cell 20"""
    return {
        "texts": [
            "Use a coordinated multi-protocol architecture for efficient processing.",
            "Just throw everything at a large language model.",
            "Apply ESL for emotion analysis, then REP for reasoning with validation.",
            "Try different approaches until something works.",
            "Implement deterministic workflows with protocol specialization."
        ],
        "strictness": "moderate",
        "out_prefix": "test_batch_validation"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_five_laws_batch_validate(server, five_laws_batch_validate_inputs, test_directories):
    """Test batch validation from tutorial Example 7 (cell 20)"""
    async with Client(server) as client:
        result = await client.call_tool("five_laws_batch_validate", five_laws_batch_validate_inputs)

        # Extract result data
        assert hasattr(result, 'content'), "Result should have content attribute"
        assert len(result.content) > 0, "Result content should not be empty"

        result_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
        result_data = json.loads(result_text)

        # 1. File Output Verification - Tutorial creates 3 files
        expected_files = ["test_batch_validation_comparison.csv",
                         "test_batch_validation_statistics.json",
                         "test_batch_validation_comparison.png"]
        artifacts = result_data.get("artifacts", [])

        assert len(artifacts) == 3, f"Expected 3 output files, got {len(artifacts)}"

        for expected_file in expected_files:
            file_found = any(expected_file in artifact.get("path", "") for artifact in artifacts)
            assert file_found, f"Expected output file {expected_file} not found in artifacts"

        # 2. Verify files exist on disk
        csv_file = None
        stats_file = None
        viz_file = None

        for artifact in artifacts:
            file_path = pathlib.Path(artifact.get("path", ""))
            assert file_path.exists(), f"Output file should exist: {file_path}"

            if "comparison.csv" in artifact.get("path", ""):
                csv_file = file_path
            elif "statistics.json" in artifact.get("path", ""):
                stats_file = file_path
            elif "comparison.png" in artifact.get("path", ""):
                viz_file = file_path

        # 3. Verify CSV comparison table
        assert csv_file is not None, "CSV comparison file should exist"
        df = pd.read_csv(csv_file)

        # Tutorial validates 5 responses
        assert len(df) == 5, f"Expected 5 responses in comparison table, got {len(df)}"

        # Verify columns exist
        expected_columns = ['id', 'text_preview', 'overall', 'law1', 'law2', 'law3', 'law4', 'law5',
                           'status', 'violations', 'recommendations']
        for col in expected_columns:
            assert col in df.columns, f"Expected column '{col}' not found in comparison table"

        # 4. Verify statistics file
        assert stats_file is not None, "Statistics file should exist"
        with open(stats_file, 'r') as f:
            stats = json.load(f)

        # Verify statistics structure
        assert stats.get("total_responses") == 5, "Should have 5 total responses"
        assert "passed" in stats, "Stats should include passed count"
        assert "conditional" in stats, "Stats should include conditional count"
        assert "failed" in stats, "Stats should include failed count"
        assert "average_compliance" in stats, "Stats should include average compliance"
        assert "best_response_id" in stats, "Stats should include best response ID"
        assert "worst_response_id" in stats, "Stats should include worst response ID"
        assert stats.get("strictness_level") == "moderate", "Strictness level should be moderate"

        # 5. Verify specific response scores from tutorial output (cell 20)
        # Response 1: Good architectural text - should have high Law 1 score
        # Response 2: "throw everything" - should fail (brute force)
        # Response 5: "deterministic workflows" - should pass

        # Check Response 1 (coordinated multi-protocol)
        resp1 = df[df['id'] == 1].iloc[0]
        assert resp1['law1'] >= 80.0, "Response 1 should have high Law 1 (architectural) score"
        assert resp1['status'] in ['PASS', 'CONDITIONAL'], "Response 1 should pass or be conditional"

        # Check Response 2 (throw everything) - should fail
        resp2 = df[df['id'] == 2].iloc[0]
        assert resp2['overall'] < 70.0, "Response 2 (brute force) should fail moderate threshold"
        assert resp2['status'] in ['FAIL', 'CONDITIONAL'], "Response 2 should fail or be conditional"

        # Check Response 5 (deterministic workflows)
        resp5 = df[df['id'] == 5].iloc[0]
        assert resp5['law5'] >= 65.0, "Response 5 should have good Law 5 (deterministic) score"

        # 6. Verify message includes summary
        message = result_data.get("message", "")
        assert "Batch validation completed" in message, "Message should indicate batch validation completed"
        assert "5" in message, "Message should mention 5 total responses"

        # 7. Image Verification - Compare generated figure with tutorial figure
        assert viz_file is not None and viz_file.exists(), "Visualization file should exist"

        notebook_figures_dir = pathlib.Path("notebooks/five_laws_validator_tutorial/images")
        png_files = [f for f in os.listdir(notebook_figures_dir) if f.endswith('.png')]

        # For figures generated by the tutorial, use imagehash to verify similarity
        hamming_vec = []
        for png_file in png_files:
            h1 = imagehash.phash(Image.open(viz_file))
            h2 = imagehash.phash(Image.open(notebook_figures_dir / png_file))
            hamming = h1 - h2
            hamming_vec.append(hamming)

        assert min(hamming_vec) < 20, f"Hamming distance {min(hamming_vec)} is greater than 20. Failed to pass the image verification."
