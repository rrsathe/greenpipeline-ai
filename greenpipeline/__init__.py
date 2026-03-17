"""GreenPipeline AI — CI/CD sustainability analysis system.

Shared data contracts used across all modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

# ---------------------------------------------------------------------------
# Core data contracts
# ---------------------------------------------------------------------------


@dataclass
class JobInfo:
    """Metadata for a single CI/CD job."""

    name: str
    stage: str
    script: list[str] = field(default_factory=list)
    image: str | None = None
    needs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    cache: dict[str, Any] | None = None
    parallel: int | None = None
    estimated_runtime_min: float = 1.0  # heuristic default
    tags: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] | None = None
    rules: list[dict] | None = None


@dataclass
class PipelineDAG:
    """Wraps a NetworkX DiGraph representing the pipeline DAG plus metadata."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)
    stages: list[str] = field(default_factory=list)
    jobs: dict[str, JobInfo] = field(default_factory=dict)
    total_estimated_runtime_min: float = 0.0
    critical_path_min: float = 0.0
    raw_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Suggestion:
    """A single optimisation suggestion."""

    category: str  # e.g. "parallelization", "caching", "redundancy"
    description: str
    affected_jobs: list[str] = field(default_factory=list)
    estimated_saving_min: float = 0.0


@dataclass
class OptimizationReport:
    """Aggregated optimisation report for a pipeline."""

    suggestions: list[Suggestion] = field(default_factory=list)
    original_runtime_min: float = 0.0
    optimized_runtime_min: float = 0.0
    total_saving_min: float = 0.0


@dataclass
class CarbonReport:
    """Carbon emission comparison between current and optimised pipelines."""

    current_emissions_kg: float = 0.0
    optimized_emissions_kg: float = 0.0
    delta_emissions_kg: float = 0.0
    reduction_pct: float = 0.0
    current_energy_kwh: float = 0.0
    optimized_energy_kwh: float = 0.0
    methodology: str = "CodeCarbon OfflineEmissionsTracker + SCI"


@dataclass
class ReasoningReport:
    """AI explanations and scoring for the pipeline."""

    explanations: list[str] = field(default_factory=list)
    efficiency_score: int = 100
    score_breakdown: dict[str, int] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Composite result aggregating all analysis outputs."""

    dag: PipelineDAG
    optimization: OptimizationReport
    carbon: CarbonReport

    # optional layers
    reasoning: ReasoningReport | None = None
    visualization_path: str | None = None
    session_id: str | None = None
    optimized_yaml: str | None = None


__all__ = [
    "JobInfo",
    "PipelineDAG",
    "Suggestion",
    "OptimizationReport",
    "CarbonReport",
    "ReasoningReport",
    "PipelineResult",
]
