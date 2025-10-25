# Changelog

All notable changes to the SIM-ONE MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### `five_laws_iterative_validate` Tool Enhancement
- **Updated tool docstring** to explicitly describe client AI self-refinement workflow
  - Now clearly states this tool is for CLIENT AI to refine their OWN responses
  - Provides step-by-step workflow instructions (generate → validate → improve → revalidate)
  - Emphasizes tool provides feedback, does not refine automatically

- **Added `guidance_for_next_iteration` field** to response
  - Provides actionable refinement guidance when validation fails
  - Lists priority actions (top 3 recommendations)
  - Shows current gap from threshold
  - Displays specific issues found
  - Estimates expected improvement
  - Includes clear next step instructions
  - Returns `null` when validation passes

- **Files modified:**
  - `src/tools/five_laws_validator_tutorial.py` (lines 481-496 docstring, lines 529-568 guidance field)

#### `compose_governed_response` Tool - Client-First Workflow
- **Changed tool to validate CLIENT AI responses instead of generating server responses**
  - Tool now accepts CLIENT AI's response as input (not just prompt)
  - Server validates the CLIENT's response, not its own generation
  - Enables testing governance of any AI (Claude, ChatGPT, etc.)

- **Updated function signature:**
  - Added required `response` parameter: CLIENT AI's response to validate
  - Made `prompt` required (provides context for refinement)
  - Both prompt and response now required for proper validation

- **Updated tool docstring:**
  - Clearly describes client-first workflow (lines 700-719)
  - Explains server validates CLIENT responses, not generates them
  - Documents that server refines using Claude CLI if needed

- **Removed server-side initial generation:**
  - No longer calls `_generate_response()` for initial response (lines 408-411)
  - Uses client-provided response directly as iteration 0
  - Server only generates during refinement steps (if needed)

- **Enhanced validation:**
  - Validates both prompt and response are provided (lines 745-760)
  - Clear error messages explaining what's required
  - Better logging showing "CLIENT-provided response" vs "server-generated" (lines 410, 414, 433)

- **Files modified:**
  - `src/tools/five_laws_validator_tutorial.py` (lines 691-774 wrapper function)
  - `src/tools/governed_response_composer.py` (lines 341-433 implementation function)

### Purpose

These changes clarify the two distinct governance workflows:

1. **Client Self-Refinement** (`five_laws_iterative_validate`):
   - Client AI generates response
   - Tool provides feedback
   - Client AI improves their own response
   - Client AI calls tool again
   - Repeat until passed

2. **Server-Assisted Refinement** (`compose_governed_response`):
   - Client AI generates response
   - Tool validates CLIENT's response
   - Server automatically refines using Claude CLI if needed
   - Returns governance-compliant version

Both workflows now clearly test the CLIENT AI's responses, not the server's generation capabilities.

---

## [Previous] - 2025-10-22

### Fixed
- Resolved Claude CLI subprocess timeout by adding `stdin=subprocess.DEVNULL`
- Fixed response format causing client hang issues by simplifying return structure
- Removed 500-character response truncation - now returns full generated response
- Updated install instructions to use correct npm command: `npm install -g @anthropic-ai/claude-code`

### Changed
- Standardized `compose_governed_response` return structure to match other tools
- Simplified return format to use only `message`, `reference`, and `artifacts` fields
- Cleaned up subprocess configuration by removing ineffective `PYTHONUNBUFFERED` env var

### Files Modified
- `src/tools/governed_response_composer.py`
- `src/tools/five_laws_validator_tutorial.py`
