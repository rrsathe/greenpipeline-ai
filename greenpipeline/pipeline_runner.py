"""Pipeline Runner — orchestrated entrypoint for GreenPipeline AI.

Directly imports from local repositories:
  - **AIOpsLab**: ``aiopslab.session.Session`` for session tracking,
    ``aiopslab.orchestrator.parser.ResponseParser`` for response parsing
  - **Dagger**: ``dagger`` Python SDK for containerised pipeline simulation
  - **CodeCarbon**: via ``greenpipeline.carbon`` (which imports locally)

Wires parser → optimizer → carbon → visualizer into a single analysis flow.
"""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, cast

from greenpipeline import PipelineResult
from greenpipeline.carbon import estimate_emissions
from greenpipeline.optimizer import analyze_pipeline
from greenpipeline.parser import build_dag, parse_gitlab_ci
from greenpipeline.patch_generator import generate_patch
from greenpipeline.visualizer import draw_pipeline_dag, export_dag_image

# Ensure the project root is on sys.path for direct script execution.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

_SAMPLES_DIR = Path(__file__).parent / "samples"
AIOpsSession = cast(Any, None)
AIOpsResponseParser = cast(Any, None)
dagger_sdk = cast(Any, None)


def _has_kube_config() -> bool:
    """Return True if Kubernetes config is available."""
    kubeconfig_env = os.getenv("KUBECONFIG")
    if kubeconfig_env:
        for entry in kubeconfig_env.split(":"):
            if Path(entry).expanduser().exists():
                return True
    return (Path.home() / ".kube" / "config").exists()


# ---- Local AIOpsLab imports ----
if _has_kube_config():
    try:
        from aiopslab.orchestrator.parser import (
            ResponseParser as AIOpsResponseParser,  # type: ignore[import-not-found]
        )
        from aiopslab.session import (
            Session as AIOpsSession,  # type: ignore[import-not-found]
        )

        _HAS_AIOPSLAB = True
    except Exception as _err:
        logger.warning("Could not import local AIOpsLab: %s", _err)
        _HAS_AIOPSLAB = False
else:
    logger.info("Skipping AIOpsLab import: no Kubernetes config found")
    _HAS_AIOPSLAB = False

# ---- Local Dagger SDK imports ----
try:
    import dagger as dagger_sdk  # type: ignore[import-not-found]  # from dagger/sdk/python/src/

    _HAS_DAGGER = True
except Exception as _err:
    logger.warning("Could not import local Dagger SDK: %s", _err)
    _HAS_DAGGER = False


# ---------------------------------------------------------------------------
# Session management — reuses AIOpsLab's Session class
# ---------------------------------------------------------------------------


class AnalysisSession:
    """Lightweight analysis session wrapping AIOpsLab's ``Session``.

    When AIOpsLab is available, delegates to ``aiopslab.session.Session``
    for history tracking and serialisation.  Otherwise falls back to a
    plain dictionary.
    """

    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())
        self._start_time = time.time()
        self._aiops_session = None

        if _HAS_AIOPSLAB:
            self._aiops_session = AIOpsSession()
            self.session_id = str(self._aiops_session.session_id)
            logger.info("Using AIOpsLab Session for tracking (id=%s)", self.session_id)
        else:
            logger.info("Using lightweight session (id=%s)", self.session_id)

    def add(self, role: str, content: str) -> None:
        """Record a step in the session history."""
        if self._aiops_session is not None:
            self._aiops_session.add({"role": role, "content": content})

    def start(self) -> None:
        """Mark session start."""
        self._start_time = time.time()
        if self._aiops_session is not None:
            self._aiops_session.start()

    def end(self) -> None:
        """Mark session end."""
        if self._aiops_session is not None:
            self._aiops_session.end()

    def to_dict(self) -> dict:
        """Return session metadata as a dictionary."""
        if self._aiops_session is not None:
            return self._aiops_session.to_dict()
        return {
            "session_id": self.session_id,
            "start_time": self._start_time,
            "status": "completed",
        }


# ---------------------------------------------------------------------------
# Response parsing — reuses AIOpsLab's ResponseParser
# ---------------------------------------------------------------------------

_response_parser = None
if _HAS_AIOPSLAB:
    _response_parser = AIOpsResponseParser()


def parse_agent_response(response: str) -> dict | None:
    """Parse a structured agent response using AIOpsLab's ``ResponseParser``.

    This enables future integration with AI agents that emit structured
    action calls (e.g. requesting pipeline analysis).

    Args:
        response: Raw response string with a code-block action call.

    Returns:
        Parsed dict with ``api_name``, ``args``, ``kwargs``, or *None*
        if AIOpsLab is unavailable.
    """
    if _response_parser is None:
        logger.warning("AIOpsLab ResponseParser not available")
        return None
    try:
        return _response_parser.parse(response)
    except Exception as e:
        logger.error("Failed to parse agent response: %s", e)
        return None


# ---------------------------------------------------------------------------
# Dagger integration
# ---------------------------------------------------------------------------


