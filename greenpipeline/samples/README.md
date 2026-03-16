# GreenPipeline Sample Pipelines

This directory contains sample GitLab CI pipelines for testing and demonstrating the GreenPipeline optimization analysis tool.

## Files

### `gitlab_real.yml`
A realistic multi-stage GitLab CI pipeline with common inefficiencies:
- Sequential job execution where parallelization is possible
- Missing caching on dependency installation
- Mix of build, test, security, and deployment stages

**Use case**: Input file for the pipeline parser and optimizer. Demonstrates what an unoptimized pipeline looks like.

**Metrics**:
- Estimated runtime: 8-10 minutes
- 5 jobs across 4 stages
- ~500+ npm packages installed per test job

---

### `gitlab_optimized.yml`
The same pipeline after applying optimization recommendations:
- Explicit caching configuration for all jobs that install dependencies
- Comments indicating parallelization opportunities
- Best practice caching paths for npm and pip

**Use case**: Expected output reference. Shows what the optimizer should recommend.

**Metrics**:
- Estimated runtime: 4-6 minutes (after cache warm-up)
- Same 5 jobs with cache acceleration
- 40-50% faster execution

---

### `OPTIMIZATION_REPORT.md`
Detailed analysis report showing:
- Each optimization finding with time savings estimate
- Explanation of the issue and recommended solution
- Summary table with priority and effort
- Carbon footprint impact analysis
- Multi-week cost savings projection

**Use case**: Reference output for what the GreenPipeline tool should generate. Shows pipeline analysis format for the demo dashboard.

---

## How to Use These Files

### For Pipeline Parser Testing
```python
from greenpipeline.parser import parse_pipeline

dag = parse_pipeline("gitlab_real.yml")
print(dag.nodes())  # Should show: build_app, build_docker, unit_tests, ...
```

### For Optimizer Testing
```python
from greenpipeline.optimizer import analyze_pipeline

result = analyze_pipeline("gitlab_real.yml")
print(result.suggestions)  # Should include caching and parallelization
```

### For Visual Comparison
Compare the two YAMLs side-by-side:
```bash
diff -u gitlab_real.yml gitlab_optimized.yml
```

### For Carbon Estimation
```python
from greenpipeline.carbon import estimate_emissions

current = estimate_emissions("gitlab_real.yml", min_duration=8)
optimized = estimate_emissions("gitlab_optimized.yml", min_duration=5)
print(f"Reduction: {current - optimized} kg CO2")
```

---

## Expected Tool Behavior

When the GreenPipeline tool processes `gitlab_real.yml`, it should:

1. ✅ Parse all 5 jobs and 4 stages correctly
2. ✅ Detect 3 optimization opportunities (parallelization + 3 caching issues)
3. ✅ Suggest adding `cache:` blocks to test jobs
4. ✅ Estimate ~1-4 minute time savings
5. ✅ Calculate ~25% carbon reduction
6. ✅ Output a report similar to `OPTIMIZATION_REPORT.md`

---

## Notes

- These files use realistic but simplified pipeline structure
- Real-world pipelines may have more complexity (artifacts, dependencies, conditions)
- The parser should handle YAML syntax validation
- The optimizer should preserve the original pipeline file
