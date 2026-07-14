"""
Observability Logger (Langfuse)
===============================

Implementation of the ``BaseObservabilityLogger`` interface.

Provides a ``NoOpLogger`` for environments without observability config,
and a ``LangfuseLogger`` that streams traces and evaluations to Langfuse.
"""

import logging
from typing import Any

from src.core.interfaces import BaseObservabilityLogger
from src.core.models import EvaluationResult, TraceData

logger = logging.getLogger(__name__)


class NoOpLogger(BaseObservabilityLogger):
    """
    A placeholder observability logger that discards all log events.
    """

    def log_trace(self, trace: TraceData) -> None:
        """Silently discard trace data."""
        logger.debug("NoOpLogger: Discarded trace '%s'", trace.trace_id)

    def log_metric(self, name: str, value: float, metadata: dict[str, Any] | None = None) -> None:
        """Silently discard metric."""
        logger.debug("NoOpLogger: Discarded metric '%s'=%f", name, value)

    def log_evaluation(self, result: EvaluationResult, run_id: str, test_case_id: str) -> None:
        """Silently discard evaluation result."""
        logger.debug(
            "NoOpLogger: Discarded evaluation '%s' for test '%s'",
            result.evaluator_name,
            test_case_id,
        )

    def flush(self) -> None:
        """No-op."""
        pass


class LangfuseLogger(BaseObservabilityLogger):
    """
    Langfuse implementation of the observability logger.
    
    Streams agent inputs, outputs, token usage, latency, and evaluation
    scores to a Langfuse project.
    """
    
    def __init__(self, public_key: str, secret_key: str, host: str | None = None) -> None:
        """
        Initialize Langfuse client.
        """
        try:
            from langfuse import Langfuse
            self.langfuse = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host or "https://cloud.langfuse.com"
            )
            logger.info("Langfuse logger initialized successfully.")
        except ImportError:
            logger.error("Failed to import langfuse. Ensure it is installed.")
            raise
        except Exception as e:
            logger.error("Failed to initialize Langfuse client: %s", str(e))
            raise

    def log_trace(self, trace: TraceData) -> None:
        """
        Log a complete execution trace to Langfuse.
        
        Args:
            trace: The full trace data containing IO and evaluation scores.
        """
        try:
            # Create a trace grouped by the Execution Run ID
            lf_trace = self.langfuse.trace(
                id=trace.trace_id,
                name=f"TestCase-{trace.test_case_id}",
                session_id=trace.run_id,
                metadata=trace.metadata,
                tags=["agent-testing-platform"]
            )
            
            # Extract inputs/outputs as dict or string
            input_data = trace.input if isinstance(trace.input, dict) else {"text": str(trace.input)}
            output_data = trace.output if isinstance(trace.output, dict) else {"text": str(trace.output)}
            
            # Create a generation to track the LLM/Agent call
            lf_trace.generation(
                name="Agent Execution",
                input=input_data,
                output=output_data,
                metadata={
                    "latency_ms": trace.latency_ms,
                    "token_usage": trace.token_usage or {}
                }
            )
            
            # Log all evaluator scores attached to this trace
            for eval_res in trace.evaluation_scores:
                lf_trace.score(
                    name=eval_res.evaluator_name,
                    value=eval_res.score,
                    comment=eval_res.explanation
                )
                
                # Extract inner metrics (like RAGAS metrics) if present in details
                if eval_res.details and "metrics" in eval_res.details:
                    metrics = eval_res.details["metrics"]
                    if isinstance(metrics, dict):
                        for metric_name, metric_val in metrics.items():
                            lf_trace.score(
                                name=f"{eval_res.evaluator_name}_{metric_name}",
                                value=metric_val
                            )
                            
        except Exception as e:
            logger.error("Failed to log trace to Langfuse: %s", str(e))

    def log_metric(self, name: str, value: float, metadata: dict[str, Any] | None = None) -> None:
        """Not strictly required as metrics are attached as scores to traces."""
        pass

    def log_evaluation(self, result: EvaluationResult, run_id: str, test_case_id: str) -> None:
        """Evaluations are typically logged inside log_trace instead to link them directly."""
        pass

    def flush(self) -> None:
        """Flush the Langfuse event queue."""
        try:
            self.langfuse.flush()
        except Exception as e:
            logger.error("Failed to flush Langfuse queue: %s", str(e))
