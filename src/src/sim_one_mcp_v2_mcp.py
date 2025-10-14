"""
Model Context Protocol (MCP) for SIM-ONE-MCP-v2

SIM-ONE is a comprehensive cognitive governance framework that provides emotional analysis and validation tools for AI systems. This implementation combines advanced emotional intelligence capabilities with rigorous Five Laws compliance checking to ensure responsible AI deployment and operation.

This MCP Server contains tools extracted from the following tutorial files:
1. esl_emotional_analysis_tutorial
    - esl_analyze_emotion: Analyze emotional content in text
    - esl_analyze_emotional_progression: Track emotional changes across conversation sequences
    - esl_recommend_response_tone: Generate empathetic response recommendations
    - esl_analyze_text_file: Analyze emotional content from text files
2. five_laws_validator_tutorial
    - five_laws_validate_text: Validate single text against Five Laws with configurable strictness
    - five_laws_batch_validate: Compare multiple texts and identify best performers
    - five_laws_iterative_validate: Iterative refinement workflow with feedback tracking
"""

from fastmcp import FastMCP

# Import statements (alphabetical order)
from tools.esl_emotional_analysis_tutorial import esl_emotional_analysis_tutorial_mcp
from tools.five_laws_validator_tutorial import five_laws_validator_tutorial_mcp

# Server definition and mounting
mcp = FastMCP(name="SIM-ONE-MCP-v2")
mcp.mount(esl_emotional_analysis_tutorial_mcp)
mcp.mount(five_laws_validator_tutorial_mcp)

if __name__ == "__main__":
    mcp.run()