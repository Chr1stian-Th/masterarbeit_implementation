"""
Common utilities shared across all RAG approaches.

This package provides standardized data schemas, token tracking, and output
logging so that all approaches produce consistent, comparable results.

Note:
    Each approach runs in its own virtual environment. This package is
    imported via sys.path manipulation (the project root is added to
    sys.path at the top of each approach's run.py).
"""
