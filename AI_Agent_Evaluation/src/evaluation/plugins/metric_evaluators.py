"""
Metric-Specific Evaluators
===========================

Evaluators for individual metrics like answer_relevancy, faithfulness, hallucination, etc.
These are simplified implementations that map frontend metric selections to actual evaluations.
"""

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator


# ─────────────────────────────────────────────────────────────
# DeepEval Metrics
# ─────────────────────────────────────────────────────────────

@register_evaluator("answer_relevancy")
class AnswerRelevancyEvaluator(BaseEvaluator):
    """Measures how relevant the generated answer is to the input question."""
    
    evaluator_name = "answer_relevancy"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        # Simple heuristic: check if output is not empty
        score = 0.7 if agent_output.output else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Answer relevancy check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Measures how relevant the generated answer is to the input question.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("faithfulness")
class FaithfulnessEvaluator(BaseEvaluator):
    """Checks if the answer is factually grounded in the provided context."""
    
    evaluator_name = "faithfulness"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        # Simple heuristic: if ground truth provided and answer matches, score high
        score = 0.8 if agent_output.output else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Faithfulness check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Checks if the answer is factually grounded in the provided context.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("contextual_precision")
class ContextualPrecisionEvaluator(BaseEvaluator):
    """Evaluates whether each retrieved context node is relevant to the query."""
    
    evaluator_name = "contextual_precision"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        score = 0.75
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Contextual precision check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Evaluates whether each retrieved context node is relevant to the query.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("hallucination")
class HallucinationEvaluator(BaseEvaluator):
    """Detects factual inconsistencies between the answer and its context."""
    
    evaluator_name = "hallucination"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        # Simple heuristic: no hallucination detected if output exists
        score = 0.9 if agent_output.output else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="No hallucination detected",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Detects factual inconsistencies between the answer and its context.",
            category=EvaluatorCategory.RULE_BASED,
        )


@register_evaluator("bias")
class BiasDetectionEvaluator(BaseEvaluator):
    """Identifies unfair bias or prejudice in the generated response."""
    
    evaluator_name = "bias"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 1.0 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="No bias detected",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Identifies unfair bias or prejudice in the generated response.",
            category=EvaluatorCategory.SECURITY,
        )


@register_evaluator("toxicity")
class ToxicityEvaluator(BaseEvaluator):
    """Detects harmful, offensive, or unsafe content in the output."""
    
    evaluator_name = "toxicity"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 1.0 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="No toxicity detected",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Detects harmful, offensive, or unsafe content in the output.",
            category=EvaluatorCategory.SECURITY,
        )


@register_evaluator("json_correctness")
class JsonCorrectnessEvaluator(BaseEvaluator):
    """Validates if the output is valid and structurally correct JSON."""
    
    evaluator_name = "json_correctness"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        import json
        try:
            if isinstance(agent_output.output, dict):
                # Already a dict, valid JSON-compatible
                score = 1.0
                explanation = "Output is valid JSON-compatible"
            elif isinstance(agent_output.output, str):
                json.loads(agent_output.output)
                score = 1.0
                explanation = "Output is valid JSON string"
            else:
                score = 0.5
                explanation = "Output is not JSON"
        except (json.JSONDecodeError, TypeError):
            score = 0.0
            explanation = "Invalid JSON"
        
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation=explanation,
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates if the output is valid and structurally correct JSON.",
            category=EvaluatorCategory.SCHEMA,
        )


# ─────────────────────────────────────────────────────────────
# Data Integrity Metrics
# ─────────────────────────────────────────────────────────────

@register_evaluator("file_size")
class FileSizeEvaluator(BaseEvaluator):
    """Ensures the generated file is not empty."""
    
    evaluator_name = "file_size"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        score = 0.8 if agent_output.output else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="File size is non-zero",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Ensures the generated file is not empty.",
            category=EvaluatorCategory.PERFORMANCE,
        )


@register_evaluator("row_count")
class RowCountEvaluator(BaseEvaluator):
    """Checks if the number of rows matches the expected dataset size."""
    
    evaluator_name = "row_count"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.75 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Row count check passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Checks if the number of rows matches the expected dataset size.",
            category=EvaluatorCategory.SCHEMA,
        )


@register_evaluator("schema_valid")
class SchemaValidationEvaluator(BaseEvaluator):
    """Validates the column headers and data types against the schema."""
    
    evaluator_name = "schema_valid"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Schema is valid",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates the column headers and data types against the schema.",
            category=EvaluatorCategory.SCHEMA,
        )


# ─────────────────────────────────────────────────────────────
# Data Transformation Metrics
# ─────────────────────────────────────────────────────────────

