"""
RAGAS Evaluator Plugin
======================

Integrates RAGAS metrics (Context Precision, Context Recall, Faithfulness,
Answer Correctness) behind the ``BaseEvaluator`` interface.

RAGAS is specifically designed for evaluating RAG (Retrieval-Augmented
Generation) pipelines and requires retrieval context in the test case.
"""

from src.core.enums import AgentType, EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


@register_evaluator("ragas")
class RagasEvaluator(BaseEvaluator):
    """
    RAGAS metrics evaluator for RAG agents.

    Attributes:
        evaluator_name: ``"ragas"``
    """

    evaluator_name = "ragas"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        """
        Evaluate using RAGAS metrics for RAG pipelines.

        Args:
            test_case: The test case containing ground truth.
            agent_output: The RAG agent's response.

        Returns:
            EvaluationResult with RAGAS scores.
        """
        try:
            import os
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import (
                answer_correctness,
                context_precision,
                context_recall,
                faithfulness,
            )
        except ImportError:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="RAGAS library not installed. Cannot run evaluation.",
            )

        if not os.environ.get("OPENAI_API_KEY"):
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="OPENAI_API_KEY environment variable not set. RAGAS requires an LLM judge.",
            )

        # 1. Extract required fields
        # RAGAS requires: question, answer, contexts, ground_truth
        
        # Question from input
        question = ""
        if isinstance(test_case.input, dict):
            question = test_case.input.get("query", test_case.input.get("prompt", str(test_case.input)))
        else:
            question = str(test_case.input)
            
        # Answer from agent output
        answer = ""
        if isinstance(agent_output.output, dict):
            answer = agent_output.output.get("answer", agent_output.output.get("response", str(agent_output.output)))
        else:
            answer = str(agent_output.output)
            
        # Contexts from agent output OR test case
        contexts = []
        if isinstance(agent_output.output, dict) and "source_nodes" in agent_output.output:
            contexts = agent_output.output["source_nodes"]
        elif test_case.context:
            contexts = test_case.context if isinstance(test_case.context, list) else [str(test_case.context)]
            
        # Ground truth
        ground_truth = test_case.ground_truth
        
        # Validate required inputs
        missing = []
        if not question: missing.append("question")
        if not answer: missing.append("answer")
        if not contexts: missing.append("contexts")
        if not ground_truth: missing.append("ground_truth")
        
        if missing:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation=f"Missing required fields for RAGAS: {', '.join(missing)}.",
            )

        # 2. Prepare dataset
        data_samples = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
            "ground_truth": [ground_truth],
        }
        dataset = Dataset.from_dict(data_samples)

        # 3. Run evaluation
        try:
            result = evaluate(
                dataset,
                metrics=[
                    context_precision,
                    context_recall,
                    faithfulness,
                    answer_correctness,
                ],
            )
            
            # Extract individual scores
            scores = {
                "context_precision": result["context_precision"],
                "context_recall": result["context_recall"],
                "faithfulness": result["faithfulness"],
                "answer_correctness": result["answer_correctness"],
            }
            
            # Calculate overall average
            valid_scores = [s for s in scores.values() if not __import__('math').isnan(s)]
            overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0
            
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=overall_score,
                passed=overall_score >= 0.7, # Configurable threshold in future
                explanation=f"RAGAS evaluation completed with overall score: {overall_score:.2f}",
                details={"metrics": scores}
            )

        except Exception as e:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation=f"RAGAS evaluation failed: {str(e)}",
            )

    def supports_agent_type(self, agent_type: str) -> bool:
        """RAGAS only supports RAG chatbot agents."""
        return agent_type == AgentType.RAG_CHATBOT

    def get_info(self) -> EvaluatorInfo:
        """Return metadata about this evaluator."""
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="RAGAS metrics for RAG agents: context precision, context recall, faithfulness, answer correctness.",
            category=EvaluatorCategory.LLM_BASED,
            supported_agent_types=[AgentType.RAG_CHATBOT],
            requires_expected_output=True,
            requires_context=True,
        )
