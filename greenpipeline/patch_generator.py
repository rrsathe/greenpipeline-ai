"""Generate optimized GitLab CI YAML by projecting the optimized DiGraph."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

import networkx as nx
import yaml

from greenpipeline import OptimizationReport, PipelineDAG
from greenpipeline.optimizer import optimize_pipeline_structure

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
    """Backward-compatible entrypoint that now emits graph-based YAML."""
    _ = opt
    optimized_graph, _meta = optimize_pipeline_structure(dag)
    return generate_graph_based_patch(original_config, dag, optimized_graph)


def generate_graph_based_patch(
    original_config: dict[str, Any],
    dag: PipelineDAG,
    optimized_graph: nx.DiGraph,
) -> str:
    """Pass 5: Project the optimized DiGraph back into GitLab CI YAML."""
    new_config = _extract_global_config(original_config, dag)

    for node_id in nx.topological_sort(optimized_graph):
        node_data = optimized_graph.nodes[node_id]

        if bool(node_data.get("is_hoisted")):
            new_config[node_id] = _emit_hoisted_job(node_id, node_data)
            logger.info("Structural Rewrite: emitted hoisted job %s", node_id)
            continue

        original_job_cfg = original_config.get(node_id)
        if not isinstance(original_job_cfg, dict):
            continue

        job_cfg = deepcopy(original_job_cfg)
        direct_predecessors = list(optimized_graph.predecessors(node_id))
        hoisted_nodes = [
            node
            for node in optimized_graph.nodes
            if bool(optimized_graph.nodes[node].get("is_hoisted"))
        ]

        script_val = job_cfg.get("script", [])
        script_lines = script_val if isinstance(script_val, list) else [str(script_val)]
        explicit_hoisted_needs: list[str] = []

        for hoisted_node in hoisted_nodes:
            hoisted_data = optimized_graph.nodes[hoisted_node]
            hoisted_command = str(hoisted_data.get("command", "")).strip().lower()
            if not hoisted_command:
                continue

            has_hoisted_command = any(
                line.strip().lower() == hoisted_command for line in script_lines
            )
            if not has_hoisted_command:
                continue

            if not nx.has_path(optimized_graph, hoisted_node, node_id):
                continue

            script_lines = [
                line for line in script_lines if line.strip().lower() != hoisted_command
            ]
            explicit_hoisted_needs.append(hoisted_node)

            cache = job_cfg.setdefault("cache", {})
            if isinstance(cache, dict):
                cache_path = detect_cache_path([hoisted_command])
                cache["key"] = f"cache-{hoisted_node}"
                paths = cache.setdefault("paths", [])
                if isinstance(paths, list) and cache_path not in paths:
                    paths.append(cache_path)
                cache["policy"] = "pull"

        job_cfg["script"] = script_lines

        combined_needs: list[str] = []
        for need in explicit_hoisted_needs + direct_predecessors:
            if need not in combined_needs:
                combined_needs.append(need)

        if combined_needs:
            job_cfg["needs"] = combined_needs
        else:
            job_info = dag.jobs.get(node_id)
            first_stage = dag.stages[0] if dag.stages else "build"
            if job_info is not None and job_info.stage == first_stage:
                job_cfg["needs"] = []
            else:
                job_cfg.pop("needs", None)

        new_config[node_id] = job_cfg

    return _dump_yaml(new_config)


def _extract_global_config(original_config: dict[str, Any], dag: PipelineDAG) -> dict[str, Any]:
    global_config: dict[str, Any] = {}

    for key, value in original_config.items():
        if key not in dag.jobs:
            global_config[key] = deepcopy(value)

    global_config["stages"] = original_config.get(
        "stages",
        ["build", "test", "security", "deploy"],
    )
    if "variables" in original_config:
        global_config["variables"] = deepcopy(original_config["variables"])

    return global_config


def _emit_hoisted_job(node_id: str, data: dict[str, Any]) -> dict[str, Any]:
    command = str(data.get("command", "")).strip()
    cache_path = detect_cache_path([command])

    return {
        "stage": data.get("stage", "build"),
        "image": data.get("image", "alpine:3.18"),
        "script": [command],
        "cache": {
            "key": f"cache-{node_id}",
            "paths": [cache_path],
            "policy": "pull-push",
        },
        "artifacts": {
            "paths": [cache_path],
            "expire_in": "1 hour",
        },
    }


def _dump_yaml(config: dict[str, Any]) -> str:
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
