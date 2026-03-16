---
name: pipeline-parser
description: Parses GitLab CI/CD pipeline YAML files (.gitlab-ci.yml) and converts them into structured pipeline graphs (DAGs) for analysis and optimization.
---

# Pipeline Parser Skill

This skill extracts the structure of CI/CD pipelines from `.gitlab-ci.yml` files and converts them into a graph representation.

The resulting pipeline graph can be used for:
- pipeline optimization
- visualization
- execution planning
- carbon footprint estimation

## When to Use This Skill

Use this skill when:

- analyzing GitLab CI pipelines
- building pipeline visualization
- detecting inefficiencies in CI/CD workflows
- constructing DAGs for pipeline execution
- preparing pipelines for AI optimization

## Pipeline Concepts

GitLab pipelines consist of:

- **Stages**
- **Jobs**
- **Dependencies**
- **Parallel tasks**
- **Artifacts**
- **Caches**

Example pipeline:

```yaml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script: make build

test:
  stage: test
  script: make test
```

## Output Format

The pipeline should be converted into a **Directed Acyclic Graph (DAG)**.

Example:

```
build → test → deploy
```

## Implementation Guidelines

Use Python.

Preferred libraries:

* `pyyaml`
* `networkx`

Example structure:

```python
import yaml
import networkx as nx

def parse_pipeline(path):

    with open(path) as f:
        config = yaml.safe_load(f)

    graph = nx.DiGraph()

    stages = config.get("stages", [])

    for stage in stages:
        graph.add_node(stage)

    for i in range(len(stages)-1):
        graph.add_edge(stages[i], stages[i+1])

    return graph
```

## Best Practices

* Validate YAML before parsing
* Preserve job dependencies
* Detect parallel jobs
* Store job metadata
* Keep graph representation reusable