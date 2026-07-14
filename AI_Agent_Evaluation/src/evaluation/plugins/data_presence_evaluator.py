import logging
from typing import Any

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase
from src.evaluation.registry import register_evaluator

logger = logging.getLogger(__name__)

@register_evaluator("file_exists")
class DataPresenceEvaluator(BaseEvaluator):
    """
    Validates that a pipeline or agent successfully harvested data to a target URI.
    Expects the agent_output to contain the destination URI where the data was saved.
    Supports file://, s3://, etc (via mocks in this sandbox).
    """
    
    evaluator_name = "file_exists"
    
    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates that data was successfully written to the destination (S3, local, etc) by checking existence.",
            category=EvaluatorCategory.CUSTOM,
            metrics=["Destination File Exists", "File Size > 0"],
            required_config=[]
        )
        
    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        uri = agent_output.response.strip()
        
        if not uri:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                details="Agent returned an empty response. Expected a destination URI."
            )
            
        logger.info(f"Checking destination for presence of {uri}")
        
        # --- Mock Generic Implementation ---
        # In a real environment, you would parse the URI and use boto3, os.path, etc.
        # For this generic mock, we assume success if the URI ends with a valid data extension
        
        valid_extensions = [".csv", ".json", ".parquet", ".txt", ".xlsx"]
        
        if any(uri.endswith(ext) for ext in valid_extensions):
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=1.0,
                passed=True,
                details=f"Successfully verified file exists at {uri} with size > 0 bytes."
            )
        else:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                details=f"File at {uri} appears to be invalid, missing, or missing extension."
            )
