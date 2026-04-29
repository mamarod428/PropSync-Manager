# Security Guide — PropSync Manager

This document describes the threat model, implemented security controls, known limitations, and recommended hardening steps for PropSync Manager.

---

## 1. Threat Model

PropSync Manager handles **live financial credentials** (MetaTrader 5 broker logins and passwords) and **cloud authentication tokens** (Supabase). The primary threats are:

| Threat | Likelihood | Impact |
|---|---|---|
| Credentials exposed in version control | **High** (if gitignore misconfigured) | Critical |
| Credentials leaked via local disk read | Medium | High |
| Man-in-the-middle on MT5 broker connection | Low | High |
| Supabase RLS misconfiguration | Medium | High |
| Unauthorised local process access | Low | Medium |

---

## 2. Implemented Controls

### 2.1 Base64 credential obfuscation

Broker account passwords are encoded with Base64 before being written to `data/credenciales.json`:

```python
# modules/config.py
def codificar(texto: str) -> str:
    return base64.b64encode(texto.encode('utf-8')).decode('utf-8')
```

**Limitation:** Base64 is encoding, not encryption. It prevents casual plaintext exposure but is trivially reversible. See §4 for the recommended upgrade.

### 2.2 Secrets separated from code

Cloud credentials (`SUPABASE_URL`, `SUPABASE_KEY`) are stored in `secrets.json` at the project root, which is listed in `.gitignore`. This file is never committed.

### 2.3 Supabase keys never exposed to the frontend via static files

The web_local interface does not hardcode any Supabase credentials. Instead, the `BridgeAPI.obtener_claves_js()` method passes them from the Python process to JavaScript at runtime:

```python
def obtener_claves_js(self):
    return {"url": URL_NUBE, "key": KEY_NUBE}
```

### 2.4 Trade deviation guard

Every `order_send` request includes `"deviation": 20` (20 points of maximum slippage). If the market price moves more than 20 points between the moment the order is constructed and when the broker receives it, the broker rejects the order. This prevents execution at dramatically different prices during high-volatility events.

### 2.5 Gitignore protection

The `.gitignore` file explicitly blocks:
- `secrets.json`
- `data/credenciales.json`
- `data/mapa_operaciones.json`
- `data/historial_operaciones.json`

---

## 3. Supabase Row-Level Security (RLS) Recommendations

The Supabase tables (`trades`, `user_configs`, `prop_firms`) should have RLS policies enforced. Recommended policies:

### `trades` table
```sql
-- Users can only see their own trades
CREATE POLICY "Users see own trades"
ON trades FOR SELECT
USING (user_email = auth.jwt() ->> 'email');

-- Users can only insert their own trades
CREATE POLICY "Users insert own trades"
ON trades FOR INSERT
WITH CHECK (user_email = auth.jwt() ->> 'email');
```

### `user_configs` table
```sql
CREATE POLICY "Users manage own config"
ON user_configs FOR ALL
USING (user_email = auth.jwt() ->> 'email')
WITH CHECK (user_email = auth.jwt() ->> 'email');
```

> **Note:** Without RLS, any authenticated user can read all other users' trade history and configurations. Always enable RLS in production.

---

## 4. Recommended Security Upgrades

### 4.1 Replace Base64 with OS Keyring

**Current:** `base64.b64encode(password)`  
**Recommended:** Use the [`keyring`](https://pypi.org/project/keyring/) library to store credentials in the OS-native secure storage (Windows Credential Manager):

```python
import keyring

# Save
keyring.set_password("propsync", account_login, password)

# Load
password = keyring.get_password("propsync", account_login)
```

This makes credentials inaccessible to any process other than the authenticated OS user.

### 4.2 Validate all inputs from the JavaScript bridge

The `BridgeAPI` methods receive data directly from the web frontend. Consider adding schema validation (e.g., with `pydantic` or simple type checks) before consuming values:

```python
def guardar_maestra(self, datos_master: dict):
    assert isinstance(datos_master.get("login"), (str, int)), "Invalid login"
    assert isinstance(datos_master.get("server"), str), "Invalid server"
    ...
```

### 4.3 Transport security for MT5

MetaTrader 5 communicates with brokers over the broker's proprietary encrypted protocol. No additional transport-level changes are needed at the application layer. Ensure you use brokers with TLS-enabled trading servers.

### 4.4 Audit logging

Consider adding a structured audit log (separate from the operational log) that records:
- Login events (success/failure)
- Account switches
- Every `order_send` call with its result code

---

## 5. Responsible Disclosure

If you discover a security vulnerability in PropSync Manager, please **do not open a public GitHub issue**. Instead, contact the maintainer directly via GitHub private message with a description of the vulnerability and steps to reproduce it. We aim to respond within 5 business days.
