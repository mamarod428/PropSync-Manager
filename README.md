# PropSync Manager

<div align="center">

**Production-grade RPA engine for synchronizing MetaTrader 5 trading accounts.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Demo](https://img.shields.io/badge/Demo-Netlify-00C7B7.svg)](https://propsync-manager.netlify.app)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

[**Live UI Demo**](https://propsync-manager.netlify.app) · [**Documentation**](docs/) · [**Contributing**](CONTRIBUTING.md) · [**Wiki**](wiki/) · [**LinkedIn Update**](https://www.linkedin.com/posts/manuel-amado-rodriguez-b72064407_fintech-algorithmictrading-opensource-share-7455203935151337472--yq-?utm_source=share&utm_medium=member_desktop&rcm=ACoAAGfE94YBgc7QFfZ_t0tg8mg9wsTYvWsFgmI)

</div>

---

## 🎓 Evaluation Guide (For Academic Reviewers)

If you are a professor or academic reviewer without prior knowledge of algorithmic trading, here is a quick summary of what this software achieves and how to evaluate it:

1. **The Business Problem:** Traders managing capital for "Prop Firms" (companies that fund traders) often trade on 5-10 accounts simultaneously. Doing this manually is slow and prone to errors. If they make a mistake, they lose the funded account.
2. **The Solution (This Software):** PropSync Manager is an RPA (Robotic Process Automation) tool. The human trades *only once* on a "Master" account. In less than 0.5 seconds, this Python engine detects the human's action and automatically copies the trade to all "Slave" accounts, calculating the exact proportional risk.
3. **How to test it without trading knowledge:**
   - You don't need to install trading platforms to see the interface. Click the **[Live UI Demo](https://propsync-manager.netlify.app)** link above. It demonstrates the cloud dashboard built for the firm's management.
   - **Demo Account Access:** Log in to the web dashboard using the following credentials to view a pre-configured network of demo accounts and real trade history:
     - **Email:** `admin@admin.com`
     - **Password:** `pass@123`
   - **Local Testing:** If you wish to run the desktop Python app locally, you will need the Supabase API keys to connect to the cloud backend. These keys have been provided in a **supplementary PDF attached to the project submission** (to avoid exposing secrets in version control). Copy the keys from the PDF into a `secrets.json` file as explained in the deployment instructions below.
   - To review the academic requirements (rubrics 6a to 6k), please read the **[`preguntas.md`](preguntas.md)** file in the root directory, which contains a detailed strategic analysis of this software's impact on a company.
   - For technical documentation, explore the **[Wiki](wiki/)** and the auto-generated **[API Docs](docs/api/)**.

---

## What is PropSync Manager?

PropSync Manager is an open-source **Robotic Process Automation (RPA)** desktop application for algorithmic traders managing multiple MetaTrader 5 accounts. It captures every market event on a **Master account** and replicates it proportionally across any number of **Slave accounts** in under 500 milliseconds — without any manual intervention.

### Why does it exist?

Managing capital distributed across multiple prop-firm accounts (FTMO, We Study Forex, Axi Select, etc.) is operationally demanding:

- A trader operating 5 funded accounts must manually replicate every trade, SL/TP modification, and closure × 5.
- Human error in replication leads to divergent risk profiles across accounts.
- Prop firm rules (max daily drawdown, profit targets) require constant per-account monitoring.

PropSync Manager **eliminates this operational overhead entirely**, allowing a single operator to manage an arbitrarily large network of accounts with zero additional cognitive load.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PropSync Manager                        │
│                                                             │
│  ┌──────────────┐    ┌───────────────┐    ┌─────────────┐  │
│  │  Web UI Layer │    │  Python Engine │    │   MT5 OT   │  │
│  │  (pywebview)  │◄──►│   (main.py)   │◄──►│    API     │  │
│  │  HTML/CSS/JS  │    │               │    │  (broker)  │  │
│  └──────────────┘    └───────┬───────┘    └─────────────┘  │
│                              │                              │
│              ┌───────────────┼───────────────┐             │
│              ▼               ▼               ▼             │
│       modules/config  modules/trading  modules/database    │
│       (credentials)   (RPA engine)    (JSON + Supabase)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ optional
                     ┌─────────────────┐
                     │  Cloud Layer    │
                     │  (Supabase)     │
                     │  auth + trades  │
                     └─────────────────┘
```

**Execution model:** The trading loop runs in a dedicated daemon thread at 500ms intervals. All MT5 API calls, position validation, and slave replication happen here without blocking the UI. The pywebview bridge exposes a clean `BridgeAPI` for the JavaScript frontend to control the engine.

---

## Live Demo

> **[🌐 Open the UI Demo on Netlify →](https://propsync-manager.netlify.app)**

The Netlify deployment shows the full dashboard interface. Full trading engine connectivity requires the local Python application running on Windows with MetaTrader 5.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **OS** | Windows 10/11 | MT5 is Windows-only |
| **Python** | 3.11+ | [Download](https://www.python.org/) — check "Add to PATH" |
| **MetaTrader 5** | Any recent | [Download free](https://www.metatrader5.com/) |
| **Supabase account** | — | Optional — enables cloud sync & web dashboard |

---

## Deployment

### Option A — Local (Recommended for full functionality)

#### 1. Clone the repository
```bash
git clone https://github.com/mamarod428/PropSync-Manager.git
cd PropSync-Manager
```

#### 2. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure credentials
Create `secrets.json` in the project root (use `secrets.example.json` as template):
```json
{
  "SUPABASE_URL": "https://your-project.supabase.co",
  "SUPABASE_KEY": "your-anon-key"
}
```
> **Note:** If you skip Supabase, leave both values as empty strings `""`. The app will run in local-only mode.

#### 5. Configure MetaTrader 5
1. Open **MetaTrader 5**.
2. Go to **Tools → Options → Expert Advisors**.
3. Enable **"Allow Algo Trading"**.
4. Ensure you are logged in to at least one account.

#### 6. Run the application
```bash
python main.py
```

---

### Option B — DevContainer (VS Code)

The repository includes a `.devcontainer` configuration for a consistent development environment.

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VS Code extension.
2. Open the project in VS Code.
3. Press `F1` → **"Dev Containers: Reopen in Container"**.
4. The container installs all Python dependencies automatically.

> **Note:** MT5 API (`MetaTrader5` package) requires Windows. Use the DevContainer for development, code review, or working on the web dashboard only.

---

### Option C — Online Demo (Web Dashboard Only)

The cloud dashboard is deployed at **[propsync-manager.netlify.app](https://propsync-manager.netlify.app)**.

To deploy your own instance:
1. Fork this repository.
2. Connect it to [Netlify](https://netlify.com).
3. Set **Publish directory** to `web_dashboard`.
4. Configure your Supabase environment variables in Netlify's dashboard.

---

## Usage Guide

### Initial Setup Workflow

```
1. Launch app → Login screen appears
2. Enter Supabase email/password → App authenticates
3. Go to "Network Configuration" tab
   └─ Enter Master account: Login, Password, Server, Initial Balance
   └─ Click "Apply Changes"
4. Register Slave nodes
   └─ Add each funded account (Login, Password, Server, Risk Factor)
   └─ Click "Register Node"
5. Click "START SERVICE" (green button, left panel)
   └─ Confirm "[SYSTEM RUNNING]" message appears
```

### Example: Copying a trade from Master to 3 Slaves

Once the service is running, open a position on your Master account in MetaTrader 5:

```
Master   → BUY 1.00 EURUSD @ 1.08520  SL: 1.08420  TP: 1.08720
PropSync → detects new position within 500ms
Slave A  → BUY 0.43 EURUSD @ 1.08521  (43% equity ratio, RF=1.0)
Slave B  → BUY 0.21 EURUSD @ 1.08521  (21% equity ratio, RF=1.0)
Slave C  → BUY 0.35 EURUSD @ 1.08522  (35% equity ratio, RF=1.0)
```

Lot sizes are calculated proportionally using the formula:
```
slave_lots = master_lots × (slave_equity / master_equity) × risk_factor
```

### Prop Firm Rule Monitoring

In the **Prop Firm Database** section, register your account limits:

| Firm | Daily DD | Total DD | Phase 1 Target | Phase 2 Target |
|---|---|---|---|---|
| FTMO | 5% | 10% | 10% | 5% |
| We Study Forex | 4% | 8% | 8% | 5% |
| Axi Select | 10% | 10% | 7% | 7% |

The dashboard visualises current drawdown vs. limits in real time.

---

## Project Structure

```
PropSync-Manager/
├── main.py               # Application entry point & BridgeAPI
├── requirements.txt      # Python dependencies
├── netlify.toml          # Netlify deployment config
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # Contribution guide
├── secrets.example.json  # Template for secrets.json
│
├── modules/
│   ├── config.py         # Credential management (Base64 obfuscation)
│   ├── trading.py        # MT5 RPA engine (open/modify/close)
│   └── database.py       # JSON persistence + Supabase cloud sync
│
├── web_dashboard/        # Cloud web interface (Netlify demo)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── web_local/            # Local pywebview interface
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── data/                 # Runtime data (gitignored)
│   ├── credenciales.json
│   ├── mapa_operaciones.json
│   └── historial_operaciones.json
│
├── docs/                 # Auto-generated API documentation (GitHub Pages)
│   └── api/
│
└── wiki/                 # Developer documentation & devlog
    ├── Home.md
    ├── Developer-Guide.md
    ├── Devlog.md
    └── Security-Guide.md
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Desktop runtime | [pywebview](https://pywebview.flowrl.com/) | Chromium-based native window |
| Trading API | [MetaTrader5](https://pypi.org/project/MetaTrader5/) | Broker OT interface |
| Cloud backend | [Supabase](https://supabase.com/) | Auth, trade history, config sync |
| Frontend | HTML5 / CSS3 / Vanilla JS | Dashboard UI |
| Data persistence | JSON files | Edge computing (zero-latency reads) |
| Documentation | pdoc3 | Auto-generated Python API docs |

---

## Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, coding standards, and ideas for future features.

---

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.