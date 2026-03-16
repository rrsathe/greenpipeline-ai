---
name: hackathon-demo-builder
description: Builds a minimal working demo for hackathon presentations with pipeline analysis, optimization suggestions, and carbon metrics.
---

# Hackathon Demo Builder

This skill builds a **minimal prototype for demonstration**.

Focus on:

- clear visualization
- simple pipeline analysis
- carbon impact estimation

Avoid heavy infrastructure such as full Kubernetes clusters.

## Demo Flow

Step 1

Load pipeline

```
.gitlab-ci.yml
```

Step 2

Generate DAG graph.

Step 3

Run optimization analysis.

Step 4

Estimate carbon footprint.

Step 5

Display dashboard.

## Recommended Stack

```
Python
NetworkX
Streamlit
CodeCarbon
```

## Demo Output

```
Pipeline runtime: 18 min
Optimized runtime: 11 min

Carbon reduction: 39%
```

## Best Practices

- keep demo under 30 seconds
- show visual improvements
- focus on impact