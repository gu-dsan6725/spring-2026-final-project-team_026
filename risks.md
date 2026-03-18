# Risks and Mitigation Plan (Milestone 2)

This document lists key risks discovered so far and how we plan to mitigate them as we build Codapter (AI Tech Debt Forge).

## Product / Scope Risks

- **Risk: Project scope creep (multi-agent + execution + verification is large)**
  - **Impact**: Miss milestones; incomplete demo.
  - **Mitigation**:
    - Keep a strict “vertical slice” roadmap: RAG → planning → 1 safe refactor → verification loop.
    - Define “done” for each milestone (minimum viable capabilities).

- **Risk: Over-reliance on LLM judgement for upgrades**
  - **Impact**: Incorrect changes; broken code; hallucinated package guidance.
  - **Mitigation**:
    - Require evidence from tools/docs: dependency metadata, test outputs, changelogs.
    - Use temperature 0 for deterministic planning drafts.
    - Add citations to retrieved snippets (file paths + extracted context) in agent outputs.

## Data / Ingestion Risks

- **Risk: Sample repo not reproducible**
  - **Observed**: current notebook assumes a local `old-demos/` directory exists.
  - **Impact**: TA cannot run the pipeline; demo fails.
  - **Mitigation**:
    - Provide a scripted way to fetch sample data (e.g., `git clone` into a known path) or include a small curated sample in-repo.
    - Document expected directory structure in README and/or a dedicated “quickstart”.

- **Risk: Parser/filetype detection quality varies by environment**
  - **Observed**: `unstructured` warns when `libmagic` is unavailable.
  - **Impact**: Some files are mis-typed or poorly parsed; retrieval quality degrades.
  - **Mitigation**:
    - Document optional system dependency (`libmagic`) and provide install instructions for macOS/Linux.
    - Add a “fallback loader” path for plain-text loading when rich parsing fails.

- **Risk: Chunking strategy harms code comprehension**
  - **Impact**: splits functions/classes mid-block; retrieval returns incomplete context.
  - **Mitigation**:
    - Evaluate code-aware splitting (e.g., split by file sections, AST, or smaller overlap tuned by filetype).
    - Add retrieval-time “context expansion” (fetch neighboring chunks from same file).

## Model / Provider Risks

- **Risk: Model/provider instability (rate limits, outages, policy changes)**
  - **Impact**: Demo downtime; inconsistent outputs.
  - **Mitigation**:
    - Keep provider-agnostic interface (LiteLLM) and maintain a tested backup model config.
    - Cache embeddings/vector index to reduce repeated calls.

- **Risk: Latency and cost**
  - **Impact**: slow interactive loop; expensive long-context runs.
  - **Mitigation**:
    - Use local embeddings + FAISS (already implemented) to keep retrieval cheap.
    - Add persistent FAISS index on disk; avoid rebuilding each run.
    - Use smaller models for routine steps; reserve larger models for planning/verification when needed.

## Safety / Execution Risks (as we move beyond Milestone 2)

- **Risk: Automated code changes break runtime behavior**
  - **Impact**: regressions; unusable output patches.
  - **Mitigation**:
    - Gate execution behind tests, lint/type checks, and smoke runs.
    - Only allow changes in a sandboxed working tree; always produce a diff for review.
    - Start with narrow transformations (dependency bumps + mechanical refactors) before complex rewrites.

- **Risk: Incomplete or missing tests in legacy repos**
  - **Impact**: hard to verify correctness; false confidence.
  - **Mitigation**:
    - Add lightweight “smoke tests” (import checks, CLI help, basic module execution).
    - Use static analysis (AST, linters) as partial verification.
    - Record uncertainty explicitly in agent outputs (“cannot verify behavior due to missing tests”).

## Evaluation Risks

- **Risk: Hard to measure modernization quality**
  - **Impact**: weak results section for paper; subjective claims.
  - **Mitigation**:
    - Define measurable metrics: build success, test pass rate, number of dependency upgrades, lint error reduction, time-to-fix.
    - Track before/after artifacts (dependency graph, failing/passing runs).

