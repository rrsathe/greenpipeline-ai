"""Generate optimized GitLab CI YAML patches."""

from __future__ import annotations

import logging
from copy import deepcopy

import yaml

from greenpipeline import OptimizationReport, PipelineDAG
from greenpipeline.parser import JobInfo

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


def generate_patch(original_config: dict, dag: PipelineDAG, opt: OptimizationReport) -> str:
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
                if job_name in config and isinstance(config[job_name], dict):
                    job_info: JobInfo = dag.jobs.get(job_name)
                    if job_info is not None:
                        cache_path = detect_cache_path(job_info.script)
                        if "cache" not in config[job_name]:
                            config[job_name]["cache"] = {}
                        if "paths" not in config[job_name]["cache"]:
                            config[job_name]["cache"]["paths"] = []
                        if cache_path not in config[job_name]["cache"]["paths"]:
                            config[job_name]["cache"]["paths"].append(cache_path)
                            logger.info("Added cache to job %s: [%s]", job_name, f"'{cache_path}'")
                            
        elif suggestion.category == "parallelization":
            for job_name in suggestion.affected_jobs:
                if job_name in config and isinstance(config[job_name], dict):
                    if dag.graph is not None:
                        # Find dependencies from previous stages
                        job_info = dag.jobs.get(job_name)
                        if job_info is not None:
                            stage_idx = dag.stages.index(job_info.stage) if job_info.stage in dag.stages else 0
                            
                            # Add explicit needs from previous stage to bypass implicit ordering
                            needs = []
                            if stage_idx > 0:
                                prev_stage = dag.stages[stage_idx - 1]
                                needs = [j for j, info in dag.jobs.items() if info.stage == prev_stage]
                            
                            if needs:
                                if "needs" not in config[job_name]:
                                    config[job_name]["needs"] = []
                                for n in needs:
                                    if n not in config[job_name]["needs"]:
                                        config[job_name]["needs"].append(n)
                                logger.info("Added 'needs' to job %s: %s (for parallelization)", job_name, ", ".join(needs))

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
