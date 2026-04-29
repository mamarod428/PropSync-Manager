# PropSync Manager — Strategic Analysis (preguntas.md)

> This document answers all evaluation criteria (6a–6k) contextualised for **PropSync Manager**, a RPA-based trade synchronisation engine for financial prop firm operators.

---

## Criterion 6a) Strategic Objectives

### What specific strategic objectives of the company does your software address?

PropSync Manager targets a **financial asset management firm** that manages capital across multiple funded accounts (Prop Firm accounts). The strategic objectives addressed are:

1. **Capital scalability without proportional headcount growth.** Managing 10 accounts manually requires 10× the human attention. PropSync makes account count operationally irrelevant.
2. **Risk compliance at scale.** Each prop firm imposes strict daily drawdown and total drawdown limits. Violating them results in account termination. The software monitors limits in real time per account, reducing the risk of costly violations.
3. **Operational standardisation.** All slave accounts replicate the same strategy with mathematically proportional sizing, eliminating inconsistency between accounts that would arise from manual replication.
4. **Data-driven decision making.** The cloud dashboard provides a consolidated view of P&L, drawdown, and open positions across all accounts, enabling the firm's operations director to make informed allocation decisions.

### How does the software align with the company's overall digitalisation strategy?

The software embodies the **Process Digitalisation** pillar of the company's digitalisation roadmap:

- **Before PropSync:** A trader manually logs into each MT5 account, replicates positions by hand, and monitors drawdowns through separate platform windows.
- **After PropSync:** A single operator supervises the entire network through one interface. The RPA engine handles execution; the operator handles strategy.

This aligns with Objective 3 of a typical financial firm's digitalisation strategy: *"Eliminate repetitive manual processes in trading operations by Q2 2026."*

---

## Criterion 6b) Business Areas and Communications

### Which company areas (production, business, communications) benefit most from your software?

| Area | Benefit |
|---|---|
| **Trading Operations (Production)** | 100% elimination of manual trade replication. Execution latency reduced from minutes (manual) to <500ms (automated). |
| **Risk Management (Business)** | Real-time per-account drawdown monitoring with visual progress bars tied to prop firm-specific limits. |
| **Reporting / Communications** | Cloud dashboard and Supabase trade history enable automatic generation of trading reports without manual data collection. |
| **Finance / Accounting** | Consolidated P&L data per account exported via the history module, reducing reconciliation time. |

### What operational impact do you expect in daily operations?

| Metric | Before | After |
|---|---|---|
| Time to replicate 1 trade across 5 accounts | ~3 minutes (manual) | <1 second (automated) |
| Daily drawdown checks | Manual, per platform | Continuous, automated, visual alert |
| Accounts manageable per operator | 2–3 (cognitive limit) | Virtually unlimited |
| Human errors in lot sizing | Frequent (manual calculation) | Zero (formula-based, broker-validated) |

The most significant daily impact is **operator cognitive load reduction**: the trader focuses exclusively on strategy, while PropSync handles all mechanical execution.

---

## Criterion 6c) Areas Susceptible to Digitalisation

### Which company areas are most susceptible to being digitalised with your software?

1. **Trade execution desk** — Currently the most labour-intensive area. Every signal (open, modify SL/TP, close) must be replicated manually per account. This is a textbook case for RPA.
2. **Risk monitoring** — Drawdown tracking is performed by checking each platform individually. This can be fully digitalised into a unified dashboard.
3. **Account onboarding** — Registering a new slave account currently involves manual credential entry and parameter calculation. PropSync's "Register Node" + "Calculate Factor" workflow digitalises this in <2 minutes.
4. **Trade history reconciliation** — Exporting and matching trade data across accounts for monthly reporting is manual. Supabase cloud sync digitalises this automatically per trade close.

### How will digitalisation improve operations in those areas?

- **Trade execution:** Zero latency propagation of risk-proportional orders. Eliminates slippage divergence between accounts due to delayed manual entry.
- **Risk monitoring:** Real-time visual drawdown gauges replace manual platform checks every 15–30 minutes. The firm can set alert thresholds and respond to limit breaches in seconds instead of minutes.
- **Reconciliation:** Supabase stores a structured trade record per close event, directly queryable for monthly P&L reports without any manual export.

