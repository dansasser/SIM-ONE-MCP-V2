#!/usr/bin/env python3
"""
Reliable notebook executor using nbclient.
"""
import sys
import nbformat
import nbclient
from pathlib import Path
import traceback


def execute_notebook(input_path: str, output_path: str, timeout: int = 600) -> bool:
    """
    Execute a Jupyter notebook using nbclient.

    Args:
        input_path: Path to input notebook
        output_path: Path to save executed notebook
        timeout: Execution timeout per cell in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        print(f"[+] Reading notebook: {input_path}")
        with open(input_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        print(f"[+] Executing notebook with timeout={timeout}s per cell")
        print(f"[+] Total cells: {len(nb.cells)}")

        # Create execution client
        client = nbclient.NotebookClient(
            nb,
            timeout=timeout,
            kernel_name='python3',
            allow_errors=False,  # Stop on first error
            record_timing=True
        )

        # Execute
        client.execute()

        print(f"[+] Execution completed successfully")
        print(f"[+] Writing output to: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

        print(f"[+] Success!")
        return True

    except nbclient.exceptions.CellExecutionError as e:
        print(f"[-] Cell execution error:")
        print(f"    Cell: {e.cell_index if hasattr(e, 'cell_index') else 'unknown'}")
        print(f"    Error: {str(e)}")

        # Save partial execution
        print(f"[+] Saving partial execution to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)

        return False

    except Exception as e:
        print(f"[-] Unexpected error: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python execute_notebook.py <input.ipynb> <output.ipynb>")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(input_path).exists():
        print(f"[-] Input file not found: {input_path}")
        sys.exit(1)

    success = execute_notebook(input_path, output_path)
    sys.exit(0 if success else 1)
