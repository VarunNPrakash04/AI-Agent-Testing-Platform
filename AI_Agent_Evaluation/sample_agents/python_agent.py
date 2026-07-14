"""
Sample Python Agent
===================

A dummy agent implemented as a Python class. 
This simulates a harvesting agent that extracts metrics from a datasource.
"""

import time
import random

class DummyHarvestAgent:
    """
    Simulates a Python-based AI agent.
    Must implement the `run(input_data: dict) -> dict` contract.
    """
    
    def run(self, input_data: dict) -> dict:
        """
        Process the input and return a dictionary output.
        """
        # Simulate some processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        datasource_id = input_data.get("datasource_id", "unknown")
        metadata_type = input_data.get("metadata_type", "unknown")
        
        # Simulate extraction based on input
        if metadata_type == "powerbi":
            metrics = [
                {"metric_name": "Total Sales", "formula": "SUM(Sales)", "owner": "Finance"},
                {"metric_name": "Active Users", "formula": "DISTINCTCOUNT(Users)", "owner": "Product"}
            ]
        elif metadata_type == "tableau":
            metrics = [
                {"metric_name": "Revenue YTD", "formula": "RUNNING_SUM(Revenue)", "owner": "Finance"}
            ]
        else:
            metrics = []
            
        return {
            "status": "success",
            "datasource_id": datasource_id,
            "metrics": metrics,
            "extracted_count": len(metrics)
        }
