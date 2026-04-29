# Devlog — PropSync Manager

This devlog documents the development journey of PropSync Manager. Each entry describes what was built, why the decision was made, and how it aligns with the project's strategic goals.

---

## Phase 3 — Open Source Publication (April 2026)

**Goal:** Prepare PropSync Manager for community contributions and academic evaluation.

### Entry 3.3 — April 24, 2026: Open Source Hardening

**What changed:**
- Rewrote `README.md` in English with badges, architecture diagram, multi-platform deployment instructions (local, DevContainer, Netlify), and usage examples.
- Created `CONTRIBUTING.md` with a skills matrix, contribution roadmap, and onboarding path for new developers (criteria 6k).
- Formalised the `LICENSE` file (MIT) — previously only referenced in the README footer.
- Expanded `.gitignore` to explicitly protect `secrets.json` and `data/credenciales.json`.
- Created `netlify.toml` to deploy `web_dashboard/` as a live UI demo at `propsync-manager.netlify.app`.
- Added Google-style docstrings to all Python modules (`main.py`, `trading.py`, `database.py`, `config.py`).
- Added JSDoc comments to `web_dashboard/app.js` and `web_local/app.js`.
- Created `wiki/` with Developer Guide, Security Guide, and this Devlog.
- Created `preguntas.md` answering all evaluation criteria (6a–6k) with specific, contextualised answers.

**Strategic alignment:** This phase transforms the project from a functional private tool into an auditable, community-ready open source project, directly supporting the company's goals of transparency, scalability, and knowledge transfer.

---

### Entry 3.2 — April 16, 2026: Prop Firm Tracker Integration

**What changed:**
- Integrated the `lp-demo-tracker-card` UI structure into both the cloud dashboard and local terminal.
- Added real-time drawdown and profit target progress bars for all configured accounts.
- Telemetry polling now correctly updates per-account metrics from the Python engine.

**Strategic alignment:** Operational risk monitoring is now visual and real-time, eliminating the need for operators to manually check individual platform accounts. This directly reduces the cognitive load on trading personnel and minimises rule-violation risk.

---

### Entry 3.1 — April 14, 2026: Analytics Dashboard Refinement

**What changed:**
- Completed integration of daily and total drawdown metrics across all accounts in the analytics dashboard.
- Finalised the landing page authentication flow (login + registration).
- Improved aesthetic alignment of phase targets and navigation tabs.

**Strategic alignment:** A polished, authenticated UI is essential for adoption beyond a single developer. This entry made PropSync presentable to non-technical stakeholders.

---

## Phase 2 — Cloud Integration (April 2026)

### Entry 2.1 — April 14, 2026: Supabase Cloud Layer

**What changed:**
- Integrated Supabase as the optional cloud backend.
- `database.py` now syncs closed trades to the `trades` table in Supabase.
- `BridgeAPI.conectar()` authenticates against Supabase Auth before starting the MT5 engine.
- `upload_user_config()` / `download_user_config()` added for config backup/restore.
- Separated `web_dashboard/` (cloud-first) from `web_local/` (pywebview).

**Why Supabase:** Evaluated Firebase and AWS Amplify. Supabase was chosen for its PostgreSQL backend (vs. NoSQL), its MIT-licensed open core, and its Python client library. The free tier is sufficient for individual trader usage.

**Strategic alignment:** Cloud integration moves PropSync from a single-machine tool to a multi-device, recoverable platform. A trader can review their trade history from any browser without accessing their trading PC.

---

## Phase 1 — Core RPA Engine (Prior to April 2026)

### Entry 1.3 — Cloud-first UI Architecture

**What changed:**
- Replaced the initial `customtkinter` GUI with a `pywebview` window rendering an HTML/CSS/JS interface.
- This decouples the UI from Python's GUI toolkit limitations, enabling modern web design patterns.

**Why pywebview:** Tkinter-based GUIs are difficult to style and maintain. pywebview provides a Chromium rendering engine while keeping the Python backend accessible via a clean JS bridge — no HTTP server needed, no CORS issues, zero additional processes.

---

### Entry 1.2 — Slave Volume Normalisation

**What changed:**
- Implemented `calcular_volumen()` with broker-aware clamping (`volume_min`, `volume_max`, `volume_step`).
- Previously, slave lot sizes were calculated as a simple ratio, which could produce values rejected by the broker (e.g., 0.003 lots when minimum is 0.01).

---

### Entry 1.1 — Initial RPA Trading Loop

**What changed:**
- Implemented `ciclo_trading_recursivo()` as a daemon thread polling MT5 every 500ms.
- Added bidirectional ticket mapping (`mapa_operaciones.json`) to track Master↔Slave trade relationships.
- Implemented full lifecycle coverage: **open → modify SL/TP → close**.

**Strategic motivation:** The core problem — replicating trades across multiple accounts — required an always-on loop with sub-second latency. A 500ms interval was chosen as the optimal balance between responsiveness and MT5 API rate limits.

---

*This devlog is also shared on [LinkedIn](https://www.linkedin.com/posts/manuel-amado-rodriguez-b72064407_fintech-algorithmictrading-opensource-share-7455203935151337472--yq-?utm_source=share&utm_medium=member_desktop&rcm=ACoAAGfE94YBgc7QFfZ_t0tg8mg9wsTYvWsFgmI) as a professional development post series.*
