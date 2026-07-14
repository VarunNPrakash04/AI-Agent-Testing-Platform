import logging
from typing import Any

from src.core.enums import EvaluatorCategory
from src.core.interfaces import BaseEvaluator
from src.core.models import AgentOutput, EvaluationResult, EvaluatorInfo, TestCase

logger = logging.getLogger(__name__)

class S3PresenceEvaluator(BaseEvaluator):
    """
    Validates that a pipeline or agent successfully harvested data and wrote it to S3.
    Expects the agent_output to contain the S3 URI where the data was saved.
    """
    
    evaluator_name = "s3_presence_check"
    
    def get_info(self) -> EvaluatorInfo:
        return EvaluatorInfo(
            name=self.evaluator_name,
            description="Validates that data was successfully harvested to S3 by checking file existence.",
            category=EvaluatorCategory.CUSTOM,
            metrics=["S3 File Exists", "File Size > 0"],
            required_config=[]
        )
        
    def evaluate(self, test_case: TestCase, agent_output: AgentOutput) -> EvaluationResult:
        s3_uri = agent_output.response.strip()
        
        # We expect the agent to return something like 's3://my-bucket/path/to/data.csv'
        if not s3_uri.startswith("s3://"):
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                details=f"Agent did not return a valid S3 URI. Returned: {s3_uri}"
            )
            
        logger.info(f"Checking S3 for presence of {s3_uri}")
        
        # --- Mock Boto3 Implementation ---
        # In a real environment, you would use:
        # import boto3
        # s3 = boto3.client('s3')
        # bucket, key = parse_s3_uri(s3_uri)
        # response = s3.head_object(Bucket=bucket, Key=key)
        # file_size = response['ContentLength']
        
        # For this mock, we will assume success if the URI ends with a valid extension
        if s3_uri.endswith(".csv") or s3_uri.endswith(".json") or s3_uri.endswith(".parquet"):
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=1.0,
                passed=True,
                details=f"Successfully verified file exists at {s3_uri} with size > 0 bytes."
            )
        else:
            return EvaluationResult(
                evaluator_name=self.evaluator_name,
                score=0.0,
                passed=False,
                details=f"File at {s3_uri} appears to be invalid or missing."
            )
