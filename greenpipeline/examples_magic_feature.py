"""Interactive demo for GreenPipeline AI's Magic Feature.

To run:
    python -c "import sys; sys.path.insert(0, '.'); \\
        exec(open('greenpipeline/examples_magic_feature.py').read())"
"""

from __future__ import annotations

import json
from pathlib import Path

from greenpipeline.gitlab_comment import generate_gitlab_comment_with_patch
from greenpipeline.pipeline_runner import run_analysis


def main():
    print("=" * 60)
    print(" 🌿 GreenPipeline AI — Multi-Agent Flow Demo")
    print("=" * 60)
    print("\nRunning analysis on sample pipeline...\n")

    # Run full analysis
    try:
        base_dir = Path(__file__).parent
    except NameError:
        base_dir = Path("greenpipeline")

    sample_path = base_dir / "samples" / "sample_pipeline.yml"
    result = run_analysis(yaml_path=sample_path)

    # 1. Pipeline Analysis Summary
    print("\n" + "=" * 60)
    print(" 1. Pipeline Analysis Summary")
    print("=" * 60)
    print(f"Jobs analyzed: {len(result.dag.jobs)}")
    print(f"Current Runtime: {result.optimization.original_runtime_min:.1f} min")
    print(f"Optimized Runtime: {result.optimization.optimized_runtime_min:.1f} min")
    print(f"Carbon Reduction: {result.carbon.reduction_pct:.1f}%")

    if result.reasoning:
        print(f"Efficiency Score: {result.reasoning.efficiency_score}/100")
        for i, text in enumerate(result.reasoning.explanations, 1):
            print(f"\n  [Reasoning {i}]: {text}")

    # 2. Optimized YAML Patch
    print("\n" + "=" * 60)
    print(" 2. Optimized YAML Patch")
    print("=" * 60)
    print(result.optimized_yaml)

    # 3. GitLab MR Comment
    print("\n" + "=" * 60)
    print(" 3. GitLab MR Comment (Ready to Post)")
    print("=" * 60)
    comment = generate_gitlab_comment_with_patch(result)
    print(comment)

    # 4. JSON Export Metrics
    print("\n" + "=" * 60)
    print(" 4. JSON Metrics Export")
    print("=" * 60)
    metrics = {
        "efficiency_score": result.reasoning.efficiency_score if result.reasoning else 0,
        "runtime_min": result.optimization.original_runtime_min,
        "optimized_runtime_min": result.optimization.optimized_runtime_min,
        "saving_min": result.optimization.total_saving_min,
        "emissions_kg": result.carbon.current_emissions_kg,
        "optimized_emissions_kg": result.carbon.optimized_emissions_kg,
        "reduction_pct": result.carbon.reduction_pct,
        "session_id": result.session_id,
    }
    print(json.dumps(metrics, indent=2))

    # 5. Next Steps Guide
    print("\n" + "=" * 60)
    print(" 5. Next Steps")
    print("=" * 60)
    print("To apply this patch:")
    print("  1. Copy the YAML patch above into your .gitlab-ci.yml")
    print("  2. Review the changes using `git diff`")
    print("  3. Commit and push to trigger your optimized pipeline!")


if __name__ == "__main__":
    main()
