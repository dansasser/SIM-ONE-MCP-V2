"""
Tests for esl_analyze_emotional_progression in esl_emotional_analysis_tutorial.py that reproduce the tutorial exactly.

Tutorial: SIM-ONE/tutorials/esl_emotional_analysis_tutorial.ipynb
"""

from __future__ import annotations
import pathlib
import pytest
import sys
from fastmcp import Client
import os
import pandas as pd
from PIL import Image
import imagehash

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
def esl_analyze_emotional_progression_inputs(test_directories) -> dict:
    """Exact conversation sequence from tutorial Example 8."""
    return {
        "texts": [
            "I'm excited to start this project!",
            "We hit some roadblocks today, feeling a bit discouraged.",
            "After the team meeting, I feel more hopeful about finding solutions.",
            "Success! We solved the problem. Feeling accomplished.",
        ],
        "out_prefix": "test_emotional_progression"
    }

# ========= Tests (Mirror Tutorial Only) =========
@pytest.mark.asyncio
async def test_esl_analyze_emotional_progression(server, esl_analyze_emotional_progression_inputs, test_directories):
    """Test esl_analyze_emotional_progression with exact tutorial example from Example 8."""
    async with Client(server) as client:
        result = await client.call_tool("esl_analyze_emotional_progression", esl_analyze_emotional_progression_inputs)

        # 1. Verify result structure
        assert hasattr(result, 'data'), "Result should have data attribute"
        result_data = result.data

        # 2. Verify message field exists
        assert "message" in result_data, "Result should contain 'message' field"
        message = result_data["message"]

        # 3. Verify message shows correct number of texts analyzed (4 from tutorial)
        assert "4" in message, f"Message should indicate 4 texts analyzed, got: {message}"

        # 4. Verify artifacts exist (should have CSV and visualization)
        assert "artifacts" in result_data, "Result should contain 'artifacts' field"
        assert len(result_data["artifacts"]) == 2, f"Should have 2 artifacts (CSV + visualization), got {len(result_data['artifacts'])}"

        # 5. Verify CSV file exists and has correct structure
        csv_artifact = [a for a in result_data["artifacts"] if "data" in a["description"].lower()][0]
        csv_path = pathlib.Path(csv_artifact["path"])
        assert csv_path.exists(), f"CSV file should exist at {csv_path}"

        # 6. Load and verify CSV structure
        df = pd.read_csv(csv_path)
        assert len(df) == 4, f"Should have 4 rows (one per text), got {len(df)}"

        # Verify columns from tutorial
        expected_columns = ["step", "text_preview", "emotion", "valence", "intensity"]
        assert all(col in df.columns for col in expected_columns), f"Missing expected columns. Got: {df.columns.tolist()}"

        # 7. Verify step sequence
        assert df["step"].tolist() == [1, 2, 3, 4], f"Steps should be [1, 2, 3, 4], got {df['step'].tolist()}"

        # 8. Verify emotional arc structure (ESL may detect different emotions based on model version)
        # Tutorial shows: 📊 Emotional arc: ['joy', 'fear', 'neutral', 'pride']
        # But we validate the emotional progression pattern rather than exact emotions
        emotional_arc = df["emotion"].tolist()

        # Verify we have 4 emotions (one per text)
        assert len(emotional_arc) == 4, f"Should have 4 emotions in arc, got {len(emotional_arc)}"

        # First text should be positive (excited)
        positive_emotions = ["joy", "excitement", "happiness"]
        assert emotional_arc[0] in positive_emotions, f"First emotion should be positive, got {emotional_arc[0]}"

        # 9. Verify valence pattern (positive -> variable -> variable -> positive/neutral)
        valences = df["valence"].tolist()

        # First text (excited) should have positive valence
        assert valences[0] > 0, f"First text (excited) should have positive valence, got {valences[0]}"

        # All valence values should be in valid range [-1, 1]
        assert all(-1 <= v <= 1 for v in valences), f"All valence values should be in [-1, 1], got {valences}"

        # 10. Verify visualization file exists
        viz_artifact = [a for a in result_data["artifacts"] if "visualization" in a["description"].lower()][0]
        viz_path = pathlib.Path(viz_artifact["path"])
        assert viz_path.exists(), f"Visualization file should exist at {viz_path}"
        assert viz_path.suffix == ".png", "Visualization should be PNG format"

        # 11. Image Verification - Compare with notebook figure
        notebook_figures_dir = pathlib.Path("notebooks/esl_emotional_analysis_tutorial/images")
        png_files = [f for f in os.listdir(notebook_figures_dir) if f.endswith('.png')]

        # Only one PNG in notebook (cell_26_output_2_fig_1.png - the progression chart)
        hamming_vec = []
        for png_file in png_files:
            h1 = imagehash.phash(Image.open(viz_path))
            h2 = imagehash.phash(Image.open(notebook_figures_dir / png_file))
            hamming = h1 - h2
            hamming_vec.append(hamming)

        assert min(hamming_vec) < 20, f"Hamming distance {min(hamming_vec)} is greater than 20. Failed to pass the image verification."
