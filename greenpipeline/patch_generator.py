"""Generate optimized GitLab CI YAML patches."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

import yaml

from greenpipeline import OptimizationReport, PipelineDAG

logger = logging.getLogger(__name__)


def detect_cache_path(script_lines: list[str]) -> str:
    """Heuristic to detect appropriate cache path based on script.

    Args:
        script_lines: The script section of the job.
    Returns:
        A string path to cache.
    """
    script_text = " ".join(script_lines).lower()

    if "npm" in script_text or "yarn" in script_text:
        return "node_modules/"
    elif "pip" in script_text or "python" in script_text:
        return ".cache/pip/"
    elif "cargo" in script_text:
        return "target/"
    elif "maven" in script_text or "mvn" in script_text:
        return ".m2/"
    else:
        return "vendor/"


def generate_patch(
    original_config: dict[str, Any],
    dag: PipelineDAG,
    opt: OptimizationReport,
) -> str:
    """Generate a complete optimized .gitlab-ci.yml patch as a string.

    Args:
        original_config: The raw parsed dictionary of `.gitlab-ci.yml`.
        dag: The parsed PipelineDAG.
        opt: The OptimizationReport.

    Returns:
        The optimized YAML as a string.
    """
    # Create a deep copy so we don't mutate the original dictionary
    config = deepcopy(original_config)

    for suggestion in opt.suggestions:
        if suggestion.category == "caching":
            for job_name in suggestion.affected_jobs:
                job_cfg = config.get(job_name)
                if not isinstance(job_cfg, dict):
                    continue

                job_info = dag.jobs.get(job_name)
                if job_info is None:
                    continue

                cache_path = detect_cache_path(job_info.script)
                cache = job_cfg.setdefault("cache", {})
                if not isinstance(cache, dict):
                    continue

                paths = cache.setdefault("paths", [])
                if not isinstance(paths, list):
                    continue

                if cache_path not in paths:
                    paths.append(cache_path)
                    logger.info(
                        "Added cache to job %s: [%s]",
                        job_name,
                        f"'{cache_path}'",
                    )

        elif suggestion.category == "parallelization":
            for job_name in suggestion.affected_jobs:
                job_cfg = config.get(job_name)
                if not isinstance(job_cfg, dict):
                    continue

                job_info_parallel = dag.jobs.get(job_name)
                if job_info_parallel is None:
                    continue

                stage_idx = (
                    dag.stages.index(job_info_parallel.stage)
                    if job_info_parallel.stage in dag.stages
                    else 0
                )

                needs = []
                if stage_idx > 0:
                    prev_stage = dag.stages[stage_idx - 1]
                    needs = [
                        j
                        for j, info in dag.jobs.items()
                        if info.stage == prev_stage and j != job_name
                    ]

                if needs:
                    needs_list = job_cfg.setdefault("needs", [])
                    if not isinstance(needs_list, list):
                        continue

                    for n in needs:
                        if n not in needs_list:
                            needs_list.append(n)
                    logger.info(
                        "Added 'needs' to job %s: %s (for parallelization)",
                        job_name,
                        ", ".join(needs),
                    )

    # Convert back to YAML with nice formatting
    class CustomDumper(yaml.SafeDumper):
        def increase_indent(self, flow=False, indentless=False):
            return super().increase_indent(flow, False)

    return yaml.dump(
        config,
        Dumper=CustomDumper,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
