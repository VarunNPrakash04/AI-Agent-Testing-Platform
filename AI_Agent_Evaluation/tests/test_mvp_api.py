from fastapi.testclient import TestClient

from src.api.app import create_app
from src.db.database import SessionLocal
from src.db.models import AgentModel
from src.testcases.manager import TestCaseManager
from src.evaluation.plugins.deepeval_evaluator import DeepEvalEvaluator
from src.core.models import TestCase, AgentOutput


def test_dashboard_overview_returns_summary_shape():
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert "stats" in body
    assert "recent_runs" in body
    assert "framework_breakdown" in body
    assert body["stats"]["total_agents"] >= 0
    assert body["stats"]["total_runs"] >= 0


def test_app_seeds_demo_agent_for_first_run():
    session = SessionLocal()
    try:
        session.query(AgentModel).delete()
        session.commit()
    finally:
        session.close()

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    body = response.json()
    assert any(agent["agent_name"] == "Sample Harvest Agent" for agent in body)


def test_txt_files_are_loaded_as_test_suites(tmp_path):
    txt_file = tmp_path / "scenario.txt"
    txt_file.write_text("First scenario\nSecond scenario\n", encoding="utf-8")

    session = SessionLocal()
    try:
        manager = TestCaseManager(session)
        suite = manager.load_from_file(txt_file, suite_name="txt-suite")

        assert suite.total_cases == 2
        assert suite.source_format == "text"

        cases = manager.get_test_cases(suite.id)
        assert [case.input["text"] for case in cases] == ["First scenario", "Second scenario"]
    finally:
        session.close()


def test_deepeval_returns_nonzero_scores():
    """Test that DeepEval evaluator now returns actual scores instead of 0.0"""
    evaluator = DeepEvalEvaluator()
    
    # Test case with successful agent output
    test_case = TestCase(
        test_id="TC001",
        input={"query": "What is AI?"},
        expected_output={"answer": "Artificial Intelligence"},
    )
    
    # Successful agent output that matches expected
    agent_output = AgentOutput(
        output={"answer": "Artificial Intelligence"},
        success=True,
        latency_ms=100,
    )
    
    result = evaluator.evaluate(test_case, agent_output)
    
    # Should get non-zero score now (0.9 = 0.5 base + 0.3 non-empty + 0.2 exact match)
    assert result.score >= 0.5, f"Expected score >= 0.5, got {result.score}"
    assert result.passed is True, "Expected evaluation to pass"
    
    # Test case with non-matching output
    agent_output_mismatch = AgentOutput(
        output={"answer": "Machine Learning"},
        success=True,
        latency_ms=100,
    )
    
    result_mismatch = evaluator.evaluate(test_case, agent_output_mismatch)
    assert result_mismatch.score == 0.8, f"Expected score 0.8, got {result_mismatch.score}"
    
    # Test case with failed agent output
    agent_output_failed = AgentOutput(
        output=None,
        success=False,
        error="Agent timeout",
        latency_ms=100,
    )
    
    result_failed = evaluator.evaluate(test_case, agent_output_failed)
    assert result_failed.score == 0.0
    assert result_failed.passed is False
