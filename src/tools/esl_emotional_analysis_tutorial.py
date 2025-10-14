"""
ESL Emotional Analysis Tutorial - Emotion Detection Tools

This MCP Server provides 4 tools for multi-dimensional emotional analysis:
1. esl_analyze_emotion: Analyze emotional content in text
2. esl_analyze_emotional_progression: Track emotional changes across conversation sequences
3. esl_recommend_response_tone: Generate empathetic response recommendations
4. esl_analyze_text_file: Analyze emotional content from text files

All tools extracted from `https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb`.
"""

# Standard imports
from typing import Annotated, Literal, Any
import pandas as pd
import numpy as np
from pathlib import Path
import os
from fastmcp import FastMCP
from datetime import datetime
import sys
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Configure matplotlib for high-resolution figures
plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams['figure.figsize'] = (10, 6)
sns.set_style("whitegrid")

# Project structure
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DEFAULT_INPUT_DIR = PROJECT_ROOT / "tmp" / "inputs"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "tmp" / "outputs"

INPUT_DIR = Path(os.environ.get("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_INPUT_DIR", DEFAULT_INPUT_DIR))
OUTPUT_DIR = Path(os.environ.get("ESL_EMOTIONAL_ANALYSIS_TUTORIAL_OUTPUT_DIR", DEFAULT_OUTPUT_DIR))

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Add SIM-ONE to Python path
SIMONE_ROOT = PROJECT_ROOT / "repo" / "SIM-ONE" / "code"
if SIMONE_ROOT.exists():
    sys.path.insert(0, str(SIMONE_ROOT))

# Import ESL protocol
try:
    from mcp_server.protocols.esl.esl import ESL
except ImportError:
    print("Warning: ESL protocol not found. Tools will not function without SIM-ONE.")
    ESL = None

# Timestamp for unique outputs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# MCP server instance
esl_emotional_analysis_tutorial_mcp = FastMCP(name="esl_emotional_analysis_tutorial")


class ESLWrapper:
    """Wrapper to adapt ESL protocol to tutorial API"""
    def __init__(self, esl_instance):
        self.esl = esl_instance

    def process(self, params):
        """Convert process() API to execute() API"""
        text = params.get("text", "")
        format_type = params.get("format", "json")

        # Call the actual execute method
        result = self.esl.execute({"user_input": text})

        if format_type == "summary":
            # Return summary format
            return {"summary": result.get("explanation", "")}
        else:
            # Transform to expected JSON format
            detected = result.get("detected_emotions", [])
            primary_emotion = result.get("emotional_state", "neutral")

            # Extract secondary emotions
            secondary_emotions = [e["emotion"] for e in detected if e["emotion"] != primary_emotion]

            # Extract social and cognitive emotions
            social_emotions = [e["emotion"] for e in detected if e.get("dimension") == "social"]
            cognitive_indicators = [e["emotion"] for e in detected if e.get("dimension") == "cognitive"]

            # Convert valence to numeric
            valence_map = {"positive": 0.7, "negative": -0.7, "neutral": 0.0, "mixed": 0.0}
            valence_numeric = valence_map.get(result.get("valence", "neutral"), 0.0)

            return {
                "emotional_state": {
                    "primary_emotion": primary_emotion,
                    "secondary_emotions": secondary_emotions,
                    "social_emotions": social_emotions,
                    "cognitive_indicators": cognitive_indicators,
                    "valence": valence_numeric,
                    "intensity": result.get("intensity", 0.0),
                    "confidence": result.get("confidence", 0.0)
                }
            }


# Initialize ESL wrapper
_esl_wrapper = None

def get_esl_wrapper():
    """Lazy initialization of ESL wrapper"""
    global _esl_wrapper
    if _esl_wrapper is None:
        if ESL is None:
            raise RuntimeError("ESL protocol not available. Ensure SIM-ONE is properly installed.")
        esl_instance = ESL()
        _esl_wrapper = ESLWrapper(esl_instance)
    return _esl_wrapper


