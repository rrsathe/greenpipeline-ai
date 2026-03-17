"""Optimization Engine — detect inefficiencies and suggest structural improvements.

Uses NetworkX graph analysis (critical-path, topology) to identify
parallelisation opportunities, missing cache, and pipeline restructuring (hoisting).
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from typing import Any

import networkx as nx

from greenpipeline import OptimizationReport, PipelineDAG, Suggestion

logger = logging.getLogger(__name__)

# Patterns in script lines that suggest package-manager usage
_PACKAGE_MANAGER_PATTERNS = (
    "npm ci",
    "npm install",
    "pip install",
    "yarn install",
    "apt-get install",
    "apk add",
    "bundle install",
    "composer install",
    "cargo build",
    "go mod download",
    "mvn install",
    "gradle build",
)

_DEFAULT_HOIST_IMAGE = "alpine:3.18"
_HOIST_RUNTIME_HEURISTIC_MIN = 1.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_pipeline(dag: PipelineDAG) -> OptimizationReport:
    """Run all detectors and produce an aggregated optimisation report.

    Args:
        dag: The pipeline DAG to analyse.

    Returns:
        :class:`OptimizationReport` with suggestions and runtime estimates.
    """
    suggestions: list[Suggestion] = []

    # 1. Structural Transformations
    suggestions.extend(detect_dependency_hoisting(dag))

    # 2. Local Optimizations
    suggestions.extend(detect_sequential_bottlenecks(dag))
    suggestions.extend(detect_missing_cache(dag))
    suggestions.extend(detect_redundant_jobs(dag))

    total_saving = estimate_time_savings(dag, suggestions)
    optimized_runtime = max(dag.critical_path_min - total_saving, 0.0)

    return OptimizationReport(
        suggestions=suggestions,
        original_runtime_min=dag.critical_path_min,
        optimized_runtime_min=optimized_runtime,
        total_saving_min=total_saving,
    )


def optimize_pipeline_structure(dag: PipelineDAG) -> tuple[nx.DiGraph, dict[str, Any]]:
    """Run structural optimization passes over the pipeline graph.

    Passes:
        1. Pattern Extraction (hoist groups)
        2. Graph Transformation (inject hoisted prep nodes)
        3. Transitive Reduction
        4. Critical Path Recalculation (node-weight based)
    """
    groups = _detect_hoist_groups(dag)

    graph_prime = dag.graph.copy()
    hoist_metadata: dict[str, dict[str, Any]] = {}

    for (image, command), jobs in groups.items():
        prep_node_id = _make_prep_node_id(image=image, command=command)

        graph_prime.add_node(
            prep_node_id,
            stage=dag.jobs[jobs[0]].stage,
            weight=_HOIST_RUNTIME_HEURISTIC_MIN,
            estimated_runtime_min=_HOIST_RUNTIME_HEURISTIC_MIN,
            is_hoisted=True,
            image=image,
            command=command,
        )

        first_job = jobs[0]
        predecessors = list(graph_prime.predecessors(first_job))
        for predecessor in predecessors:
            graph_prime.add_edge(predecessor, prep_node_id, type="hoist-input")

        for job_name in jobs:
            graph_prime.add_edge(prep_node_id, job_name, type="hoist")

            current_runtime = float(graph_prime.nodes[job_name].get("estimated_runtime_min", 0.0))
            adjusted_runtime = max(current_runtime - _HOIST_RUNTIME_HEURISTIC_MIN, 0.1)
            graph_prime.nodes[job_name]["estimated_runtime_min"] = adjusted_runtime

        hoist_metadata[prep_node_id] = {
            "jobs": list(jobs),
            "command": command,
            "image": image,
        }

    reduced_graph = nx.transitive_reduction(graph_prime)
    for node in graph_prime.nodes:
        if node in reduced_graph:
            reduced_graph.nodes[node].update(graph_prime.nodes[node])

    optimized_path = nx.dag_longest_path(reduced_graph)
    optimized_runtime = _path_runtime(reduced_graph, optimized_path)

    return reduced_graph, {
        "hoist_metadata": hoist_metadata,
        "optimized_runtime": optimized_runtime,
        "path": optimized_path,
    }


def detect_dependency_hoisting(dag: PipelineDAG) -> list[Suggestion]:
    """Identify duplicate dependency installations that can be hoisted.

    If multiple downstream jobs run the exact same heavy setup command
    (like `npm ci`), suggest extracting it into a single dedicated upstream
    job that passes the dependencies via cache/artifacts.
    """
    suggestions: list[Suggestion] = []
    groups = _detect_hoist_groups(dag)

    for (_, command), jobs in groups.items():
        if len(jobs) >= 2:
            total_saving = _HOIST_RUNTIME_HEURISTIC_MIN * (len(jobs) - 1)

            suggestions.append(
                Suggestion(
                    category="hoisting",
                    description=(
                        f"Structural Refactor: The command `{command}` is executed redundantly across "
                        f"{len(jobs)} jobs ({', '.join(jobs)}). Hoist this into a single 'prepare_dependencies' "
                        f"job in an early stage, and pass the output to these jobs via `needs:` and artifacts/cache. "
                        f"This eliminates duplicate network egress and compute."
                    ),
                    affected_jobs=jobs,
                    estimated_saving_min=total_saving,
                )
            )

    return suggestions


def _detect_hoist_groups(dag: PipelineDAG) -> dict[tuple[str, str], list[str]]:
    """PASS 1: Identify repeated (image, command) install patterns."""
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)

    for job_name, job in dag.jobs.items():
        base_image = job.image or _DEFAULT_HOIST_IMAGE
        for line in job.script:
            clean_line = line.strip().lower()
            if any(clean_line.startswith(pattern) for pattern in _PACKAGE_MANAGER_PATTERNS):
                groups[(base_image, clean_line)].append(job_name)

    return {key: names for key, names in groups.items() if len(names) >= 2}


def _make_prep_node_id(image: str, command: str) -> str:
    digest = hashlib.sha1(f"{image}::{command}".encode()).hexdigest()[:8]
    return f"prep_{digest}"


def _path_runtime(graph: nx.DiGraph, path: list[str]) -> float:
    return sum(float(graph.nodes[node].get("estimated_runtime_min", 1.0)) for node in path)


def detect_sequential_bottlenecks(dag: PipelineDAG) -> list[Suggestion]:
    """Find jobs within the same stage that could be parallelised via ``needs:``.

    Jobs that share a stage and rely on implicit stage-ordering (no ``needs:``)
    are candidates for parallelisation with explicit ``needs:`` pointing only
    to their actual upstream dependencies.
    """
    suggestions: list[Suggestion] = []
    stage_groups: dict[str, list[str]] = defaultdict(list)

    for name, job in dag.jobs.items():
        stage_groups[job.stage].append(name)

    for stage, job_names in stage_groups.items():
        if len(job_names) <= 1:
            continue

        # Find jobs in this stage that don't use `needs:`
        no_needs = [n for n in job_names if not dag.jobs[n].needs]
        if len(no_needs) >= 2:
            combined_runtime = sum(dag.jobs[n].estimated_runtime_min for n in no_needs)
            max_runtime = max(dag.jobs[n].estimated_runtime_min for n in no_needs)
            saving = combined_runtime - max_runtime

            if saving > 0:
                suggestions.append(
                    Suggestion(
                        category="parallelization",
                        description=(
                            f"In stage '{stage}', jobs {no_needs} run sequentially because "
                            f"GitLab enforces stage ordering. Adding `needs:` allows them "
                            f"to run concurrently, decoupling them from stage synchronization barriers "
                            f"and reducing pipeline critical path by ~{saving:.1f} min."
                        ),
                        affected_jobs=no_needs,
                        estimated_saving_min=saving,
                    )
                )

    return suggestions


def detect_missing_cache(dag: PipelineDAG) -> list[Suggestion]:
    """Flag jobs whose scripts use package managers but have no ``cache:`` config."""
    suggestions: list[Suggestion] = []

    for name, job in dag.jobs.items():
        if job.cache is not None:
            continue
        script_text = " ".join(job.script).lower()
        for pattern in _PACKAGE_MANAGER_PATTERNS:
            if pattern in script_text:
                suggestions.append(
                    Suggestion(
                        category="caching",
                        description=(
                            f"Job '{name}' uses '{pattern}' but has no cache "
                            f"configured. Without caching, registry packages are re-downloaded "
                            f"over the network every pipeline run."
                        ),
                        affected_jobs=[name],
                        estimated_saving_min=1.0,
                    )
                )
                break  # one suggestion per job

    return suggestions


def detect_redundant_jobs(dag: PipelineDAG) -> list[Suggestion]:
    """Identify jobs with identical scripts or images that may be consolidated."""
    suggestions: list[Suggestion] = []
    script_hash: dict[str, list[str]] = defaultdict(list)

    for name, job in dag.jobs.items():
        key = "|".join(job.script)
        script_hash[key].append(name)

    for script_key, names in script_hash.items():
        if len(names) >= 2 and script_key:
            suggestions.append(
                Suggestion(
                    category="redundancy",
                    description=(
                        f"Jobs {names} have identical scripts. "
                        f"Consider consolidating into a single job with "
                        f"parallel outputs or a shared template."
                    ),
                    affected_jobs=names,
                    estimated_saving_min=min(dag.jobs[n].estimated_runtime_min for n in names),
                )
            )

    return suggestions


def estimate_time_savings(dag: PipelineDAG, suggestions: list[Suggestion]) -> float:
    """Compute total estimated time savings from all suggestions.

    Avoids double-counting by capping savings at half the critical-path time.
    """
    raw_saving = sum(s.estimated_saving_min for s in suggestions)
    # Cap at 60% of critical path to avoid unrealistic estimates
    return min(raw_saving, dag.critical_path_min * 0.6)
