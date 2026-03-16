---
name: pipeline-visualizer
description: Visualizes CI/CD pipelines as DAG graphs using NetworkX and interactive dashboards.
---

# Pipeline Visualization Skill

This skill generates visual representations of CI/CD pipelines.

## When to Use

Use when:

- showing pipeline structure
- explaining pipeline inefficiencies
- demonstrating optimizations
- building dashboards

## Visualization Options

### Static Graph

Using:

```
networkx
matplotlib
```

Example:

```python
import networkx as nx
import matplotlib.pyplot as plt

nx.draw(graph, with_labels=True)
plt.show()
```

---

### Interactive Dashboard

Use:

```
Streamlit
```

Example:

```python
import streamlit as st

st.title("Pipeline Graph")
```

---

## Best Practices

* highlight critical paths
* show parallel jobs
* show runtime estimates