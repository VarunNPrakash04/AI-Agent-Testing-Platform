"""
Evaluator Plugins Package
==========================

Contains concrete implementations of ``BaseEvaluator`` for different
evaluation strategies. Each plugin auto-registers itself via the
``@register_evaluator`` decorator on import.

Available Plugins:
    - ``exact_match_evaluator.py``: Deep equality check.
    - ``json_validator.py``: JSON schema validation.
    - ``business_rules.py``: Declarative business rule evaluation.
    - ``latency_evaluator.py``: Response time threshold checks.
    - ``deepeval_evaluator.py``: DeepEval heuristic evaluation.
    - ``ragas_evaluator.py``: RAGAS metrics.
    - ``security_evaluator.py``: Security checks.
    - ``metric_evaluators.py``: Individual metric evaluators for UI support.
"""

from src.evaluation.plugins.exact_match_evaluator import ExactMatchEvaluator  # noqa: F401
from src.evaluation.plugins.json_validator import JsonValidatorEvaluator  # noqa: F401
from src.evaluation.plugins.business_rules import BusinessRuleEvaluator  # noqa: F401
from src.evaluation.plugins.latency_evaluator import LatencyEvaluator  # noqa: F401
from src.evaluation.plugins.deepeval_evaluator import DeepEvalEvaluator  # noqa: F401
from src.evaluation.plugins.ragas_evaluator import RagasEvaluator  # noqa: F401
from src.evaluation.plugins.security_evaluator import SecurityEvaluator  # noqa: F401
from src.evaluation.plugins.data_presence_evaluator import DataPresenceEvaluator  # noqa: F401
from src.evaluation.plugins.metric_evaluators import (  # noqa: F401
    AnswerRelevancyEvaluator,
    FaithfulnessEvaluator,
    ContextualPrecisionEvaluator,
    HallucinationEvaluator,
    BiasDetectionEvaluator,
    ToxicityEvaluator,
    JsonCorrectnessEvaluator,
    FileSizeEvaluator,
    RowCountEvaluator,
    SchemaValidationEvaluator,
    FormulaEquivalenceEvaluator,
    LogicCheckEvaluator,
)
