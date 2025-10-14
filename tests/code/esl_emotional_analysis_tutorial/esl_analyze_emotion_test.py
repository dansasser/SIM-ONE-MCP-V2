"""
Tests for esl_analyze_emotion in esl_emotional_analysis_tutorial.py that reproduce the tutorial exactly.

Tutorial: SIM-ONE/tutorials/esl_emotional_analysis_tutorial.ipynb
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
    """FastMCP server fixture with the esl_emotional_analysis_tutorial tool."""
    # Force module reload
    module_name = 'src.tools.esl_emotional_analysis_tutorial'
    if module_name in sys.modules:
        del sys.modules[module_name]

    import src.tools.esl_emotional_analysis_tutorial
    return src.tools.esl_emotional_analysis_tutorial.esl_emotional_analysis_tutorial_mcp

@pytest.fixture
def test_directories():
    """Setup test directories and environment variables."""
    test_input_dir = pathlib.Path(__file__).parent.parent.parent / "data" / "esl_emotional_analysis_tutorial"
    test_output_dir = pathlib.Path(__file__).parent.parent.parent / "results" / "esl_emotional_analysis_tutorial"

    test_input_dir.mkdir(parents=True, exist_ok=True)
    test_output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variable management
    old_input_dir = os.environ.get("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_INPUT_DIR")
    old_output_dir = os.environ.get("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_OUTPUT_DIR")

    os.environ["ESL_EMOTIONAL_ANALYSIS_TUTORIAL_INPUT_DIR"] = str(test_input_dir.resolve())
    os.environ["ESL_EMOTIONAL_ANALYSIS_TUTORIAL_OUTPUT_DIR"] = str(test_output_dir.resolve())

    yield {"input_dir": test_input_dir, "output_dir": test_output_dir}

    # Cleanup
    if old_input_dir is not None:
        os.environ["ESL_EMOTIONAL_ANALYSIS_TUTORIAL_INPUT_DIR"] = old_input_dir
    else:
        os.environ.pop("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_INPUT_DIR", None)

    if old_output_dir is not None:
        os.environ["ESL_EMOTIONAL_ANALYSIS_TUTORIAL_OUTPUT_DIR"] = old_output_dir
    else:
        os.environ.pop("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_OUTPUT_DIR", None)

# ========= Input Fixtures (Tutorial Values) =========
@pytest.fixture
def esl_analyze_emotion_inputs(test_directories) -> dict:
    return {
        "text": "I'm so excited about this new project! It's going to be amazing.",
        "output_format": "json",
        "out_prefix": "test_emotion_analysis"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_esl_analyze_emotion(server, esl_analyze_emotion_inputs, test_directories):
    """Test esl_analyze_emotion with exact tutorial example from Example 1."""
    async with Client(server) as client:
        result = await client.call_tool("esl_analyze_emotion", esl_analyze_emotion_inputs)

        # 1. Verify result structure
        assert hasattr(result, 'data'), "Result should have data attribute"
        result_data = result.data

        # 2. Verify message field exists
        assert "message" in result_data, "Result should contain 'message' field"

        # 3. Verify artifacts exist and output file created
        assert "artifacts" in result_data, "Result should contain 'artifacts' field"
        assert len(result_data["artifacts"]) > 0, "Should have at least one artifact"

        output_file_path = pathlib.Path(result_data["artifacts"][0]["path"])
        assert output_file_path.exists(), f"Output file should exist at {output_file_path}"

        # 4. Verify output file content structure (tutorial shows JSON format)
        with open(output_file_path, 'r') as f:
            output_data = json.load(f)

        assert "emotional_state" in output_data, "Output should contain 'emotional_state'"
        emotional_state = output_data["emotional_state"]

        # 5. Verify emotional state structure
        assert "primary_emotion" in emotional_state, "Should have primary_emotion"
        assert "valence" in emotional_state, "Should have valence"
        assert "intensity" in emotional_state, "Should have intensity"

        # 6. Verify tutorial-specific values (Example 1: excited text should show joy)
        # Tutorial shows: Primary Emotion: joy, Valence: 0.70 (positive), Intensity: 0.75
        assert emotional_state["primary_emotion"] == "joy", f"Expected 'joy', got {emotional_state['primary_emotion']}"
        assert emotional_state["valence"] == pytest.approx(0.70, rel=0.1), f"Expected valence ~0.70, got {emotional_state['valence']}"
        assert emotional_state["intensity"] == pytest.approx(0.75, rel=0.1), f"Expected intensity ~0.75, got {emotional_state['intensity']}"

        # 7. Verify valence is positive (tutorial specifies positive)
        assert emotional_state["valence"] > 0, "Valence should be positive for excited text"
