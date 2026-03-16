# GreenPipeline AI

You are a multi-agent development team building **GreenPipeline AI**.

Your task is to implement a system that analyzes CI/CD pipelines, detects inefficiencies, and estimates carbon footprint reductions.

The system should integrate existing tools in this repository.

---

# Project Overview

GreenPipeline AI analyzes GitLab CI/CD pipelines and provides:

1. Pipeline structure visualization
2. Optimization recommendations
3. Carbon footprint estimation
4. A demonstration dashboard

The project focuses on **CI/CD sustainability optimization**.

---

# System Architecture

The architecture follows a modular pipeline:

GitLab CI YAML  
→ Pipeline Parser  
→ Pipeline DAG  
→ Optimization Engine  
→ Carbon Estimator  
→ Visualization Dashboard  

Agents collaborate to implement each stage.

---

# Repository Context

This repository contains several subsystems:

AIOpsLab  
Framework for building and evaluating AI agents.

dagger  
Programmable CI/CD engine used for pipeline simulation.

codecarbon  
Library used to measure energy usage and carbon emissions.

pipeline-graph-view-plugin  
Reference implementation for pipeline DAG visualization.

sci-guide  
Documentation for Software Carbon Intensity (SCI) methodology.

SWE-bench  
Reference benchmark for AI software engineering agents.

Agents should **reuse existing components whenever possible** instead of rewriting them.

---

# Target System Modules

The final implementation should contain a new module:

```
greenpipeline/
```

Expected structure:

```
greenpipeline
├── parser.py
├── optimizer.py
├── carbon.py
├── visualizer.py
├── pipeline_runner.py
└── dashboard.py
```

Descriptions:

parser.py  
Parses `.gitlab-ci.yml` and builds pipeline DAG.

optimizer.py  
Analyzes pipeline graph and suggests optimizations.

carbon.py  
Calculates carbon emissions using CodeCarbon.

visualizer.py  
Creates pipeline graphs using NetworkX.

pipeline_runner.py  
Runs pipeline simulations using Dagger.

dashboard.py  
Streamlit dashboard for demonstration.

---

# Agent Responsibilities

Agents must divide work into clear roles.

Architecture Agent  
Design system modules and define file structure.

Pipeline Analysis Agent  
Parse CI/CD pipelines and build DAG.

Optimization Agent  
Detect inefficiencies and suggest improvements.

Carbon Intelligence Agent  
Estimate emissions using CodeCarbon.

Integration Agent  
Integrate all modules with AIOpsLab and Dagger.

Demo Agent  
Build Streamlit dashboard and visualization.

Agents should **work asynchronously and independently**.

---

# Implementation Workflow

Follow this sequence:

1. Parse `.gitlab-ci.yml`
2. Construct pipeline DAG
3. Analyze pipeline inefficiencies
4. Suggest optimization strategies
5. Estimate carbon emissions
6. Visualize pipeline structure
7. Display results in dashboard

---

# Coding Standards

Language: Python 3.11

Guidelines:

- Write modular Python files
- Prefer async when interacting with AIOpsLab
- Avoid monolithic scripts
- Separate logic from visualization
- Use type hints where possible

Preferred libraries:

PyYAML  
NetworkX  
CodeCarbon  
Streamlit  

---

# Runtime Constraints

This project should run **locally without heavy infrastructure**.

Avoid:

- full Kubernetes deployments
- large cloud dependencies

Focus on:

- lightweight pipeline simulation
- minimal hackathon prototype

---

# Output Expectations

The system should produce:

Pipeline analysis report

Example:

Pipeline runtime: 18 minutes  
Optimized runtime: 11 minutes  

Suggestions:

- Parallelize test and lint stages  
- Enable dependency caching  
- Remove redundant docker build  

Carbon footprint:

Current: 1.8 kg CO2  
Optimized: 0.9 kg CO2  

---

# Demo Requirements

The final demo must include:

1. Pipeline DAG visualization
2. Optimization recommendations
3. Carbon impact comparison
4. Interactive dashboard

Demo runtime should be under **30 seconds**.

---

# Agent Collaboration Rules

Agents should:

- reuse existing modules
- avoid rewriting repository components
- keep implementations simple
- prioritize working prototype over perfect architecture