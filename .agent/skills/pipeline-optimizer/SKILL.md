---
name: pipeline-optimizer
description: Detects inefficiencies in CI/CD pipelines and suggests optimizations such as parallelization, caching, job deduplication, and dependency reduction.
---

# Pipeline Optimizer Skill

This skill analyzes CI/CD pipelines and suggests improvements to:

- reduce runtime
- reduce compute cost
- reduce carbon emissions
- improve pipeline throughput

## When to Use This Skill

Use when:

- analyzing CI/CD performance
- optimizing GitLab pipelines
- reducing redundant jobs
- identifying sequential bottlenecks
- improving pipeline speed

## Common CI/CD Inefficiencies

### Sequential Jobs

Jobs that could run in parallel but do not.

Example:

```
build → test → lint

```

Better:

```

build
├─ test
└─ lint

```

---

### Redundant Jobs

Multiple builds for the same artifact.

Example:

```

build
build-docker
build-package

```

Better:

```

build
├─ docker
└─ package

```

---

### Missing Caching

Dependency installation repeated every run.

Example fix:

```yaml
cache:
  paths:
    - node_modules/
```

---

### Inefficient Docker Builds

Repeated base image builds.

Use:

```
docker layer caching
```

---

## Optimization Strategies

1. Job Parallelization
2. Dependency Caching
3. Artifact Reuse
4. Stage Merging
5. Conditional Execution

---

## Output Format

Return suggestions like:

```
Pipeline Analysis

Current runtime: 18 minutes

Suggestions:

• Parallelize test and lint stages
• Enable dependency caching
• Remove redundant build step

Estimated runtime: 11 minutes
```

---

## Best Practices

* Never modify original pipeline automatically
* Provide suggested YAML changes
* Provide expected runtime improvements
