# 🌿 GreenPipeline AI

## 🚀 The Compiler for CI/CD Pipelines

GreenPipeline AI transforms inefficient YAML CI/CD pipelines into optimised execution graphs.

> ⚡ **60% faster pipelines**
> 🌍 **60% lower carbon footprint**
> ✅ **Validated before deployment**

---

## 💡 What it does

CI pipelines today are written manually, which wastes time by duplicating work.

GreenPipeline treats your pipeline as a **Directed Acyclic Graph (DAG)** and automatically:

* 🔁 **Eliminates redundant work** (e.g., repeated `npm ci`)
* ⚡ **Maximizes parallel execution**
* 🌿 **Reduces compute and carbon usage**
* 🧪 **Validates the optimised pipeline using containers**

---

## 🔥 Key Features

### 🧠 Dependency Hoisting

Detects repeated install steps and moves them into a single shared job:

```yaml
# Before (repeated 4x)
- npm ci

# After (once)
prepare_dependencies:
  script: npm ci
```

### ⚡ DAG Optimisation

Uses graph algorithms to:

* remove unnecessary dependencies
* unlock parallel execution
* minimise total runtime

### 🧪 Execution Validation (Dagger)

Runs the optimised pipeline in **real containers** before deployment:

> "Not just optimised — proven to work."

### 🌍 Carbon Intelligence

Powered by CodeCarbon + SCI:

* measures real CO₂ savings
* accounts for regional energy grids

---

## 🧠 How it works (Compiler Architecture)

GreenPipeline is a **5-pass optimizer**:

1. 🔍 Detect redundant patterns
2. 🔧 Rewrite the execution graph
3. ✂️ Remove redundant dependencies
4. ⏱ Recompute critical path
5. 🧾 Generate optimised YAML

---

## ⚡ Example Impact

| Metric             | Before    | After         |
| ------------------ | --------- | ------------- |
| Runtime            | 3.0 min   | **1.2 min**   |
| Redundant installs | 4         | **1**         |
| Carbon footprint   | 0.0012 kg | **0.0005 kg** |

---

## 🛠️ Quick Start

```bash
git clone https://github.com/rrsathe/greenpipeline-ai.git --recursive
cd greenpipeline-ai
uv venv && source .venv/bin/activate
uv pip install -e .
```

Run optimisation:

```bash
uv run python greenpipeline/pipeline_runner.py path/to/.gitlab-ci.yml
```

Launch the interactive dashboard:

```bash
uv run streamlit run greenpipeline/dashboard.py
```

---

## 🏗️ Built With

* **NetworkX** — graph optimization
* **Dagger** — execution validation
* **CodeCarbon** — emissions tracking
* **AIOpsLab** — session intelligence
* **Streamlit** — visualization

---

## 🏆 Why this matters

> CI/CD today is written manually.
> GreenPipeline makes it **self-optimizing.**

---

**Built for the GitLab AI Challenge 2026** 🚀
