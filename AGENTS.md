# GreenPipeline AI Agents

## Purpose

GreenPipeline AI analyzes GitLab CI/CD pipelines and suggests optimizations that improve efficiency and reduce carbon emissions.

## Agents

### Pipeline Analyzer

Parses `.gitlab-ci.yml` files and constructs a directed acyclic graph (DAG) of pipeline jobs and dependencies.

### Optimization Agent

Detects inefficiencies such as:

* redundant builds
* sequential jobs that could run in parallel
* missing dependency caching
* inefficient container builds

### Reasoning Agent

Explains why pipeline inefficiencies occur and how suggested fixes improve runtime and sustainability.

### Carbon Estimator

Estimates carbon footprint of CI/CD pipelines using the Software Carbon Intensity (SCI) model.

### Patch Generator

Produces an optimized `.gitlab-ci.yml` configuration that developers can apply.

## Trigger

Agents run when the user mentions:

@greenpipeline

in a merge request or issue discussion.

## Expected Output

The agent produces:

* pipeline analysis
* optimization suggestions
* carbon impact estimate
* optimized pipeline patch