@esl_emotional_analysis_tutorial_mcp.tool
def esl_analyze_emotion(
    text: Annotated[str | None, "Text to analyze for emotional content"] = None,
    output_format: Annotated[Literal["json", "summary"], "Output format: 'json' for structured data, 'summary' for human-readable text"] = "json",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Analyze emotional content in text using SIM-ONE's ESL protocol with multi-dimensional emotion detection.
    Input is text string and output is emotional state analysis with primary/secondary emotions, valence, intensity, and confidence scores.
    """
    # Input validation
    if text is None:
        raise ValueError("Text to analyze must be provided")

    if not text.strip():
        raise ValueError("Text cannot be empty")

    # Get ESL wrapper
    esl = get_esl_wrapper()

    # Analyze emotion
    result = esl.process({
        "text": text,
        "format": output_format
    })

    # Prepare output file
    if out_prefix is None:
        out_prefix = f"emotion_analysis_{timestamp}"

    output_file = OUTPUT_DIR / f"{out_prefix}.json"

    # Save results
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Extract key information
    if output_format == "json":
        emotional_state = result.get("emotional_state", {})
        message = f"Detected {emotional_state.get('primary_emotion', 'neutral')} (valence: {emotional_state.get('valence', 0):.2f}, intensity: {emotional_state.get('intensity', 0):.2f})"
    else:
        message = "Emotional analysis completed (summary format)"

    return {
        "message": message,
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Emotional analysis results",
                "path": str(output_file.resolve())
            }
        ]
    }


@esl_emotional_analysis_tutorial_mcp.tool
def esl_analyze_emotional_progression(
    texts: Annotated[list | None, "List of text strings to analyze in sequence (e.g., conversation turns)"] = None,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Track emotional progression across a conversation or sequence of texts with visualization.
    Input is list of text strings and output is DataFrame with emotional metrics plus valence/intensity progression charts.
    """
    # Input validation
    if texts is None:
        raise ValueError("List of texts must be provided")

    if not texts or len(texts) == 0:
        raise ValueError("Text list cannot be empty")

    # Get ESL wrapper
    esl = get_esl_wrapper()

    # Analyze each text in sequence
    results = []
    for i, text in enumerate(texts, 1):
        result = esl.process({"text": text, "format": "json"})
        emotional_state = result.get("emotional_state", {})

        results.append({
            "step": i,
            "text_preview": text[:50],
            "emotion": emotional_state.get("primary_emotion", "neutral"),
            "valence": emotional_state.get("valence", 0),
            "intensity": emotional_state.get("intensity", 0)
        })

    # Create DataFrame
    df = pd.DataFrame(results)

    # Prepare output files
    if out_prefix is None:
        out_prefix = f"emotional_progression_{timestamp}"

    csv_file = OUTPUT_DIR / f"{out_prefix}.csv"
    plot_file = OUTPUT_DIR / f"{out_prefix}_visualization.png"

    # Save DataFrame
    df.to_csv(csv_file, index=False)

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Valence over time
    ax1.plot(df["step"], df["valence"], marker='o', linewidth=2, markersize=8)
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_ylabel("Valence", fontsize=12)
    ax1.set_title("Emotional Valence Progression", fontsize=14)
    ax1.grid(True, alpha=0.3)

    # Intensity over time
    ax2.plot(df["step"], df["intensity"], marker='s', linewidth=2, markersize=8, color='orange')
    ax2.set_xlabel("Conversation Step", fontsize=12)
    ax2.set_ylabel("Intensity", fontsize=12)
    ax2.set_title("Emotional Intensity Progression", fontsize=14)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.close()

    # Create summary message
    emotion_arc = " → ".join(df['emotion'].tolist())
    message = f"Analyzed {len(texts)} texts. Emotional arc: {emotion_arc}"

    return {
        "message": message,
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Emotional progression data",
                "path": str(csv_file.resolve())
            },
            {
                "description": "Valence and intensity visualization",
                "path": str(plot_file.resolve())
            }
        ]
    }


