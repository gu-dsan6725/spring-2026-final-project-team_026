# Codapter Architecture (Milestone 2)

This document captures the **updated system architecture** based on what we have implemented and learned so far (Milestone 2).

## Goal

Codapter is an AI agent system that helps modernize outdated Python codebases by:
- ingesting a target repository as “memory”
- answering diagnostic questions (RAG)
- (next) planning and applying safe, testable upgrades under human oversight

## Current (Milestone 2) Architecture: Working RAG Agent

### High-level flow

```mermaid
flowchart LR
  A[Target repo / directory<br/>e.g., old-demos/] --> B[Ingestion<br/>DirectoryLoader + file globs]
  B --> C[Preprocess / Parse<br/>unstructured + langchain loaders]
  C --> D[Chunking<br/>RecursiveCharacterTextSplitter<br/>1000 chars, overlap 200]
  D --> E[Embeddings<br/>sentence-transformers<br/>all-MiniLM-L6-v2]
  E --> F[Vector Store<br/>FAISS (local)]
  F --> G[Retriever<br/>similarity / MMR]
  G --> H[RAG Chain<br/>retrieve + generate]
  H --> I[LLM via LiteLLM<br/>Groq: llama-3.1-8b-instant]
  I --> J[Answers / Analysis<br/>basic agent capability]
```

### Components (what exists today)

- **LLM access**
  - `langchain_community.chat_models.ChatLiteLLM` via `litellm`
  - Default model: `groq/llama-3.1-8b-instant`
  - Config: environment variable `GROQ_API_KEY` loaded from `.env`

- **Data ingestion**
  - Directory-level loading of code and docs using `DirectoryLoader`
  - Current sample directory: `old-demos/` (local clone of a legacy Python repo)
  - File types: `*.py`, `*.md`, `*.txt`, `*.sh` (as configured in the notebook)

- **Memory / retrieval**
  - Chunking with overlap to preserve local context
  - Local embeddings using `sentence-transformers`
  - FAISS vector store for fast local retrieval
  - Retrieval modes: similarity / MMR

## “Updated Architecture” Learnings (what we changed/confirmed)

These are the concrete takeaways from implementing the first working agent:

- **Start with retrieval-first**: a single RAG agent is the fastest path to a usable baseline for repo understanding and technical-debt discovery.
- **Local embeddings reduce cost + improve iteration speed**: `sentence-transformers` + FAISS keeps indexing local and reproducible.
- **Provider-agnostic LLM layer matters**: LiteLLM lets us swap models (Groq/OpenAI/Anthropic) with minimal code churn.
- **Parsing quality is a dependency**: `unstructured` warns when `libmagic` is unavailable; parsing reliability and filetype detection affect ingestion quality.
- **Reproducibility requires pinned sample data**: the pipeline currently assumes `old-demos/` exists locally; this must be standardized for consistent demos and evaluation.

## Next Architecture (Milestone 3+): Multi-Agent Modernization Loop

Milestone 2 proves ingestion + memory + basic QA. The next step is to evolve into a **plan–execute–verify** loop with multiple agents.

```mermaid
flowchart TB
  subgraph Memory[Shared Memory Layer]
    VS[(FAISS Vector Store)]
    SUM[Run notes / decisions]
  end

  subgraph Tools[Tooling / Execution Layer]
    T1[Static analysis<br/>AST/lint/type checks]
    T2[Dependency inspection<br/>pip/uv metadata]
    T3[Test runner<br/>pytest / scripts]
    T4[Patch application<br/>git diff + rollback]
  end

  A[Target repo] --> ING[Ingestion + Indexing] --> VS

  VS --> D[Debt Detector Agent<br/>(find outdated patterns)]
  VS --> P[Planner Agent<br/>(upgrade plan + steps)]
  P --> E[Executor Agent<br/>(apply patches)]
  E --> V[Verifier Agent<br/>(tests + sanity checks)]

  D --> SUM
  P --> SUM
  E --> SUM
  V --> SUM

  D --> Tools
  P --> Tools
  E --> Tools
  V --> Tools

  V -->|pass| OUT[PR-ready change set]
  V -->|fail| P
```

### Coordination + safety model (intended)

- **Human-in-the-loop checkpoints**: planning output and patch diffs are reviewable before execution.
- **Reversible changes**: all modifications applied via diffs/commits; failures trigger rollback/retry.
- **Evidence-driven decisions**: prefer tool outputs (tests, dependency metadata, docs) over pure model assertions.

