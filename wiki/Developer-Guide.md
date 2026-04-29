# Developer Guide — PropSync Manager

This guide explains the internal architecture of PropSync Manager for contributors and technical evaluators.

---

## 1. High-Level Architecture

PropSync Manager follows a **layered architecture** separating concerns across four domains:

```
┌────────────────────────────────────────────┐
│   Presentation Layer (pywebview / Browser) │
│   web_local/index.html  ·  web_local/app.js│
└────────────────────┬───────────────────────┘
                     │ JS ↔ Python bridge (BridgeAPI)
┌────────────────────▼───────────────────────┐
│    Application Layer  (main.py)            │
│    BridgeAPI · iciar_motor · ciclo_trading │
└──────┬──────────────┬──────────────────────┘
       │              │
┌──────▼──────┐  ┌────▼──────────┐
│ modules/    │  │ modules/      │
│ config.py   │  │ trading.py    │
│ (I/O only)  │  │ (MT5 RPA)     │
└─────────────┘  └────┬──────────┘
                      │
              ┌───────▼─────────┐
              │ modules/        │
              │ database.py     │
              │ JSON + Supabase │
              └─────────────────┘
```

---

## 2. Module Responsibilities

### `main.py` — Entry point & API bridge

| Responsibility | Implementation |
|---|---|
| Launch the pywebview window | `webview.create_window()` → `webview.start()` |
| Expose Python functions to JavaScript | `BridgeAPI` class passed as `js_api` |
| Manage the trading engine lifecycle | `iniciar_motor_trading()` / `detener_motor_trading()` |
| Run the trading loop in a daemon thread | `ciclo_trading_recursivo()` |
| Relay log messages to JS console | `registrar_log()` |

**Key design decision:** The trading loop runs in a `threading.Thread(daemon=True)` so it never blocks the UI thread. All shared state (`bot_activo`, `memoria_db`, `tickets_maestros_abiertos`) is accessed via Python globals. This is sufficient for the single-user, single-process nature of the application.

---

### `modules/config.py` — Configuration I/O

| Function | Purpose |
|---|---|
| `cargar_credenciales()` | Reads `data/credenciales.json`, decoding Base64 passwords |
| `guardar_credenciales()` | Encodes passwords in Base64 before writing to disk |
| `cargar_secrets()` | Reads `secrets.json` for Supabase credentials |
| `cargar_empresas()` | Reads prop firm rule sets from `data/prop_firms.json` |

**Security note:** Passwords are encoded with Base64 (not encrypted). This prevents casual shoulder-surfing of JSON files but is not cryptographically secure. See [Security Guide](Security-Guide.md) for the recommended upgrade path using OS keyring.

---

### `modules/trading.py` — MT5 RPA Engine

This is the operational technology (OT) layer. It speaks directly to the MetaTrader 5 broker API.

**Core functions:**

| Function | MT5 action |
|---|---|
| `cambiar_cuenta()` | `mt5.initialize()` → `mt5.login()` |
| `obtener_estado_maestro()` | `mt5.positions_get()` + `mt5.orders_get()` |
| `ejecutar_apertura()` | `mt5.order_send()` with `TRADE_ACTION_DEAL` or `TRADE_ACTION_PENDING` |
| `ejecutar_modificacion()` | `mt5.order_send()` with `TRADE_ACTION_SLTP` or `TRADE_ACTION_MODIFY` |
| `ejecutar_cierre()` | `mt5.order_send()` with `TRADE_ACTION_DEAL` (counter-position) or `TRADE_ACTION_REMOVE` |

**Volume calculation formula:**
```python
slave_lots = master_lots × (slave_equity / master_equity) × risk_factor
# Clamped to broker's volume_min and volume_max, rounded to volume_step
```

---

### `modules/database.py` — Persistence Layer

Two storage backends operate simultaneously:

#### Local JSON (primary — zero latency)
| File | Purpose |
|---|---|
| `data/mapa_operaciones.json` | Live map of `master_ticket → slave_ticket` links |
| `data/historial_operaciones.json` | Closed trade history |

The map is loaded into RAM at startup (`cargar_mapa_a_ram()`). All reads/writes during the trading loop operate on the in-memory dict. The RAM state is flushed to disk only when a change occurs (`guardar_ram_a_disco()`), minimising I/O overhead.

#### Supabase (secondary — async, optional)
| Table | Purpose |
|---|---|
| `trades` | Persistent trade history per user |
| `prop_firms` | Shared prop firm configuration |
| `user_configs` | Cloud backup of user's account configuration |

---

## 3. Data Flow: New Trade Replication

```
Master opens BUY 1.00 EURUSD
        │
        ▼ (every 500ms)
ciclo_trading_recursivo()
        │
        ├─ obtener_estado_maestro() → list of open positions
        │
        ├─ For each slave node:
        │     obtener_vinculo(db_ram, slave_id, master_ticket) → None (new)
        │     → add to tareas[slave_id]: {"tipo": "NUEVA", ...}
        │
        ├─ cambiar_cuenta(slave_cfg) → mt5.login(slave)
        │
        └─ ejecutar_apertura(op, slave_cfg, eq_master)
              │
              ├─ calcular_volumen() → slave_lots
              ├─ mt5.order_send(request)
              └─ guardar_vinculo(db_ram, slave_id, master_ticket, slave_ticket)
```

---

## 4. pywebview Bridge

The `BridgeAPI` class in `main.py` is the communication contract between the JavaScript frontend and the Python backend.

**Calling Python from JavaScript:**
```javascript
// All bridge calls are asynchronous and return Promises
const config = await window.pywebview.api.obtener_configuracion();
const result = await window.pywebview.api.guardar_maestra(masterData);
```

**Available bridge methods:**

| Method | Direction | Purpose |
|---|---|---|
| `conectar(email, password)` | JS → Python | Auth + start engine |
| `apagar_motor()` | JS → Python | Stop trading loop |
| `encender_motor()` | JS → Python | Restart trading loop |
| `obtener_telemetria()` | JS → Python | Get equity, balance, trade history |
| `obtener_configuracion()` | JS → Python | Get current app_config |
| `guardar_maestra(datos)` | JS → Python | Save master account config |
| `guardar_esclava(datos)` | JS → Python | Add or update a slave node |
| `eliminar_esclava(id)` | JS → Python | Remove a slave node |
| `db_get_prop_firms()` | JS → Python | Fetch prop firm rules from Supabase |
| `db_add_prop_firm(data)` | JS → Python | Insert a new prop firm record |
| `obtener_claves_js()` | JS → Python | Pass Supabase keys to JS securely |

---

## 5. Setting Up the Development Environment

See [CONTRIBUTING.md](../CONTRIBUTING.md#development-setup) for the full setup guide.

### Generating API documentation

```bash
pip install pdoc3
pdoc3 --html --output-dir docs/api/ main modules
```

Open `docs/api/index.html` in your browser.

### Running syntax checks

```bash
python -m py_compile main.py modules/trading.py modules/database.py modules/config.py
```

---

## 6. Testing Strategy

The application currently relies on manual integration testing with a live MT5 demo account. Future contributors are encouraged to add:

- **Unit tests** for `calcular_volumen()` and `guardar_vinculo()` (pure functions, no MT5 dependency).
- **Mock-based tests** for `trading.py` using `unittest.mock.patch` to substitute `mt5.*` calls.
- **E2E tests** for the web dashboard using Playwright.