async def simulate_with_dagger(yaml_path: str | Path) -> dict:
    """Run pipeline simulation using the local Dagger Python SDK.

    Connects to the Dagger engine and creates a container per job
    in the pipeline to simulate execution.

    Requires a running Dagger engine — see ``dagger/install.sh``.

    Args:
        yaml_path: Path to ``.gitlab-ci.yml``.

    Returns:
        Dict with simulation results or a stub message.
    """
    if not _HAS_DAGGER:
        return {
            "status": "unavailable",
            "message": (
                "Dagger Python SDK not importable. Ensure "
                "dagger/sdk/python/src/ is in the repository. "
                "The local analysis pipeline is used instead."
            ),
        }

    config = parse_gitlab_ci(yaml_path)
    dag = build_dag(config)

    try:
        async with dagger_sdk.connect() as client:
            results = {}
            for job_name, job_info in dag.jobs.items():
                image = job_info.image or "alpine:3.18"
                container = client.container().from_(image)

                # Execute each script line in the container
                for line in job_info.script:
                    container = container.with_exec(["sh", "-c", line])

                # Capture stdout
                output = await container.stdout()
                results[job_name] = {
                    "status": "success",
                    "output_preview": output[:500] if output else "",
                }

            return {"status": "completed", "jobs": results}

    except Exception as e:
        logger.error("Dagger simulation failed: %s", e)
        return {
            "status": "error",
            "message": str(e),
            "hint": (
                "Ensure the Dagger engine is running. Install with: cd dagger && ./install.sh"
            ),
        }


# ---------------------------------------------------------------------------
# Main orchestrated pipeline
# ---------------------------------------------------------------------------


def create_session() -> AnalysisSession:
    """Create an analysis session using AIOpsLab's Session when available."""
    return AnalysisSession()


def run_analysis(
    yaml_path: str | Path | None = None,
    yaml_content: str | None = None,
    country: str = "USA",
    output_dir: str | Path | None = None,
) -> PipelineResult:
    """Run the full GreenPipeline analysis pipeline.

    Orchestration flow (modelled after AIOpsLab's ``Orchestrator``):
        1. Create session → ``AnalysisSession`` (wraps AIOpsLab ``Session``)
        2. Parse YAML → ``PipelineDAG``
        3. Analyse pipeline → ``OptimizationReport``
        4. Estimate carbon → ``CarbonReport`` (via local CodeCarbon)
        5. Generate visualisation → figure path

    Args:
        yaml_path: Path to a ``.gitlab-ci.yml`` file.
        yaml_content: Raw YAML string (takes priority over ``yaml_path``).
        country: ISO country code for carbon intensity.
        output_dir: Directory for saving visualisation output.

    Returns:
        :class:`PipelineResult` with all analysis outputs.
    """
    session = create_session()
    session.start()
    session.add("system", "GreenPipeline analysis started")
    logger.info("Starting analysis session %s", session.session_id)

    # 1. Parse
    if yaml_content:
        import tempfile

        tmp = Path(tempfile.mktemp(suffix=".yml"))
        tmp.write_text(yaml_content, encoding="utf-8")
        config = parse_gitlab_ci(tmp)
        tmp.unlink(missing_ok=True)
    elif yaml_path:
        config = parse_gitlab_ci(yaml_path)
    else:
        sample = _SAMPLES_DIR / "sample_pipeline.yml"
        config = parse_gitlab_ci(sample)

    dag = build_dag(config)
    session.add("env", f"Parsed pipeline: {len(dag.jobs)} jobs, {len(dag.stages)} stages")
    logger.info(
        "Parsed pipeline: %d jobs, %d stages, %.1f min critical path",
        len(dag.jobs),
        len(dag.stages),
        dag.critical_path_min,
    )

    # 2. Optimize
    report = analyze_pipeline(dag)
    session.add(
        "assistant",
        f"Found {len(report.suggestions)} optimizations, saving {report.total_saving_min:.1f} min",
    )
    logger.info(
        "Optimization: %d suggestions, %.1f min saving",
        len(report.suggestions),
        report.total_saving_min,
    )

    # 3. Carbon (uses local CodeCarbon)
    carbon = estimate_emissions(
        dag,
        optimized_runtime_min=report.optimized_runtime_min,
        country=country,
    )
    session.add(
        "env",
        f"Carbon: current={carbon.current_emissions_kg:.4f} kg, "
        f"optimized={carbon.optimized_emissions_kg:.4f} kg, "
        f"reduction={carbon.reduction_pct:.1f}%",
    )
    logger.info(
        "Carbon: current=%.4f kg, optimized=%.4f kg, reduction=%.1f%%",
        carbon.current_emissions_kg,
        carbon.optimized_emissions_kg,
        carbon.reduction_pct,
    )

    # 4. Visualize
    fig = draw_pipeline_dag(dag)
    viz_path: str | None = None
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        viz_path = export_dag_image(fig, out / "pipeline_dag.png")

    # 5. Generate reasoning explanations and efficiency score
    from greenpipeline.agents.reasoning_agent import generate_reasoning

    reasoning = generate_reasoning(report)
    session.add("assistant", f"Pipeline Efficiency Score: {reasoning.efficiency_score}/100")
    logger.info("Pipeline Efficiency Score: %d", reasoning.efficiency_score)

    # 6. Generate optimized YAML patch
    optimized_yaml = generate_patch(config, dag, report)
    session.add(
        "assistant",
        "Generated optimized YAML patch with suggested improvements",
    )
    logger.info("Generated optimized YAML patch")

    session.end()

    return PipelineResult(
        dag=dag,
        optimization=report,
        carbon=carbon,
        reasoning=reasoning,
        visualization_path=viz_path,
        session_id=session.session_id,
        optimized_yaml=optimized_yaml,
    )


def main() -> None:
    """CLI entrypoint for `greenpipeline` command."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="GreenPipeline AI — pipeline analyser")
    parser.add_argument("yaml", nargs="?", help="Path to .gitlab-ci.yml")
    parser.add_argument("--country", default="USA", help="ISO country code")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    result = run_analysis(yaml_path=args.yaml, country=args.country, output_dir=args.output_dir)

    from greenpipeline.gitlab_comment import generate_gitlab_comment_with_patch

    comment = generate_gitlab_comment_with_patch(result)
    print(comment)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
