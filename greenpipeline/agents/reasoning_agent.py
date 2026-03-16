"""Pipeline Reasoning Agent — Explains CI/CD inefficiencies in natural language.

Part of the GreenPipeline AI multi-agent architecture.
"""

from __future__ import annotations

from greenpipeline import OptimizationReport, ReasoningReport


def calculate_efficiency_score(
    report: OptimizationReport,
) -> tuple[int, dict[str, int]]:
    """Calculate a heuristic Pipeline Efficiency Score out of 100.

    Deducts points based on the number and type of inefficiencies found.
    - Missing cache: -10 points each (max -30)
    - Sequential bottlenecks: -15 points each (max -45)
    - Redundant jobs: -20 points each (max -40)
    """
    score = 100
    breakdown = {"Parallelization": 50, "Caching": 30, "Redundancy": 20}

    for suggestion in report.suggestions:
        if suggestion.category == "caching":
            deduction = min(10, breakdown["Caching"])
            breakdown["Caching"] -= deduction
            score -= deduction
        elif suggestion.category == "parallelization":
            deduction = min(15, breakdown["Parallelization"])
            breakdown["Parallelization"] -= deduction
            score -= deduction
        elif suggestion.category == "redundancy":
            deduction = min(20, breakdown["Redundancy"])
            breakdown["Redundancy"] -= deduction
            score -= deduction

    return max(0, score), breakdown


def generate_reasoning(report: OptimizationReport) -> ReasoningReport:
    """Generate conversational AI explanations for pipeline inefficiencies."""
    explanations = []

    for suggestion in report.suggestions:
        if suggestion.category == "caching":
            jobs_str = ", ".join(suggestion.affected_jobs)
            explanations.append(
                f"**Missing Dependency Cache**: Jobs `{jobs_str}` are installing "
                "dependencies from scratch on each pipeline run. Without caching, "
                "packages must be downloaded again over the network, which "
                "increases both runtime and cloud compute energy usage."
            )

        elif suggestion.category == "parallelization":
            jobs_str = ", ".join(suggestion.affected_jobs)
            explanations.append(
                f"**Sequential Bottleneck**: Jobs `{jobs_str}` are running sequentially "
                "due to implicit stage ordering. Because they don't depend on each "
                "other, using the `needs:` keyword allows them to run concurrently "
                "in parallel, significantly reducing overall pipeline wall-clock time."
            )

        elif suggestion.category == "redundancy":
            jobs_str = ", ".join(suggestion.affected_jobs)
            explanations.append(
                f"**Job Redundancy**: Jobs `{jobs_str}` execute identical scripts. "
                "Running duplicate workloads wastes compute resources entirely. "
                "Consider consolidating them into a single job or using a shared "
                "abstract template."
            )

    score, breakdown = calculate_efficiency_score(report)

    if not explanations:
        explanations.append(
            "Your pipeline is highly optimized! Dependencies are properly cached "
            "and jobs run with maximum safe concurrency."
        )

    return ReasoningReport(
        explanations=explanations,
        efficiency_score=score,
        score_breakdown=breakdown,
    )