---

## Criterion 6d) Fit Between Digitalised and Non-Digitalised Areas

### How do digitalised and non-digitalised areas interact?

The digitalised process (automated trade replication) is completely dependent on a non-digitalised input: **the Master trader's decision to open or modify a position**. PropSync does not generate trading signals — it amplifies human decisions.

| Area | Status | Interaction Point |
|---|---|---|
| Strategy / signal generation | **Non-digitalised** (human) | Master account position changes |
| Trade execution & replication | **Digitalised** (PropSync) | Reads master positions, writes slave orders |
| Broker settlement | **Non-digitalised** (broker OT) | MT5 API returns execution confirmations |
| Reporting to management | **Partially digitalised** | Dashboard provides raw data; human writes narrative |

### What solutions would you propose to integrate these areas?

1. **Signal digitalisation bridge:** Integrate a TradingView webhook or a custom Pine Script alert system that feeds signals directly into PropSync, eliminating the need for the trader to manually enter positions on the master account.
2. **Automated reporting:** Add a scheduled Supabase function (Edge Function / cron) that generates a PDF performance report and emails it to management every Monday morning, fully digitalising the reporting pipeline.
3. **Broker API direct integration:** Future version: bypass MT5 entirely and connect to FIX Protocol or broker REST APIs, removing the Windows + MT5 installation dependency.

---

## Criterion 6e) Present and Future Needs

### What current company needs does your software solve?

| Current Pain Point | PropSync Solution |
|---|---|
| Manual trade replication across all funded accounts | Automated, sub-second synchronisation |
| Risk of missing a prop firm drawdown limit | Real-time visual monitoring per account |
| Calculation errors in proportional lot sizes | Formula-based, broker-validated volume calculation |
| No centralised view of multi-account performance | Unified cloud dashboard with P&L consolidation |
| Configuration loss if trading PC fails | Supabase cloud config backup + restore |

### What future needs does the software anticipate?

Looking at industry trends over the next 24–36 months:

| Future Need | Proposed Extension |
|---|---|
| Mobile monitoring (operators away from desk) | Mobile companion app (React Native) consuming Supabase real-time API |
| Multi-broker support | Plugin architecture allowing broker-specific adapters (cTrader, Interactive Brokers) |
| Automated risk shutdown | Per-account drawdown circuit breaker: auto-close all positions and halt replication when limit is 80% reached |
| Signal marketplace | Integration with copy-trade networks (e.g., MQL5 Signals) as signal source |
| Regulatory reporting | MIFID II compliant trade log export (timestamp, ISIN, execution price, counterparty) |

These extensions are documented in [CONTRIBUTING.md](CONTRIBUTING.md) as future contribution areas.

---

## Criterion 6f) Relationship with Enabling Technologies

### What enabling technologies have you used and how do they impact company areas?

| Technology | Classification | Company Area Impacted | Specific Benefit |
|---|---|---|---|
| **MetaTrader 5 Python API** | OT (Operational Technology) | Trading Operations | Direct, programmatic access to broker execution infrastructure |
| **RPA (Robotic Process Automation)** | THD (Digital Enabling Technology) | All operational areas | Eliminates repetitive human-computer interaction (login, replicate, verify) |
| **Supabase (BaaS)** | Cloud / IT | Risk Management, Reporting | Real-time persistent data layer with authentication, eliminates self-hosted infrastructure |
| **pywebview** | IT Middleware | UX / Operations | Bridges Python engine to modern web UI without HTTP server overhead |
| **Edge Computing (local JSON)** | IT Data Layer | Trading Operations | Zero-latency data access; critical for 500ms execution cycle |
| **Base64 obfuscation / OS Keyring (planned)** | IT Security | All areas | Credential protection at rest |

### What specific benefits does implementing these technologies bring?

- **RPA via MetaTrader5 API:** Transforms a 3-minute manual task into a <500ms automated one — a 360× speed improvement. This directly increases the firm's maximum tradable account capacity.
- **Supabase:** Eliminates the need to host and maintain a backend server. A two-person trading firm can have cloud-grade infrastructure with no DevOps team.
- **Edge computing (local JSON):** The decision to store live operational data locally (not in the cloud) is a performance-critical architectural choice. A cloud round-trip would add 50–200ms per decision cycle, potentially causing slippage on fast-moving markets.

