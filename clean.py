#!/usr/bin/env python3
"""
Cleanup script for Exergy Ore Grade Decrease Model.
Removes temporary and cache files.
"""

import os
import shutil
from pathlib import Path


def clean_directory():
    """Remove temporary files and directories."""
    root = Path(__file__).parent
    
    # Remove __pycache__ directories
    for pycache in root.rglob("__pycache__"):
        print(f"Removing {pycache}...")
        shutil.rmtree(pycache, ignore_errors=True)
    
    # Remove .ipynb_checkpoints
    for checkpoint in root.rglob(".ipynb_checkpoints"):
        print(f"Removing {checkpoint}...")
        shutil.rmtree(checkpoint, ignore_errors=True)
    
    # Remove Python cache files
    for pyc in root.rglob("*.pyc"):
        print(f"Removing {pyc}...")
        pyc.unlink(ignore_errors=True)
    
    # Remove temporary files
    for tmp in root.rglob("*.tmp"):
        print(f"Removing {tmp}...")
        tmp.unlink(ignore_errors=True)
    
    for temp in root.rglob("*.temp"):
        print(f"Removing {temp}...")
        temp.unlink(ignore_errors=True)
    
    print("Cleanup complete!")


if __name__ == "__main__":
    clean_directory()
