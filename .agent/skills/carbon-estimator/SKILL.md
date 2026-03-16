---
name: carbon-estimator
description: Estimates energy usage and carbon emissions of CI/CD pipelines using CodeCarbon.
---

# Carbon Estimator Skill

This skill estimates the **carbon footprint of pipeline executions**.

It uses the **CodeCarbon** library.

## When to Use

Use when:

- measuring CI/CD environmental impact
- comparing pipeline optimizations
- estimating energy consumption
- reporting sustainability metrics

## SCI Concept

Software Carbon Intensity:

```
SCI = carbon emissions per unit of computation
```

For pipelines:

```
SCI = carbon per pipeline execution
```

## Implementation

```python
from codecarbon import EmissionsTracker

tracker = EmissionsTracker()
tracker.start()

# run pipeline task

emissions = tracker.stop()
```

Output:

```
0.00021 kg CO2
```

## Example Output

```
Pipeline carbon footprint

Current pipeline: 1.8 kg CO2
Optimized pipeline: 0.9 kg CO2

Reduction: 50%
```

## Best Practices

* measure runtime
* measure CPU usage
* estimate per job emissions