"""Generate optimized GitLab CI YAML patches via structural DAG transformations."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

import yaml

from greenpipeline import OptimizationReport, PipelineDAG

logger = logging.getLogger(__name__)


def detect_cache_path(script_lines: list[str]) -> str:
    """Heuristic to detect appropriate cache path based on script."""
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
    """Generate a complete optimized .gitlab-ci.yml patch as a string."""
    config = deepcopy(original_config)

    for suggestion in opt.suggestions:
        # -------------------------------------------------------------------
        # 1. STRUCTURAL DAG REWRITE: DEPENDENCY HOISTING
        # -------------------------------------------------------------------
        if suggestion.category == "hoisting":
            affected = suggestion.affected_jobs
            if not affected:
                continue

            # Identify the common command and the base image
            common_cmd = None
            base_image = "alpine:3.18"
            for job_name in affected:
                job_cfg = config.get(job_name, {})
                if "image" in job_cfg:
                    base_image = job_cfg["image"]
                script = job_cfg.get("script", [])
                for line in script:
                    clean_line = line.strip().lower()
                    if any(p in clean_line for p in ["npm ci", "npm install", "pip install"]):
                        common_cmd = line
                        break
                if common_cmd:
                    break

            if not common_cmd:
                continue

            cache_path = detect_cache_path([common_cmd])
            prep_job_name = "prepare_dependencies"
            first_stage = config.get("stages", ["build"])[0]

            # Inject the new master dependency job into the DAG
            config[prep_job_name] = {
                "stage": first_stage,
                "image": base_image,
                "script": [common_cmd],
                "cache": {"key": "global-deps-cache", "paths": [cache_path], "policy": "pull-push"},
            }
            logger.info(
                "Structural Rewrite: Created '%s' to hoist '%s'", prep_job_name, common_cmd.strip()
            )

            # Strip the redundant commands from downstream jobs and rewire them
            for job_name in affected:
                job_cfg = config.get(job_name)
                if not isinstance(job_cfg, dict):
                    continue

                # Strip the command
                old_script = job_cfg.get("script", [])
                new_script = [line for line in old_script if line.strip() != common_cmd.strip()]
                job_cfg["script"] = new_script

                # Rewire the DAG
                needs = job_cfg.setdefault("needs", [])
                if prep_job_name not in needs:
                    needs.append(prep_job_name)

                # Configure downstream pull cache
                cache = job_cfg.setdefault("cache", {})
                cache["key"] = "global-deps-cache"
                paths = cache.setdefault("paths", [])
                if cache_path not in paths:
                    paths.append(cache_path)
                cache["policy"] = "pull"

                logger.info(
                    "Rewrote job '%s': removed duplicate install, added edge to '%s'",
                    job_name,
                    prep_job_name,
                )

        # -------------------------------------------------------------------
        # 2. LOCAL OPTIMIZATION: CACHING
        # -------------------------------------------------------------------
        elif suggestion.category == "caching":
            for job_name in suggestion.affected_jobs:
                job_cfg = config.get(job_name)
                if not isinstance(job_cfg, dict):
                    continue
                # Skip if hoisting already rewrote this job's cache
                if job_cfg.get("cache", {}).get("key") == "global-deps-cache":
                    continue

                job_info = dag.jobs.get(job_name)
                if job_info is None:
                    continue

                cache_path = detect_cache_path(job_info.script)
                cache = job_cfg.setdefault("cache", {})
                paths = cache.setdefault("paths", [])
                if cache_path not in paths:
                    paths.append(cache_path)
                    logger.info("Added cache to job %s: ['%s']", job_name, cache_path)

        # -------------------------------------------------------------------
        # 3. TOPOLOGY REWRITE: PARALLELIZATION
        # -------------------------------------------------------------------
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

                if "needs" not in job_cfg:
                    job_cfg["needs"] = []

                needs_list = job_cfg["needs"]
                if not isinstance(needs_list, list):
                    continue

                if stage_idx == 0:
                    # First stage parallelization: empty needs array
                    logger.info(
                        "Added 'needs: []' to job %s for immediate parallel execution", job_name
                    )
                else:
                    # Later stage parallelization: explicitly depend on previous stage jobs
                    prev_stage = dag.stages[stage_idx - 1]
                    needs = [
                        j
                        for j, info in dag.jobs.items()
                        if info.stage == prev_stage and j != job_name
                    ]
                    for n in needs:
                        if n not in needs_list:
                            needs_list.append(n)
                    logger.info("Added explicit 'needs' to job %s for parallelization", job_name)

    # Convert back to YAML
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
