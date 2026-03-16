"""Tests for greenpipeline.parser module."""

from pathlib import Path

import networkx as nx
import pytest

from greenpipeline.parser import build_dag, extract_jobs, extract_stages, parse_gitlab_ci

_SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "sample_pipeline.yml"


class TestParseGitlabCi:
    def test_loads_valid_yaml(self):
        config = parse_gitlab_ci(_SAMPLE)
        assert isinstance(config, dict)
        assert "stages" in config

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            parse_gitlab_ci("/nonexistent/file.yml")


class TestExtractStages:
    def test_returns_stages_from_config(self):
        config = parse_gitlab_ci(_SAMPLE)
        stages = extract_stages(config)
        assert "build" in stages
        assert "test" in stages
        assert "deploy" in stages

    def test_fallback_on_missing_stages(self):
        stages = extract_stages({"job_a": {"script": ["echo hi"]}})
        assert stages == ["build", "test", "deploy"]


class TestExtractJobs:
    def test_extracts_all_jobs(self):
        config = parse_gitlab_ci(_SAMPLE)
        jobs = extract_jobs(config)
        assert len(jobs) >= 5  # sample has 8 jobs
        assert "build_app" in jobs
        assert "unit_tests" in jobs

    def test_job_metadata(self):
        config = parse_gitlab_ci(_SAMPLE)
        jobs = extract_jobs(config)
        build_app = jobs["build_app"]
        assert build_app.stage == "build"
        assert build_app.cache is not None
        assert len(build_app.script) > 0

    def test_needs_extracted(self):
        config = parse_gitlab_ci(_SAMPLE)
        jobs = extract_jobs(config)
        unit = jobs["unit_tests"]
        assert "build_app" in unit.needs


class TestBuildDag:
    def test_creates_digraph(self):
        config = parse_gitlab_ci(_SAMPLE)
        dag = build_dag(config)
        assert isinstance(dag.graph, nx.DiGraph)
        assert len(dag.graph.nodes) >= 5

    def test_has_edges(self):
        config = parse_gitlab_ci(_SAMPLE)
        dag = build_dag(config)
        assert len(dag.graph.edges) > 0

    def test_critical_path_positive(self):
        config = parse_gitlab_ci(_SAMPLE)
        dag = build_dag(config)
        assert dag.critical_path_min > 0

    def test_stages_preserved(self):
        config = parse_gitlab_ci(_SAMPLE)
        dag = build_dag(config)
        assert dag.stages == ["build", "test", "security", "deploy"]

    def test_no_crash_on_minimal_yaml(self):
        config = {"stages": ["build"], "job_a": {"stage": "build", "script": ["echo hello"]}}
        dag = build_dag(config)
        assert len(dag.graph.nodes) == 1
