"""Tests for greenpipeline.pipeline_runner module (end-to-end)."""

from greenpipeline import PipelineResult
from greenpipeline.pipeline_runner import create_session, run_analysis


class TestCreateSession:
    def test_returns_dict_with_session_id(self):
        session = create_session()
        assert hasattr(session, "session_id")
        assert session.session_id is not None


class TestRunAnalysis:
    def test_end_to_end_with_sample(self):
        result = run_analysis()
        assert isinstance(result, PipelineResult)
        assert result.dag is not None
        assert result.optimization is not None
        assert result.carbon is not None
        assert result.session_id is not None

    def test_dag_has_jobs(self):
        result = run_analysis()
        assert len(result.dag.jobs) >= 5

    def test_optimization_has_suggestions(self):
        result = run_analysis()
        assert isinstance(result.optimization.suggestions, list)

    def test_carbon_has_values(self):
        result = run_analysis()
        assert result.carbon.current_emissions_kg >= 0
