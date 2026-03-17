"""Tests for greenpipeline.carbon module."""

from pathlib import Path

from greenpipeline import CarbonReport
from greenpipeline.carbon import compute_carbon_delta, estimate_emissions
from greenpipeline.parser import build_dag, parse_gitlab_ci

_SAMPLE = (
    Path(__file__).resolve().parent.parent / "greenpipeline" / "samples" / "sample_pipeline.yml"
)


def _get_sample_dag():
    config = parse_gitlab_ci(_SAMPLE)
    return build_dag(config)


class TestEstimateEmissions:
    def test_returns_carbon_report(self):
        dag = _get_sample_dag()
        report = estimate_emissions(dag, optimized_runtime_min=dag.critical_path_min * 0.5)
        assert isinstance(report, CarbonReport)

    def test_non_negative_values(self):
        dag = _get_sample_dag()
        report = estimate_emissions(dag)
        assert report.current_emissions_kg >= 0
        assert report.optimized_emissions_kg >= 0
        assert report.current_energy_kwh >= 0

    def test_reduction_when_optimized(self):
        dag = _get_sample_dag()
        report = estimate_emissions(dag, optimized_runtime_min=dag.critical_path_min * 0.5)
        assert report.reduction_pct >= 0


class TestComputeCarbonDelta:
    def test_correct_delta(self):
        report = compute_carbon_delta(
            current_emissions_kg=2.0,
            optimized_emissions_kg=1.0,
            current_energy_kwh=5.0,
            optimized_energy_kwh=2.5,
        )
        assert report.delta_emissions_kg == 1.0
        assert report.reduction_pct == 50.0

    def test_zero_current(self):
        report = compute_carbon_delta(0.0, 0.0)
        assert report.reduction_pct == 0.0
