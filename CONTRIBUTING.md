# Contributing to PropSync Manager

Thank you for your interest in contributing to PropSync Manager! This document explains how to get involved, what areas need work, and what skills are most useful.

---

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Areas for Contribution](#areas-for-contribution)
6. [Required Skills & Training](#required-skills--training)
7. [Submitting a Pull Request](#submitting-a-pull-request)

---

## Code of Conduct

This project follows a simple rule: **be professional and constructive**. Harassment, discriminatory language, or bad-faith behaviour will result in permanent exclusion. When in doubt, treat every contributor as a colleague you respect.

---

## How to Contribute

There are many ways to contribute beyond writing code:

- **Bug reports** — Open a [GitHub Issue](https://github.com/mamarod428/PropSync-Manager/issues) with reproduction steps.
- **Feature requests** — Describe the use case, not just the implementation.
- **Documentation** — Improve the wiki, add docstring examples, or translate content.
- **Testing** — Write integration tests or validate behaviour with different brokers/servers.
- **Code** — Fix bugs, improve performance, or implement features from the roadmap below.

---

## Development Setup

### 1. Fork & clone

```bash
git clone https://github.com/YOUR_USERNAME/PropSync-Manager.git
cd PropSync-Manager
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux (for UI-only work)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure secrets

Copy the template and fill in your Supabase credentials:

```bash
copy secrets.example.json secrets.json
```

Edit `secrets.json`:
```json
{
  "SUPABASE_URL": "https://your-project.supabase.co",
  "SUPABASE_KEY": "your-anon-key"
}
```

### 5. Verify the setup

```bash
python -m py_compile main.py modules/trading.py modules/database.py modules/config.py
echo "All modules compile successfully"
```

---

## Coding Standards

### Python

- Follow **PEP 8** (max line length 100 characters).
- Use **Google-style docstrings** for all public functions, classes, and modules:

```python
def calcular_volumen(symbol: str, lot_maestro: float, eq_maestra: float,
                     eq_esclava: float, factor_riesgo: float) -> float:
    """Calculates the proportional lot size for a slave account.

    Args:
        symbol: The trading instrument symbol (e.g., 'EURUSD').
        lot_maestro: The lot size on the master account.
        eq_maestra: The equity of the master account in account currency.
        eq_esclava: The equity of the slave account in account currency.
        factor_riesgo: A user-defined multiplier to scale risk up or down.

    Returns:
        The normalised lot size clamped to the broker's volume_min/volume_max.
    """
```

- Avoid bare `except:` — always catch specific exceptions or at minimum `Exception as e`.
- Use boolean variables rather than bare integers for flag states where clarity is improved.

### JavaScript

- Use **JSDoc** for all functions:

```javascript
/**
 * Polls the Python engine for live telemetry data and updates the dashboard.
 * @param {number} intervalMs - Polling interval in milliseconds.
 * @returns {void}
 */
function startTelemetryPolling(intervalMs) { ... }
```

- Prefer `const`/`let` over `var`.
- All DOM element IDs must be unique and descriptive.

### Git

- Branch naming: `feature/short-description`, `fix/issue-number-description`, `docs/what-you-improved`.
- Commit messages follow **Conventional Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`.
- Do **not** commit `secrets.json` or `data/credenciales.json` — they are gitignored for a reason.

---

## Areas for Contribution

These are concrete improvements sorted by complexity:

### 🟢 Good first issues (low complexity)

| # | Area | Description |
|---|---|---|
| 1 | Docs | Add `secrets.example.json` template file |
| 2 | Docs | Translate README sections to Spanish |
| 3 | UI | Add a "Copy to clipboard" button for log messages |
| 4 | Config | Validate numeric fields before saving Master config |
| 5 | Tests | Write unit tests for `calcular_volumen()` edge cases |

### 🟡 Medium complexity

| # | Area | Description |
|---|---|---|
| 6 | Feature | CSV export for the trade history table |
| 7 | Feature | Configurable polling interval (currently hardcoded at 500ms) |
| 8 | Feature | Per-slave enable/disable toggle without deleting the node |
| 9 | Security | Replace Base64 obfuscation with OS-level keyring (`keyring` library) |
| 10 | Feature | Email/Telegram alert when drawdown threshold is breached |

### 🔴 Advanced / high-impact

| # | Area | Description |
|---|---|---|
| 11 | Platform | Linux compatibility (requires alternative to `MetaTrader5` package, e.g., Wine or cTrader) |
| 12 | Platform | Mobile companion app (React Native) consuming the Supabase trade history |
| 13 | Feature | Backtesting mode: replay historical trades and simulate replication results |
| 14 | Architecture | Plugin system for custom risk rules per slave node |
| 15 | Cloud | Real-time dashboard using Supabase Realtime subscriptions instead of polling |

---

## Required Skills & Training

### For Python (engine) contributions

| Skill | Level needed | Learning resources |
|---|---|---|
| Python 3.11+ | Intermediate | [Official docs](https://docs.python.org/3/) |
| MetaTrader5 Python API | Beginner | [MQL5 docs](https://www.mql5.com/en/docs/python_metatrader5) |
| Threading / daemon threads | Beginner | [RealPython guide](https://realpython.com/intro-to-python-threading/) |
| Supabase Python client | Beginner | [Supabase docs](https://supabase.com/docs/reference/python/introduction) |
| JSON file I/O | Beginner | Python official docs |

### For JavaScript (dashboard) contributions

| Skill | Level needed | Learning resources |
|---|---|---|
| Vanilla ES6+ JS | Intermediate | [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/JavaScript) |
| Supabase JS client | Beginner | [Supabase JS docs](https://supabase.com/docs/reference/javascript/introduction) |
| Chart.js | Beginner | [Chart.js docs](https://www.chartjs.org/docs/latest/) |
| pywebview JS↔Python bridge | Beginner | [pywebview docs](https://pywebview.flowrl.com/guide/api.html) |

### Onboarding path for new contributors

1. **Read the [Developer Guide](wiki/Developer-Guide.md)** — understand module responsibilities and the data flow.
2. **Run the application locally** — follow the README setup instructions.
3. **Read an existing module** — start with `modules/config.py` (smallest, ~100 lines).
4. **Pick a 🟢 issue** — open it, comment that you're working on it, then submit a PR.
5. **Request a review** — all PRs need at least one reviewer approval before merging.

---

## Submitting a Pull Request

1. Ensure your branch is up to date with `main`.
2. Run the compile check:
   ```bash
   python -m py_compile main.py modules/trading.py modules/database.py modules/config.py
   ```
3. Update docstrings if you changed function signatures.
4. Open a PR against `main` with a clear description of *what* changed and *why*.
5. Link any related issues in the PR description.

---

*Thank you for making PropSync Manager better for everyone.*