---

## Criterion 6g) Security Gaps

### What security gaps could arise when implementing your software?

| Gap | Severity | Affected Area |
|---|---|---|
| Base64 is reversible encoding, not encryption | High | Credential security |
| `secrets.json` could be accidentally committed to GitHub | Critical | Cloud security |
| Supabase tables without RLS expose all users' data | Critical | Data privacy |
| pywebview JS bridge has no input validation | Medium | Application integrity |
| No audit log of trade events | Medium | Regulatory / forensics |
| No rate limiting on bridge API calls | Low | Stability |

### What concrete measures do you propose to mitigate them?

| Gap | Mitigation |
|---|---|
| Base64 credentials | Migrate to `keyring` library (OS Credential Manager) — see [Security Guide](wiki/Security-Guide.md) §4.1 |
| `secrets.json` in git | Explicitly listed in `.gitignore`; add a pre-commit hook that blocks commits if the file is modified |
| Supabase without RLS | Implement row-level security policies (see [Security Guide](wiki/Security-Guide.md) §3) |
| Bridge input validation | Add Pydantic model validation to all `BridgeAPI` methods |
| No audit log | Add structured audit logging with timestamps to a separate `data/audit.json` file |
| No rate limiting | Add a cooldown counter in the bridge to reject calls made faster than 5/second |

---

## Criterion 6h) Data Treatment and Analysis

### How is data managed in your software and what methodologies do you use?

PropSync uses a **dual-tier data architecture**:

#### Tier 1: Local Edge Storage (operational, real-time)
| Data | Format | Location | Lifecycle |
|---|---|---|---|
| Live trade map | JSON | `data/mapa_operaciones.json` | Written on open, deleted on close |
| Trade history | JSON array | `data/historial_operaciones.json` | Append-only, never deleted |
| Account credentials | Base64 JSON | `data/credenciales.json` | Updated on user config save |
| Prop firm rules | JSON | `data/prop_firms.json` | Updated on firm database edit |

**In-memory first:** The trade map is loaded into a Python dict at startup. All reads/writes during the trading loop operate on RAM. Disk writes happen only when a change is detected — minimising I/O latency.

#### Tier 2: Cloud Storage (analytics, recovery)
| Data | Table | Lifecycle |
|---|---|---|
| Closed trades | `trades` | Appended on close, permanent |
| User configuration | `user_configs` | Upserted on config save |
| Prop firm database | `prop_firms` | Shared reference data |

The synchronisation between Tier 1 and Tier 2 is **asynchronous and eventually consistent**: local operations never wait for cloud confirmation.

### How do you ensure the quality and consistency of the data?

1. **Bidirectional ticket mapping:** Every master ticket is linked to a slave ticket with a recorded SL, TP, and price. The trading loop validates this map every 500ms against the live broker state, purging stale entries automatically.
2. **Type enforcement:** All financial values (SL, TP, price) are rounded to 5 decimal places (`round(float(x), 5)`) before storage, preventing floating-point drift accumulation across write cycles.
3. **Cloud deduplication:** Before uploading historical trades to Supabase, `sincronizar_historial_con_nube()` fetches existing ticket IDs and performs a set-difference, uploading only records that are absent in the cloud. This prevents duplicate entries.
4. **Graceful degradation:** All JSON read operations are wrapped in `try/except`, returning empty defaults on corruption rather than crashing the application. The trading engine continues running even if persistence fails temporarily.

---

## Criterion 6i) Integration Between Data, Applications, and Platforms

### How do the systems and data interact?

```
[MetaTrader 5 Broker Server]  ←→  [MT5 Python API]
                                         │
                              [modules/trading.py]
                                         │ reads/writes
                              [modules/database.py]
                               /                    \
              [data/*.json]                    [Supabase Cloud]
              (local, 0ms)                     (async, ~50ms)
                    │                                │
              [main.py RAM]                  [trades table]
                    │
         [BridgeAPI methods]
                    │ pywebview bridge
         [web_local/app.js]  ←→  [web_dashboard/app.js]
                    │                      │
            [Local UI]              [Netlify Demo / Browser]
```

