# AGENTS.md - Permanent System Rules & Invariants

This file establishes the permanent engineering, ethical, and architectural invariants for the **AI-Based Fake Identity & Document Screening System**. All agents, developers, and code contributors must strictly adhere to these rules.

---

## 1. Operational & Decision Principles
- **Officer in the Loop:** AI assists the officer; it never makes the final border decision.
- **Risk Score Semantics:** Risk score is a screening signal, NOT a fraud probability. Never label it as a percentage chance of fraud.
- **Graceful Degradation:** Missing data, failed OCR, unavailable sources, or low-quality images must result in status `"incomplete"`, never an automatic fraud finding.
- **Validity vs. Forgery:** An expired document is a validity finding (`EXPIRED_DOCUMENT`, severity `medium`), not proof of forgery.
- **Findings vs. Checks:** Findings contain ONLY detected issues and anomalies. Passing results appear exclusively in the `checks` array, never in `findings`.

---

## 2. Architecture & Modularity
- **Modular Monolith:** Built with strict boundaries.
- **Interface Segregation:** Core business logic depends strictly on abstract interfaces (`typing.Protocol`) defined in `backend/app/domain/interfaces.py`:
  - `IOcrService`
  - `IDocumentValidator`
  - `ITamperDetector`
  - `IFaceVerifier`
  - `IWatchlistService`
  - `IObjectStorage`
  - `IJobQueue`
- **Dependency Injection:** Concrete classes are injected via FastAPI dependencies.
- **Decoupled Orchestrator:** The orchestrator never imports concrete implementations directly.

---

## 3. Data Privacy, PII & Logging
- **Opaque Identifiers:** Use opaque UUID primary keys throughout the entire database schema; never use passport numbers, national IDs, or document numbers as keys.
- **Zero Raw Data Logging:** Never log raw documents, full OCR text, or MRZ lines. Log IDs and non-sensitive metadata only.
- **Synthetic Data Exclusivity:** Use only synthetic or sample data. Real personal identification data is strictly prohibited.
- **Authentication & Seed Users:** Authentication uses `username`. Seed users are `"officer"` and `"admin"`.

---

## 4. Schemas, Enums & Finding Contracts
- **Finding Structure:** Every finding must have:
  - `type` (string code identifying the check, e.g., `EXPIRATION_CHECK`, `MRZ_CHECKSUM`)
  - `severity`: `"low"` | `"medium"` | `"high"`
  - `reason`: Human-readable explanation
  - `source`: Service or module that generated the finding (e.g., `ocr`, `validator`, `tamper_detector`)
  - `evidence_ref`: Nullable reference or bounding box identifier
- **Standard Statuses:**
  - `"queued"`
  - `"processing"`
  - `"completed"`
  - `"incomplete"`
  - `"failed"`
- **Standard Risk Levels:**
  - `"low"`
  - `"review_required"`
  - `"high"`
  - `"incomplete"`

---

## 5. Engineering Standards & Quality
- **Strict Typing:** All code must be fully typed (Python typing / TypeScript strict mode).
- **Unit Testing:** Every service must have unit tests.
- **Quality Gate:** Run tests before declaring any phase or task done.
