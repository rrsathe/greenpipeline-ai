"""Pipeline Visualizer — render pipeline DAGs using NetworkX + matplotlib.

Produces stage-coloured graph visualizations with dependency-type edges.
"""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend for server / Streamlit use

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

from greenpipeline import PipelineDAG

logger = logging.getLogger(__name__)

# Stage → colour mapping (extends automatically for unknown stages)
_STAGE_COLOURS: dict[str, str] = {
    "build": "#4A90D9",
    "test": "#50C878",
    "security": "#F5A623",
    "deploy": "#D0021B",
    "lint": "#9B59B6",
    "release": "#E74C3C",
    "review": "#1ABC9C",
    "staging": "#3498DB",
    "production": "#E67E22",
}

_DEFAULT_COLOUR = "#95A5A6"
_EXTRA_PALETTE = [
    "#8E44AD", "#2ECC71", "#E74C3C", "#3498DB",
    "#F39C12", "#1ABC9C", "#D35400", "#2C3E50",
]


def _colour_for_stage(stage: str, seen: dict[str, str]) -> str:
    """Return a consistent colour for a stage name."""
    if stage in _STAGE_COLOURS:
        return _STAGE_COLOURS[stage]
    if stage not in seen:
        idx = len(seen) % len(_EXTRA_PALETTE)
        seen[stage] = _EXTRA_PALETTE[idx]
    return seen[stage]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_dag_layout(dag: PipelineDAG) -> dict[str, tuple[float, float]]:
    """Compute a layered layout grouped by stage.

    Returns a dictionary mapping node name → (x, y) position.
    """
    G = dag.graph
    if not G.nodes:
        return {}

    # Assign layer (x) by stage index, spread jobs (y) within each stage
    stage_buckets: dict[str, list[str]] = {}
    for node in G.nodes:
        stage = G.nodes[node].get("stage", "unknown")
        stage_buckets.setdefault(stage, []).append(node)

    pos: dict[str, tuple[float, float]] = {}
    for stage_idx, stage in enumerate(dag.stages):
        jobs_in_stage = stage_buckets.get(stage, [])
        for job_idx, job_name in enumerate(jobs_in_stage):
            y = -(job_idx - (len(jobs_in_stage) - 1) / 2.0)
            pos[job_name] = (float(stage_idx), y)

    # Handle jobs whose stage wasn't in the stages list
    extra_x = len(dag.stages)
    for stage, jobs in stage_buckets.items():
        if stage not in dag.stages:
            for job_idx, job_name in enumerate(jobs):
                y = -(job_idx - (len(jobs) - 1) / 2.0)
                pos[job_name] = (float(extra_x), y)
            extra_x += 1

    return pos


def draw_pipeline_dag(
    dag: PipelineDAG,
    output_path: str | Path | None = None,
    figsize: tuple[int, int] = (14, 8),
) -> plt.Figure:
    """Render the pipeline DAG as a matplotlib figure.

    Args:
        dag: The pipeline DAG to visualise.
        output_path: If given, save the figure to this path (PNG/SVG).
        figsize: Figure dimensions in inches.

    Returns:
        The matplotlib :class:`~matplotlib.figure.Figure`.
    """
    G = dag.graph
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    if not G.nodes:
        ax.text(0.5, 0.5, "Empty pipeline", ha="center", va="center",
                color="white", fontsize=16, transform=ax.transAxes)
        return fig

    pos = get_dag_layout(dag)
    extra_colours: dict[str, str] = {}

    # Node colours based on stage
    node_colors = [
        _colour_for_stage(G.nodes[n].get("stage", "unknown"), extra_colours)
        for n in G.nodes
    ]

    # Node sizes proportional to estimated runtime
    runtimes = [G.nodes[n].get("estimated_runtime_min", 1.0) for n in G.nodes]
    max_rt = max(runtimes) if runtimes else 1.0
    node_sizes = [800 + (rt / max_rt) * 1200 for rt in runtimes]

    # Draw edges — dashed for needs, solid for stage-order
    needs_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("type") == "needs"]
    stage_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("type") != "needs"]

    nx.draw_networkx_edges(
        G, pos, edgelist=stage_edges, ax=ax,
        edge_color="#555555", alpha=0.6, width=1.5,
        arrows=True, arrowsize=15, style="solid",
        connectionstyle="arc3,rad=0.1",
    )
    nx.draw_networkx_edges(
        G, pos, edgelist=needs_edges, ax=ax,
        edge_color="#AAAAAA", alpha=0.8, width=2.0,
        arrows=True, arrowsize=15, style="dashed",
        connectionstyle="arc3,rad=0.1",
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
        edgecolors="#FFFFFF",
        linewidths=1.5,
    )

    # Labels
    labels = {}
    for n in G.nodes:
        rt = G.nodes[n].get("estimated_runtime_min", 0)
        labels[n] = f"{n}\n({rt:.1f}m)"

    nx.draw_networkx_labels(
        G, pos, labels, ax=ax,
        font_size=7, font_color="white", font_weight="bold",
    )

    # Legend
    all_stages = list(dict.fromkeys(
        G.nodes[n].get("stage", "unknown") for n in G.nodes
    ))
    legend_patches = [
        mpatches.Patch(
            color=_colour_for_stage(s, extra_colours), label=s.capitalize()
        )
        for s in all_stages
    ]
    legend_patches.append(mpatches.Patch(color="#555555", label="Stage order"))
    legend_patches.append(mpatches.Patch(color="#AAAAAA", label="Explicit needs"))
    ax.legend(
        handles=legend_patches, loc="upper left",
        fontsize=8, facecolor="#2D2D44", edgecolor="#555555",
        labelcolor="white",
    )

    ax.set_title(
        "Pipeline DAG",
        fontsize=16, fontweight="bold", color="white", pad=15,
    )
    ax.axis("off")
    fig.tight_layout()

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        logger.info("Saved DAG visualization to %s", output_path)

    return fig


def export_dag_image(fig: plt.Figure, path: str | Path) -> str:
    """Save a matplotlib figure to disk.

    Returns the absolute path of the saved file.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(p), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    return str(p.resolve())


def fig_to_bytes(fig: plt.Figure) -> bytes:
    """Convert a matplotlib figure to PNG bytes (useful for Streamlit)."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()