**Key integration points:**
- **MT5 ↔ Python:** MetaTrader5 package wraps the MT5 COM/DLL interface. All position, order, and account data is returned as namedtuples.
- **Python ↔ JavaScript:** pywebview provides a synchronous-from-JS-perspective bridge. JS awaits Python method calls which execute synchronously in the Python process.
- **Python ↔ Supabase:** The Supabase Python client uses HTTPX under the hood. All cloud operations are attempted but silently skipped on failure, ensuring local operations are never blocked.

### What proposals would you make to improve interoperability between systems?

1. **WebSocket event streaming:** Replace the 500ms JavaScript polling loop for telemetry with a WebSocket channel. Python pushes updates when state changes, eliminating unnecessary network round-trips.
2. **Supabase Realtime subscriptions:** Use Supabase's real-time capabilities to push trade events to the web dashboard without polling, enabling sub-second dashboard updates on any browser.
3. **REST API layer:** Expose a local REST API (FastAPI) alongside pywebview, enabling third-party integrations (TradingView webhooks, mobile apps, external monitoring tools) without modifying the core engine.
4. **Standardised data schema:** Define a JSON Schema (or Pydantic model) for the trade record and config objects, ensuring all integration points (local JSON, Supabase, API) use the same data contract.

---

## Criterion 6j) Documenting Changes Per Strategy

### How have changes been clearly recorded and linked to strategic objectives?

All development changes are documented in the [Devlog](wiki/Devlog.md), structured by phase and entry, with each entry explicitly stating:
- **What changed** (technical description)
- **Why** (business justification)
- **Strategic alignment** (link to company objective)

Example: Entry 1.2 (Slave Volume Normalisation) was not a feature addition — it was a quality fix driven by the strategic objective *"ensure prop firm compliance at scale"*. Without correct lot sizing, slave accounts would receive broker rejections, undermining the firm's operational reliability.

### How is the devlog maintained?

The devlog in `wiki/Devlog.md` is:
- Updated with every significant merge to `main`.
- Formatted for direct LinkedIn publication (each entry reads as a standalone professional post).
- Cross-referenced with the GitHub Release changelog for official version milestones.

---

## Criterion 6k) Human Resources Suitability

### What specific skills are needed to develop and maintain this software?

| Role | Required Skills | Desirable Skills |
|---|---|---|
| **Core Engine Developer (Python)** | Python 3.11+, threading, JSON I/O, MetaTrader5 API | Finance domain knowledge, RPA patterns |
| **Frontend Developer (Web)** | HTML5, CSS3, Vanilla JS ES6+, JSDoc | Chart.js, Supabase JS client |
| **Cloud Engineer** | Supabase (PostgreSQL, Auth, RLS, Edge Functions) | SQL, REST API design |
| **DevOps / Maintainer** | Git, GitHub Actions, Netlify, pdoc3 | Docker, GitHub Pages |
| **Domain Expert** | Financial trading concepts, prop firm rules, MT5 platform | Algorithmic strategy evaluation |

### What training strategies do you propose for future collaborators?

1. **Structured onboarding path** (documented in [CONTRIBUTING.md](CONTRIBUTING.md#required-skills--training)):
   - Week 1: Read Developer Guide + run the app locally.
   - Week 2: Implement a 🟢 Good First Issue.
   - Week 3+: Graduate to 🟡 Medium issues.

2. **Annotated codebase:** All modules now contain Google-style docstrings with parameter types, return values, and usage examples. New contributors can understand any function in isolation without tracing the entire codebase.

3. **"Good first issue" labels on GitHub:** Curated list of 5 starter tasks in CONTRIBUTING.md and on the GitHub Issues board, matched to each skill level.

4. **Domain knowledge resource list:** The CONTRIBUTING.md contains direct links to the MetaTrader5 Python API documentation, Supabase docs, and pywebview bridge guide — the three most unfamiliar technologies for typical web developers joining the project.

5. **Code review culture:** All PRs require at least one review. The review process itself is a training mechanism — reviewers document *why* a pattern was accepted or rejected, building institutional knowledge.