@esl_emotional_analysis_tutorial_mcp.tool
def esl_recommend_response_tone(
    text: Annotated[str | None, "User text to analyze for response tone recommendation"] = None,
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Analyze user emotion and recommend appropriate empathetic response tone.
    Input is user text and output is recommended response tone with guidance on how to respond empathetically.
    """
    # Input validation
    if text is None:
        raise ValueError("Text to analyze must be provided")

    if not text.strip():
        raise ValueError("Text cannot be empty")

    # Get ESL wrapper
    esl = get_esl_wrapper()

    # Analyze emotion
    result = esl.process({"text": text, "format": "json"})
    emotional_state = result.get("emotional_state", {})

    emotion = emotional_state.get("primary_emotion", "neutral")
    valence = emotional_state.get("valence", 0)
    intensity = emotional_state.get("intensity", 0)

    # Determine response tone based on tutorial logic
    if valence < 0 and intensity > 0.7:
        response_tone = "empathetic"
        recommendation = "Use warm, understanding language. Acknowledge their feelings."
    elif valence > 0:
        response_tone = "encouraging"
        recommendation = "Match their positive energy. Celebrate their emotion."
    elif "confusion" in emotional_state.get("cognitive_indicators", []):
        response_tone = "clear_explanatory"
        recommendation = "Provide clear, structured explanations. Break down complex ideas."
    else:
        response_tone = "neutral_supportive"
        recommendation = "Maintain professional, supportive tone."

    # Prepare output
    recommendation_data = {
        "user_text": text,
        "detected_emotion": emotion,
        "valence": valence,
        "intensity": intensity,
        "recommended_tone": response_tone,
        "guidance": recommendation
    }

    # Save results
    if out_prefix is None:
        out_prefix = f"response_recommendation_{timestamp}"

    output_file = OUTPUT_DIR / f"{out_prefix}.json"

    with open(output_file, 'w') as f:
        json.dump(recommendation_data, f, indent=2)

    message = f"Recommend '{response_tone}' tone for {emotion} (valence: {valence:.2f}, intensity: {intensity:.2f})"

    return {
        "message": message,
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb",
        "artifacts": [
            {
                "description": "Response tone recommendation",
                "path": str(output_file.resolve())
            }
        ]
    }


@esl_emotional_analysis_tutorial_mcp.tool
def esl_analyze_text_file(
    file_path: Annotated[str | None, "Path to text file to analyze (.txt extension)"] = None,
    output_format: Annotated[Literal["json", "summary"], "Output format: 'json' for structured data, 'summary' for human-readable text"] = "json",
    out_prefix: Annotated[str | None, "Output file prefix"] = None,
) -> dict:
    """
    Analyze emotional content from a text file using ESL protocol.
    Input is path to text file and output is emotional state analysis with primary/secondary emotions, valence, and intensity.
    """
    # Input validation
    if file_path is None:
        raise ValueError("Path to text file must be provided")

    # File existence validation
    text_file = Path(file_path)
    if not text_file.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    # Read file content
    text = text_file.read_text()

    if not text.strip():
        raise ValueError("File content is empty")

    # Get ESL wrapper
    esl = get_esl_wrapper()

    # Analyze emotion
    result = esl.process({
        "text": text,
        "format": output_format
    })

    # Prepare output file
    if out_prefix is None:
        out_prefix = f"file_emotion_analysis_{timestamp}"

    output_file = OUTPUT_DIR / f"{out_prefix}.json"

    # Save results
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Extract key information
    if output_format == "json":
        emotional_state = result.get("emotional_state", {})
        message = f"File analysis: {emotional_state.get('primary_emotion', 'neutral')} (valence: {emotional_state.get('valence', 0):.2f})"
    else:
        message = "File emotional analysis completed (summary format)"

    return {
        "message": message,
        "reference": "https://github.com/lse-ai4gov/SIM-ONE/blob/main/tutorials/esl_emotional_analysis_tutorial.ipynb",
        "artifacts": [
            {
                "description": "File emotional analysis results",
                "path": str(output_file.resolve())
            }
        ]
    }
