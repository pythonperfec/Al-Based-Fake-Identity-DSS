# AI-Based Fake Identity & Document Screening System

**Context:** Hackathon prototype (5-hour budget, 2 developers).

An AI-assisted document screening and identity verification platform designed to aid border control and document screening officers. 

> **Important Operational Principle:**
> AI assists the officer; it never makes the final border decision. Risk score is a screening signal, NOT a fraud probability.

---

## Architecture Overview

- **`/backend`**: FastAPI (Python 3.11), asynchronous API, modular monolith architecture using interface-driven dependencies.
- **`/frontend`**: Next.js App Router (TypeScript, Tailwind CSS), reviewer-facing dashboard.
- **`/samples`**: Synthetic sample document generator and test fixtures (strictly non-production, synthetic data).
- **`/docs`**: System documentation, API contracts, and decision records.

---

## Directory Structure

```text
.
├── .env.example
├── .gitignore
├── AGENTS.md
├── docker-compose.yml
├── README.md
├── backend/
├── frontend/
├── samples/
└── docs/
    └── API_CONTRACT.md
```

See [AGENTS.md](AGENTS.md) for permanent engineering principles and [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for endpoint specifications.