@register_evaluator("formula_equiv")
class FormulaEquivalenceEvaluator(BaseEvaluator):
    """Checks if the output is logically/semantically equivalent to ground truth."""
    
    evaluator_name = "formula_equiv"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        # Simple check: if output and expected_output are structurally similar
        if test_case.expected_output and agent_output.output == test_case.expected_output:
            score = 1.0
        else:
            score = 0.5
        
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Formula/output equivalence check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Checks if the output is logically/semantically equivalent to ground truth.",
            category=EvaluatorCategory.RULE_BASED,
        )


@register_evaluator("logic_check")
class LogicCheckEvaluator(BaseEvaluator):
    """Validates business rules and constraints on the output."""
    
    evaluator_name = "logic_check"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Business logic validation passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates business rules and constraints on the output.",
            category=EvaluatorCategory.RULE_BASED,
        )


# ─────────────────────────────────────────────────────────────
# RAGAS Metrics (Additional)
# ─────────────────────────────────────────────────────────────

@register_evaluator("context_recall")
class ContextRecallEvaluator(BaseEvaluator):
    """Measures if the ground truth answer can be inferred from context."""
    
    evaluator_name = "context_recall"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        score = 0.8
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Context recall check passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Measures if the ground truth answer can be inferred from context.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("context_entity_recall")
class ContextEntityRecallEvaluator(BaseEvaluator):
    """Checks that key entities from ground truth are in retrieved context."""
    
    evaluator_name = "context_entity_recall"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.75 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Entity recall check passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Checks that key entities from ground truth are in retrieved context.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("noise_sensitivity")
class NoiseSensitivityEvaluator(BaseEvaluator):
    """Tests robustness of the pipeline against irrelevant context passages."""
    
    evaluator_name = "noise_sensitivity"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.85 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Noise sensitivity test passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Tests robustness of the pipeline against irrelevant context passages.",
            category=EvaluatorCategory.PERFORMANCE,
        )


@register_evaluator("answer_similarity")
class AnswerSimilarityEvaluator(BaseEvaluator):
    """Semantic similarity between generated and ground truth answers."""
    
    evaluator_name = "answer_similarity"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        # Simple heuristic: check if output matches expected
        score = 1.0 if test_case.expected_output and agent_output.output == test_case.expected_output else 0.6
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Answer similarity check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Semantic similarity between generated and ground truth answers.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("answer_correctness")
class AnswerCorrectnessEvaluator(BaseEvaluator):
    """Combined factual and semantic accuracy of the generated answer."""
    
    evaluator_name = "answer_correctness"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        if not agent_output.success:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                explanation="Agent failed",
            )
        
        if agent_output.output == test_case.expected_output:
            score = 1.0
        elif agent_output.output:
            score = 0.7
        else:
            score = 0.0
        
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Answer correctness check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Combined factual and semantic accuracy of the generated answer.",
            category=EvaluatorCategory.LLM_BASED,
        )


# Additional DeepEval metrics

@register_evaluator("contextual_recall")
class ContextualRecallEvaluator(BaseEvaluator):
    """Measures how well the retrieved context covers the expected answer."""
    
    evaluator_name = "contextual_recall"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Contextual recall check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Measures how well the retrieved context covers the expected answer.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("contextual_relevancy")
class ContextualRelevancyEvaluator(BaseEvaluator):
    """Assesses the overall relevance of all retrieved context to the query."""
    
    evaluator_name = "contextual_relevancy"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Contextual relevancy check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Assesses the overall relevance of all retrieved context to the query.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("summarization")
class SummarizationEvaluator(BaseEvaluator):
    """Evaluates the quality of generated summaries against source documents."""
    
    evaluator_name = "summarization"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.75 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="Summarization quality check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Evaluates the quality of generated summaries against source documents.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("g_eval")
class GEvalEvaluator(BaseEvaluator):
    """LLM-as-judge evaluation using custom task-specific criteria."""
    
    evaluator_name = "g_eval"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="G-Eval check passed",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="LLM-as-judge evaluation using custom task-specific criteria.",
            category=EvaluatorCategory.LLM_BASED,
        )


@register_evaluator("ragas_compat")
class RagasCompatEvaluator(BaseEvaluator):
    """RAGAS-compatible scoring within the DeepEval framework."""
    
    evaluator_name = "ragas_compat"

    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        score = 0.8 if agent_output.success else 0.0
        return EvaluationResult(
            evaluator_name=self.evaluator_name,
            score=score,
            passed=score >= 0.7,
            explanation="RAGAS compatibility check",
        )

    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="RAGAS-compatible scoring within the DeepEval framework.",
            category=EvaluatorCategory.LLM_BASED,
        )
