"""GreenPipeline AI — Streamlit Dashboard.

Interactive demo dashboard showing:
1. Pipeline DAG visualisation
2. Optimisation recommendations
3. Carbon impact comparison
4. Pipeline summary metrics

Run: ``streamlit run greenpipeline/dashboard.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path for greenpipeline imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st  # noqa: E402

import greenpipeline._paths  # noqa: F401,E402 — activate local repo paths (codecarbon, AIOpsLab, dagger)
from greenpipeline.pipeline_runner import run_analysis  # noqa: E402
from greenpipeline.visualizer import draw_pipeline_dag  # noqa: E402

_SAMPLES_DIR = Path(__file__).parent / "samples"


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GreenPipeline AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    /* Dark premium palette */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }
    .main .block-container { padding-top: 2rem; }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .metric-card h3 {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6ee7b7, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card .label { color: #64748b; font-size: 0.8rem; }

    /* Suggestion cards */
    .suggestion-card {
        background: #1e293b;
        border-left: 4px solid #6ee7b7;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
    }
    .suggestion-card.caching { border-left-color: #f59e0b; }
    .suggestion-card.redundancy { border-left-color: #ef4444; }
    .suggestion-card .category {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #6ee7b7;
        margin-bottom: 0.3rem;
    }
    .suggestion-card.caching .category { color: #f59e0b; }
    .suggestion-card.redundancy .category { color: #ef4444; }

    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #334155;
    }

    /* Carbon comparison */
    .carbon-current {
        color: #f87171;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .carbon-optimized {
        color: #6ee7b7;
        font-size: 1.5rem;
        font-weight: 700;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🌿 GreenPipeline AI")
    st.markdown("*CI/CD Sustainability Analyser*")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Upload `.gitlab-ci.yml`",
        type=["yml", "yaml"],
        help="Upload your GitLab CI pipeline definition",
    )
    use_sample = st.checkbox("Use sample pipeline", value=True)
    country = st.selectbox(
        "Region (carbon intensity)",
        ["USA", "GBR", "DEU", "FRA", "IND", "CHN", "AUS", "CAN", "JPN", "BRA"],
        index=0,
    )

    st.markdown("---")
    run_btn = st.button("🚀 Run Analysis", type="primary", width="stretch")

    st.markdown("---")
    st.markdown(
        "<small style='color:#64748b'>Powered by CodeCarbon · NetworkX · "
        "AIOpsLab patterns</small>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

st.markdown(
    "<h1 style='text-align:center; color:#e2e8f0;'>"
    "🌿 GreenPipeline AI"
    "</h1>"
    "<p style='text-align:center; color:#94a3b8; margin-top:-10px;'>"
    "Analyse · Optimise · Decarbonise your CI/CD pipelines"
    "</p>",
    unsafe_allow_html=True,
)

if run_btn:
    with st.spinner("Analysing pipeline..."):
        # Determine input source
        if uploaded and not use_sample:
            yaml_content = uploaded.read().decode("utf-8")
            result = run_analysis(yaml_content=yaml_content, country=country)
        else:
            result = run_analysis(country=country)

    dag = result.dag
    opt = result.optimization
    carbon = result.carbon

    # ---- Summary metrics ----
    st.markdown(
        '<div class="section-header">📊 Pipeline Summary</div>', unsafe_allow_html=True
    )
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Jobs</h3>
                <div class="value">{len(dag.jobs)}</div>
                <div class="label">pipeline jobs</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Stages</h3>
                <div class="value">{len(dag.stages)}</div>
                <div class="label">pipeline stages</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Critical Path</h3>
                <div class="value">{opt.original_runtime_min:.1f}m</div>
                <div class="label">estimated runtime</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Optimised</h3>
                <div class="value">{opt.optimized_runtime_min:.1f}m</div>
                <div class="label">after optimisation</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ---- DAG Visualization ----
    st.markdown(
        '<div class="section-header">🔗 Pipeline Dependency Graph</div>',
        unsafe_allow_html=True,
    )

    # Display DAG statistics for debugging
    if dag.graph and dag.graph.nodes:
        st.write(
            f"**Nodes:** {len(dag.graph.nodes)} | **Edges:** {len(dag.graph.edges)}"
        )

    # Safety check before rendering
    if dag and dag.graph and len(dag.graph.nodes) > 0:
        fig = draw_pipeline_dag(dag)
        st.pyplot(fig, width="stretch")
    else:
        st.warning(
            "⚠️ Pipeline DAG could not be visualized. Check if pipeline was parsed correctly."
        )

    # ---- Optimization Recommendations ----
    st.markdown(
        '<div class="section-header">⚡ Optimisation Recommendations</div>',
        unsafe_allow_html=True,
    )

    if opt.suggestions:
        for s in opt.suggestions:
            css_class = f"suggestion-card {s.category}"
            st.markdown(
                f"""<div class="{css_class}">
                    <div class="category">{s.category} · ⏱ ~{s.estimated_saving_min:.1f} min saved</div>
                    <div style="color:#e2e8f0; font-size:0.95rem;">{s.description}</div>
                    <div style="color:#64748b; font-size:0.8rem; margin-top:0.3rem;">
                        Affected: {", ".join(s.affected_jobs)}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ No major optimisations detected — pipeline looks efficient!")

    # ---- AI Pipeline Reasoning ----
    st.markdown(
        '<div class="section-header">🧠 AI Pipeline Reasoning</div>',
        unsafe_allow_html=True,
    )

    if result.reasoning:
        score = result.reasoning.efficiency_score

        # Color score
        if score >= 80:
            score_color = "#6ee7b7"  # Green
        elif score >= 50:
            score_color = "#f59e0b"  # Yellow
        else:
            score_color = "#ef4444"  # Red

        c1, c2 = st.columns([1, 3])
        with c1:
            st.markdown(
                f"""<div style="background: linear-gradient(145deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; text-align: center; margin-bottom: 1rem;">
                    <div style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;">Efficiency Score</div>
                    <div style="font-size: 3rem; font-weight: 700; color: {score_color};">{score}</div>
                    <div style="color: #64748b; font-size: 0.8rem; margin-top: 0.5rem;">out of 100</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown(
                '<div style="padding-top: 0.5rem;"></div>', unsafe_allow_html=True
            )
            for explanation in result.reasoning.explanations:
                st.info(explanation, icon="💡")
    else:
        st.info("No AI reasoning available for this pipeline.", icon="ℹ️")

    # ---- Carbon Impact ----
    st.markdown(
        '<div class="section-header">🌍 Carbon Impact Comparison</div>',
        unsafe_allow_html=True,
    )

    cc1, cc2, cc3 = st.columns(3)

    with cc1:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Current Emissions</h3>
                <div class="carbon-current">{carbon.current_emissions_kg:.4f} kg</div>
                <div class="label">CO₂ per run</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with cc2:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Optimised Emissions</h3>
                <div class="carbon-optimized">{carbon.optimized_emissions_kg:.4f} kg</div>
                <div class="label">CO₂ per run</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with cc3:
        st.markdown(
            f"""<div class="metric-card">
                <h3>Reduction</h3>
                <div class="value">{carbon.reduction_pct:.1f}%</div>
                <div class="label">carbon savings</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Yearly impact calculation
    runs_per_day = 100
    yearly_saving_kg = (
        (carbon.current_emissions_kg - carbon.optimized_emissions_kg)
        * runs_per_day
        * 365
    )

    st.metric(
        "Estimated yearly CO₂ saving (100 runs/day)",
        f"{yearly_saving_kg:.2f} kg CO₂",
        delta=f"-{carbon.reduction_pct:.1f}%",
    )

    # Carbon comparison bar chart
    import matplotlib.pyplot as plt

    fig2, ax = plt.subplots(figsize=(8, 3))
    fig2.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    bars = ax.barh(
        ["Optimised", "Current"],
        [carbon.optimized_emissions_kg, carbon.current_emissions_kg],
        color=["#6ee7b7", "#f87171"],
        height=0.5,
        edgecolor="#334155",
    )

    for bar, val in zip(
        bars, [carbon.optimized_emissions_kg, carbon.current_emissions_kg], strict=False
    ):
        ax.text(
            bar.get_width() + 0.0001,
            bar.get_y() + bar.get_height() / 2,
            f" {val:.4f} kg CO₂",
            va="center",
            color="white",
            fontsize=10,
        )

    ax.set_xlabel("kg CO₂", color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#334155")
    ax.spines["left"].set_color("#334155")
    fig2.tight_layout()
    st.pyplot(fig2, width="stretch")

    # ---- Suggested Pipeline Patch ----
    st.markdown(
        '<div class="section-header">🛠 Suggested Pipeline Patch</div>',
        unsafe_allow_html=True,
    )

    if result.optimized_yaml:
        st.markdown(
            "**Apply these changes to your `.gitlab-ci.yml` for immediate improvements:**"
        )
        st.code(result.optimized_yaml, language="yaml")

        # Download button
        st.download_button(
            label="📥 Download Optimized Pipeline",
            data=result.optimized_yaml,
            file_name="gitlab_ci_optimized.yml",
            mime="text/yaml",
            width="stretch",
        )
    else:
        st.info("💡 Optimized YAML patch generation coming soon.")

    # ---- Energy details ----
    with st.expander("📋 Energy Details"):
        st.markdown(f"""
        | Metric | Current | Optimised |
        |--------|---------|-----------|
        | **Energy (kWh)** | {carbon.current_energy_kwh:.6f} | {carbon.optimized_energy_kwh:.6f} |
        | **Emissions (kg CO₂)** | {carbon.current_emissions_kg:.6f} | {carbon.optimized_emissions_kg:.6f} |
        | **Methodology** | {carbon.methodology} | — |
        """)

    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; color:#64748b; font-size:0.8rem;'>"
        f"Session {result.session_id} · GreenPipeline AI v0.1"
        "</p>",
        unsafe_allow_html=True,
    )

else:
    # Landing state
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center; padding:3rem 1rem;">
            <p style="font-size:3rem;">🌿</p>
            <p style="color:#94a3b8; font-size:1.1rem;">
                Upload a <code>.gitlab-ci.yml</code> or use the sample pipeline,<br>
                then click <b>Run Analysis</b> to see optimisation and carbon insights.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
