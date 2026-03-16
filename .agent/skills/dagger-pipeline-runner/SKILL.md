---
name: dagger-pipeline-runner
description: Executes CI/CD pipelines using the Dagger engine for local pipeline simulation and runtime analysis.
---

# Dagger Pipeline Runner Skill

This skill runs CI/CD pipelines locally using **Dagger**, a programmable CI/CD engine.

This allows agents to:

- simulate pipeline execution
- measure runtime
- test optimizations

## When to Use

Use when:

- executing pipelines locally
- benchmarking pipeline runtime
- validating pipeline changes
- testing optimization strategies

## Why Dagger

Dagger provides:

- containerized pipeline execution
- reproducible builds
- programmatic CI/CD pipelines

## Basic Example

```python
import dagger

async def run_pipeline():

    async with dagger.Connection() as client:

        container = (
            client.container()
            .from_("python:3.11")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["pytest"])
        )

        output = await container.stdout()

        return output
```

## Best Practices

* isolate pipeline jobs in containers
* measure execution time
* capture logs
* capture resource usage