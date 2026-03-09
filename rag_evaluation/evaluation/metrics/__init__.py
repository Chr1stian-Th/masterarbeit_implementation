"""
Evaluation metrics registry for the RAG evaluation framework.

This package provides a registry pattern that allows new DeepEval metrics
to be added as separate modules. Each metric module must define:

- ``METRIC_NAME``: A string identifier for the metric.
- ``create_metric(**kwargs)``: A factory function returning a configured
  DeepEval metric instance.

The :func:`get_all_metrics` function automatically discovers and loads
all metric modules in this package.

Adding a New Metric:
    1. Create a new file in ``evaluation/metrics/`` (e.g., ``answer_relevancy.py``).
    2. Define ``METRIC_NAME = "answer_relevancy"`` at the module level.
    3. Define ``create_metric(**kwargs)`` returning the DeepEval metric.
    4. The metric will be automatically discovered and registered.

Example:
    >>> from evaluation.metrics import get_all_metrics
    >>> metrics = get_all_metrics(model="gpt-4o-mini")
    >>> for name, metric in metrics.items():
    ...     print(f"Registered: {name}")
"""

from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Any


# Registry: metric_name -> metric factory function
_METRIC_REGISTRY: dict[str, callable] = {}


def register_metric(name: str, factory: callable) -> None:
    """Register a metric factory in the global registry.

    Args:
        name: Unique metric identifier string.
        factory: Callable that returns a configured DeepEval metric instance.
    """
    _METRIC_REGISTRY[name] = factory


def get_all_metrics(**kwargs: Any) -> dict[str, Any]:
    """Discover and instantiate all registered metrics.

    Scans this package for metric modules, registers any unregistered
    ones, then creates instances of all metrics.

    Args:
        **kwargs: Keyword arguments passed to each metric's
            ``create_metric()`` factory (e.g., ``model="gpt-4o-mini"``).

    Returns:
        Dictionary mapping metric names to their instantiated metric objects.
    """
    _discover_metrics()

    metrics = {}
    for name, factory in _METRIC_REGISTRY.items():
        metrics[name] = factory(**kwargs)
    return metrics


def get_metric(name: str, **kwargs: Any) -> Any:
    """Get a specific metric by name.

    Args:
        name: The metric identifier.
        **kwargs: Arguments passed to the metric factory.

    Returns:
        The instantiated metric object.

    Raises:
        KeyError: If the metric name is not registered.
    """
    _discover_metrics()

    if name not in _METRIC_REGISTRY:
        raise KeyError(
            f"Metric '{name}' not found. Available: {list(_METRIC_REGISTRY.keys())}"
        )
    return _METRIC_REGISTRY[name](**kwargs)


def list_metrics() -> list[str]:
    """List all available metric names.

    Returns:
        Sorted list of registered metric names.
    """
    _discover_metrics()
    return sorted(_METRIC_REGISTRY.keys())


def _discover_metrics() -> None:
    """Auto-discover metric modules in this package.

    Scans for Python files in the metrics directory and imports any
    that define ``METRIC_NAME`` and ``create_metric``.
    """
    package_dir = os.path.dirname(__file__)

    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        if module_name.startswith("_"):
            continue

        module = importlib.import_module(f".{module_name}", package=__name__)

        if hasattr(module, "METRIC_NAME") and hasattr(module, "create_metric"):
            name = module.METRIC_NAME
            if name not in _METRIC_REGISTRY:
                register_metric(name, module.create_metric)
