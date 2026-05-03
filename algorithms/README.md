# Algorithms

This directory contains the core algorithmic primitives that power decision‑making, optimisation, and learning across the Sovereign Architecture platform.

## What is an Algorithm (in this context)?

An algorithm module provides **pure, stateless functions** that agents call as tools. Each function:

- Takes well‑typed inputs.
- Returns a deterministic result (or a probability distribution when the algorithm is inherently stochastic, using an explicit random seed).
- Has **no side effects** — no I/O, no global state mutation.

## Directory Structure

```
algorithms/
├── README.md            ← this file
└── core_algorithm.py    ← base interface + example algorithm implementations
```

Add new algorithm modules alongside `core_algorithm.py`, grouped by domain (e.g. `search.py`, `optimisation.py`, `classification.py`).

## Adding a New Algorithm

1. Create a new file, e.g. `algorithms/ranking.py`.
2. Define a clear function signature with type annotations.
3. Write a docstring explaining inputs, outputs, complexity, and any assumptions.
4. Add unit tests in `algorithms/tests/` covering normal cases, edge cases, and expected failures.

## Guidelines

- **No I/O** inside algorithm functions. If data must be fetched first, do it in the agent and pass the data as a parameter.
- **Explicit random seeds** for any non‑deterministic algorithm to keep tests reproducible.
- **Document complexity** (time and space) in the function docstring.
- **Prefer standard library** implementations over third‑party dependencies unless the performance benefit is clearly justified.

## Testing

Algorithm tests are the most important tests in the platform because algorithms underpin every agent decision. Aim for 100 % branch coverage. Place tests in `algorithms/tests/`.
