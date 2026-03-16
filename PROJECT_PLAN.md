# GreenPipeline AI - Project Plan

This plan is optimized for Antigravity planning mode.

## Mission

Build a lightweight, local-first hackathon prototype that:
- parses GitLab CI pipelines,
- identifies optimization opportunities,
- estimates carbon impact,
- and presents results in a fast demo dashboard.

## Scope

In scope:
- `.gitlab-ci.yml` parsing into DAG
- optimization recommendation engine
- carbon estimation with CodeCarbon
- local simulation hook via Dagger
- dashboard demo under 30 seconds

Out of scope:
- Kubernetes deployment
- cloud-only infrastructure
- full production hardening

## Target Deliverables

- `greenpipeline/parser.py`
- `greenpipeline/optimizer.py`
- `greenpipeline/carbon.py`
- `greenpipeline/visualizer.py`
- `greenpipeline/pipeline_runner.py`
- `greenpipeline/dashboard.py`
- `greenpipeline/__init__.py`
- simple sample input pipeline for demo
- one end-to-end demo script or run flow

## Agent Team and Ownership

- **architecture-agent**: module boundaries, interfaces, sequencing
- **pipeline-analysis-agent**: parser and DAG extraction
- **optimization-agent**: inefficiency detection and recommendations
- **carbon-intelligence-agent**: emissions tracking and comparison
- **integration-agent**: wiring modules with AIOpsLab + Dagger hooks
- **demo-agent**: dashboard assembly and presentation flow

## Task Groups

## TG1 - Architecture and Interfaces
Owner: architecture-agent

Tasks:
1. Define data contracts shared between modules.
2. Define DAG representation and metadata schema.
3. Confirm final folder structure under `greenpipeline/`.

Acceptance criteria:
- clear function signatures for each module
- no overlapping responsibilities
- implementation order documented

## TG2 - Pipeline Parsing and DAG Construction
Owner: pipeline-analysis-agent

Tasks:
1. Parse `.gitlab-ci.yml` safely.
2. Extract stages, jobs, dependencies, parallel behavior.
3. Build DAG plus metadata output.

Acceptance criteria:
- parser handles valid GitLab CI examples
- DAG output includes jobs and dependency edges
- parser does not mutate input files

## TG3 - Optimization Engine
Owner: optimization-agent

Tasks:
1. Detect sequential bottlenecks.
2. Detect redundant jobs and missing caching.
3. Produce optimization suggestions with estimated runtime impact.

Acceptance criteria:
- report format is human-readable
- suggestions map to concrete pipeline sections
- original pipeline remains unchanged

## TG4 - Carbon Estimation
Owner: carbon-intelligence-agent

Tasks:
1. Add CodeCarbon-backed measurement wrapper.
2. Estimate current vs optimized run impact.
3. Output carbon comparison summary.

Acceptance criteria:
- reports include current and optimized emissions
- method is reproducible locally
- output integrates with dashboard inputs

## TG5 - Integration and Execution Flow
Owner: integration-agent

Tasks:
1. Add Dagger-based local runner hook.
2. Wire parser -> optimizer -> carbon -> visualizer pipeline.
3. Expose one orchestrated entrypoint for demo flow.

Acceptance criteria:
- full pipeline can run end-to-end locally
- integration reuses existing repo capabilities
- minimal additional dependencies

## TG6 - Demo Dashboard
Owner: demo-agent

Tasks:
1. Build Streamlit dashboard layout.
2. Show DAG visualization.
3. Show optimization and carbon delta panels.
4. Keep run under 30 seconds for sample pipeline.

Acceptance criteria:
- dashboard presents all four required outputs
- startup and run are fast enough for hackathon demo
- UX remains minimal and clear

## Execution Order

Recommended order:
1. TG1
2. TG2 + TG3 (parallel after interfaces are stable)
3. TG4 (can start after TG2 contracts)
4. TG5
5. TG6

## Coordination Rules

- Prefer existing repository modules over rebuilding from scratch.
- Keep each commit focused to one task group where possible.
- Use small, testable functions and explicit return objects.
- Use Python 3.11 and type hints where practical.

## Risks and Mitigations

Risk: parser fails on unusual pipeline syntax.
Mitigation: defensive parsing + fallback metadata capture.

Risk: carbon values vary by machine.
Mitigation: emphasize comparative deltas, not absolute guarantees.

Risk: demo latency exceeds 30 seconds.
Mitigation: use small sample pipeline and avoid heavy runtime setup.

## Definition of Done

- End-to-end run from pipeline input to dashboard output works locally.
- Optimization and carbon reports are visible in dashboard.
- Architecture remains modular with no duplicated subsystem rewrites.
- Demo path is reliable for hackathon presentation.
