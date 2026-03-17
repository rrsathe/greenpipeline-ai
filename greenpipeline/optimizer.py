"""Optimization Engine — detect inefficiencies and suggest improvements.

Uses NetworkX graph analysis (critical-path, topology) to identify
parallelisation opportunities, missing cache, and redundant jobs.
"""

from __future__ import annotations

import logging
from collections import defaultdict

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
                            f"to run in parallel and reduces pipeline runtime by ~{saving:.1f} min."
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
                            f"configured. Adding cache can save ~0.5–2 min per run."
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
