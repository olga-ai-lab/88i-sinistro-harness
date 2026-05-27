"""Agent package - re-exports main functions from agent.py module.

Note: There's both agent.py (module) and agent/ (package).
Python prefers the package, so we re-export functions from agent.py here.
"""

# Import from parent directory's agent.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    # Try to import from agent.py in parent directory
    from agent import processar_narrativa
    __all__ = ["processar_narrativa"]
except ImportError:
    # Fallback
    __all__ = []
