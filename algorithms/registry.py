"""Algorithm registry for automatic discovery of step detection algorithms.

Copyright (c) 2025 Konrad Rieck. MIT License
"""

import importlib
import inspect
from pathlib import Path

from .base import BaseDetector


def discover_algorithms():
    """Discover all available algorithms in the algorithms directory."""
    algorithms = {}

    # Get the algorithms directory
    algorithms_dir = Path(__file__).parent

    # Iterate through all Python files in the algorithms directory
    for file_path in algorithms_dir.glob("*.py"):
        # Skip __init__.py, base.py, and registry.py
        if file_path.name in ["__init__.py", "base.py", "registry.py"]:
            continue

        # Import the module
        module_name = f"algorithms.{file_path.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find all classes that inherit from BaseDetector
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseDetector)
                    and obj != BaseDetector
                ):
                    # Convert camelcase to lowercase with underscores
                    algo_name = "".join(
                        ["_" + c.lower() if c.isupper() else c for c in name]
                    ).lstrip("_")
                    algorithms[algo_name] = obj

        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")

    return algorithms


# Global registry of available algorithms
detectors = discover_algorithms()
