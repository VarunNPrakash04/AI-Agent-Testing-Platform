"""
Sample REST Agent
=================

A dummy agent implemented as a standalone FastAPI service.
This simulates a RAG chatbot or general text-generation agent.

Run this script to start the agent:
    uvicorn sample_agents.rest_agent:app --port 9001
"""

import time
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Sample REST Agent")

class AgentInput(BaseModel):
    query: str | None = None
    context: list[str] | None = None
    # Flexible catch-all for other fields
    model_config = {"extra": "allow"}

@app.get("/health")
def health_check():
    """Endpoint for the testing platform to verify reachability."""
    return {"status": "healthy"}

@app.post("/api/v1/run")
def run_agent(input_data: AgentInput):
    """
    Main endpoint for the agent. Processes input and returns output.
    """
    # Simulate processing delay
    time.sleep(random.uniform(0.2, 0.8))
    
    query = input_data.query or getattr(input_data, "prompt", "Hello")
    
    if "error" in query.lower():
        raise HTTPException(status_code=500, detail="Simulated agent failure")
        
    answer = f"This is a simulated response to: '{query}'."
    if input_data.context:
        answer += f" Used {len(input_data.context)} context documents."
        
    return {
        "answer": answer,
        "confidence": round(random.uniform(0.7, 0.99), 2),
        "source_nodes": ["doc_1", "doc_2"] if input_data.context else []
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9001)
