"""
Evaluator Registry
==================

Central registry for evaluation plugins. Mirrors the ``ConnectorRegistry``
pattern with decorator-based auto-registration and type-safe lookup.

The evaluation engine uses this registry to discover and instantiate
evaluators based on user-selected evaluator names at run time.

Usage::

    from src.evaluation.registry import register_evaluator, evaluator_registry

    @register_evaluator("my_metric")
    class MyEvaluator(BaseEvaluator):
        ...

    # Later, to retrieve:
    EvaluatorClass = evaluator_registry.get("my_metric")
    evaluator = EvaluatorClass()
"""

from src.core.exceptions import EvaluatorNotFoundError
from src.core.interfaces import BaseEvaluator
from src.core.models import EvaluatorInfo


class EvaluatorRegistry:
    """
    Registry for evaluator plugins.

    Maintains a mapping of evaluator name strings to their implementing
    classes. Supports filtering by agent type compatibility.

    Attributes:
        _evaluators: Internal dictionary mapping names to classes.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, type[BaseEvaluator]] = {}

    def register(self, evaluator_name: str, cls: type[BaseEvaluator]) -> None:
        """
        Register an evaluator class under the given name.

        Args:
            evaluator_name: Unique evaluator identifier (e.g., ``"deepeval_relevancy"``).
            cls: The evaluator class to register.

        Raises:
            ValueError: If the evaluator name is already registered.
        """
        if evaluator_name in self._evaluators:
            raise ValueError(
                f"Evaluator '{evaluator_name}' is already registered "
                f"by {self._evaluators[evaluator_name].__name__}."
            )
        self._evaluators[evaluator_name] = cls

    def get(self, evaluator_name: str) -> type[BaseEvaluator]:
        """
        Look up an evaluator class by name.

        Args:
            evaluator_name: The evaluator name to look up.

        Returns:
            The registered evaluator class.

        Raises:
            EvaluatorNotFoundError: If no evaluator is registered with the name.
        """
        if evaluator_name not in self._evaluators:
            raise EvaluatorNotFoundError(evaluator_name)
        return self._evaluators[evaluator_name]

    def list_evaluators(self) -> list[str]:
        """
        List all registered evaluator names.

        Returns:
            Sorted list of registered evaluator names.
        """
        return sorted(self._evaluators.keys())

    def list_evaluator_info(self) -> list[EvaluatorInfo]:
        """
        Return metadata for all registered evaluators.

        Instantiates each evaluator temporarily to call ``get_info()``.

        Returns:
            List of ``EvaluatorInfo`` objects.
        """
        infos = []
        for name, cls in sorted(self._evaluators.items()):
            try:
                instance = cls()
                infos.append(instance.get_info())
            except Exception:
                infos.append(EvaluatorInfo(name=name))
        return infos

    def get_for_agent_type(self, agent_type: str) -> list[str]:
        """
        List evaluators compatible with the given agent type.

        Args:
            agent_type: The agent type to filter by.

        Returns:
            List of evaluator names that support the given agent type.
        """
        compatible = []
        for name, cls in self._evaluators.items():
            try:
                instance = cls()
                if instance.supports_agent_type(agent_type):
                    compatible.append(name)
            except Exception:
                continue
        return sorted(compatible)

    def has(self, evaluator_name: str) -> bool:
        """Check if an evaluator is registered."""
        return evaluator_name in self._evaluators


# ---------------------------------------------------------------------------
# Global singleton registry instance
# ---------------------------------------------------------------------------
evaluator_registry = EvaluatorRegistry()


def register_evaluator(evaluator_name: str):
    """
    Decorator to auto-register an evaluator class with the global registry.

    Usage::

        @register_evaluator("answer_relevancy")
        class AnswerRelevancyEvaluator(BaseEvaluator):
            ...

    Args:
        evaluator_name: The name to register the evaluator under.

    Returns:
        Decorator function that registers the class and returns it unchanged.
    """

    def decorator(cls: type[BaseEvaluator]) -> type[BaseEvaluator]:
        evaluator_registry.register(evaluator_name, cls)
        cls.evaluator_name = evaluator_name
        return cls

    return decorator
