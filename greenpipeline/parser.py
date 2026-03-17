"""Pipeline Parser — parse .gitlab-ci.yml and build pipeline DAG.

Handles stages, jobs, dependencies (needs / dependencies), caching,
parallel configuration, and implicit stage-ordering edges.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import networkx as nx
import yaml

from greenpipeline import JobInfo, PipelineDAG

logger = logging.getLogger(__name__)

# Keys that are *not* job definitions in a GitLab CI config
_RESERVED_KEYS = frozenset(
    {
        "stages",
        "variables",
        "default",
        "include",
        "workflow",
        "image",
        "services",
        "before_script",
        "after_script",
        "cache",
        "pages",
    }
)

# Heuristic: each script line ≈ 0.5 min runtime
_RUNTIME_PER_LINE = 0.5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_gitlab_ci(yaml_path: str | Path) -> dict[str, Any]:
    """Load and safely parse a ``.gitlab-ci.yml`` file.

    Args:
        yaml_path: Path to the YAML file.

    Returns:
        Parsed YAML as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is malformed YAML.
    """
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        config: dict = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise ValueError(
            f"Expected YAML mapping at top level, got {type(config).__name__}"
        )
    return config


def extract_stages(config: dict[str, Any]) -> list[str]:
    """Return the ordered list of stage names.

    Falls back to ``["build", "test", "deploy"]`` if no ``stages:`` key.
    """
    stages = config.get("stages")
    if stages and isinstance(stages, list):
        return list(stages)
    return ["build", "test", "deploy"]


def extract_jobs(config: dict[str, Any]) -> dict[str, JobInfo]:
    """Extract all job definitions from the parsed config.

    Args:
        config: Parsed YAML dictionary.

    Returns:
        Mapping of job name → :class:`JobInfo`.
    """
    stages = extract_stages(config)
    default_stage = stages[0] if stages else "test"
    jobs: dict[str, JobInfo] = {}

    for key, value in config.items():
        # Skip reserved / non-job keys and hidden jobs (starting with '.')
        if key in _RESERVED_KEYS or key.startswith(".") or not isinstance(value, dict):
            continue

        try:
            script_raw = value.get("script", [])
            script = script_raw if isinstance(script_raw, list) else [str(script_raw)]

            # Needs can be list of strings or list of dicts with "job" key
            raw_needs = value.get("needs", [])
            needs: list[str] = []
            if isinstance(raw_needs, list):
                for n in raw_needs:
                    if isinstance(n, str):
                        needs.append(n)
                    elif isinstance(n, dict) and "job" in n:
                        needs.append(n["job"])

            deps = value.get("dependencies", [])
            if not isinstance(deps, list):
                deps = []

            cache_val = value.get("cache")
            if isinstance(cache_val, list) and len(cache_val) > 0:
                cache_val = cache_val[0]  # take first cache config
            cache = cache_val if isinstance(cache_val, dict) else None

            parallel = value.get("parallel")
            if parallel is not None:
                parallel = int(parallel) if isinstance(parallel, (int, str)) else None

            runtime = max(len(script) * _RUNTIME_PER_LINE, 0.5)

            tags = value.get("tags", [])
            if not isinstance(tags, list):
                tags = []

            artifacts = value.get("artifacts")
            if artifacts is not None and not isinstance(artifacts, dict):
                artifacts = None

            rules = value.get("rules")
            if rules is not None and not isinstance(rules, list):
                rules = None

            jobs[key] = JobInfo(
                name=key,
                stage=value.get("stage", default_stage),
                script=script,
                image=value.get("image"),
                needs=needs,
                dependencies=deps,
                cache=cache,
                parallel=parallel,
                estimated_runtime_min=runtime,
                tags=tags,
                artifacts=artifacts,
                rules=rules,
            )
        except Exception:
            logger.warning("Skipping malformed job definition: %s", key, exc_info=True)

    return jobs


def build_dag(config: dict[str, Any]) -> PipelineDAG:
    """Construct a pipeline DAG from a parsed ``.gitlab-ci.yml`` config.

    Nodes represent jobs; edges represent dependency relationships.

    * **Explicit edges** come from ``needs:`` declarations.
    * **Implicit edges** connect jobs in consecutive stages when a job
      does *not* declare ``needs:``.

    Args:
        config: Parsed YAML dictionary.

    Returns:
        Populated :class:`PipelineDAG`.
    """
    stages = extract_stages(config)
    jobs = extract_jobs(config)
    G = nx.DiGraph()

    # Add nodes
    for name, job in jobs.items():
        stage_idx = stages.index(job.stage) if job.stage in stages else 0
        G.add_node(
            name,
            stage=job.stage,
            stage_index=stage_idx,
            estimated_runtime_min=job.estimated_runtime_min,
            has_cache=job.cache is not None,
            image=job.image or "",
            parallel=job.parallel,
        )

    # Add explicit edges from `needs:`
    for name, job in jobs.items():
        if job.needs:
            for dep in job.needs:
                if dep in jobs:
                    G.add_edge(dep, name, type="needs")
                else:
                    logger.warning("Job '%s' needs unknown job '%s'", name, dep)

    # Add implicit stage-ordering edges for jobs *without* `needs:`
    stage_jobs: dict[str, list[str]] = {s: [] for s in stages}
    for name, job in jobs.items():
        if job.stage in stage_jobs:
            stage_jobs[job.stage].append(name)

    for name, job in jobs.items():
        if not job.needs:
            stage_idx = stages.index(job.stage) if job.stage in stages else -1
            if stage_idx > 0:
                prev_stage = stages[stage_idx - 1]
                for prev_job in stage_jobs.get(prev_stage, []):
                    G.add_edge(prev_job, name, type="stage-order")

    # Compute metrics
    total_runtime = sum(j.estimated_runtime_min for j in jobs.values())

    try:
        critical_path = nx.dag_longest_path_length(G, weight="estimated_runtime_min")
    except (nx.NetworkXError, nx.NetworkXUnfeasible):
        critical_path = total_runtime

    return PipelineDAG(
        graph=G,
        stages=stages,
        jobs=jobs,
        total_estimated_runtime_min=total_runtime,
        critical_path_min=critical_path,
        raw_config=config,
    )
