---
name: aiopslab-integration
description: Integrates custom AI agents with the AIOpsLab orchestration framework.
---

# AIOpsLab Integration Skill

This skill integrates AI agents into AIOpsLab.

## When to Use

Use when:

- creating new AIOps agents
- registering agents with the orchestrator
- running benchmark problems

## Agent Requirements

Agents must implement:

```python
async def get_action(self, state: str) -> str
```

Example:

```python
class PipelineAgent:

    async def get_action(self, state):

        if "slow pipeline" in state:
            return "suggest_parallelization"
```

## Register Agent

```python
from aiopslab.orchestrator import Orchestrator

agent = PipelineAgent()
orch = Orchestrator()

orch.register_agent(agent)
```

---

## Best Practices

* keep agents stateless
* use async functions
* return structured actions