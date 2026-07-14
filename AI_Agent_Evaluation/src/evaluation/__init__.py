"""
Evaluation Package
==================

The evaluation engine is the most critical module of the platform.
It uses a plugin-based architecture where each evaluator implements
the ``BaseEvaluator`` interface and is registered with the
``EvaluatorRegistry``.

Sub-packages:
    - ``registry.py``: Central evaluator registry.
    - ``engine.py``: Evaluation dispatcher that runs selected evaluators.
    - ``plugins/``: Concrete evaluator implementations (placeholders in M1).
"""
