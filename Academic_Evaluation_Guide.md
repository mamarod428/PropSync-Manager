# PropSync Manager - Academic Evaluation Guide

## 1. Project Overview
**PropSync Manager** is an open-source Robotic Process Automation (RPA) tool built to synchronize high-frequency trading operations between a Master MetaTrader 5 account and multiple Slave accounts. It is designed to assist prop-firm traders in managing capital securely across distributed Edge nodes with a unified Cloud Dashboard.

## 2. Cloud Dashboard Access (Live Demo)
A cloud-hosted version of the analytic dashboard is available to review the telemetry and UI localization without running the python engine locally.

1. Navigate to the live web application (e.g., hosted on Netlify).
2. Use the following demo credentials:
   - **Email:** `admin@admin.com`
   - **Password:** `pass@123`
3. The dashboard will connect to the Supabase backend and render the simulated trading history, metrics, and network topology.

## 3. Local Engine Setup (Python / PyWebView)
To evaluate the local Edge Engine execution and view the PyWebView interface, please follow these steps:

### Prerequisites:
- **OS:** Windows 10/11 (Required for MetaTrader 5 integration).
- **Python:** 3.10 or higher.
- **MetaTrader 5 Terminal:** Installed and running.

### Initialization Steps:
1. Extract the project repository and open a terminal in the root directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **API Keys Configuration:** 
   Please create a file named `secrets.json` in the root folder of the project.
   Paste the Supabase API keys provided securely via the academic submission portal:
   ```json
   {
       "SUPABASE_URL": "YOUR_SUPABASE_URL_HERE",
       "SUPABASE_KEY": "YOUR_SUPABASE_KEY_HERE"
   }
   ```
4. **Demo Trading Credentials:**
   The repository includes a set of pre-configured demo credentials in `data/credenciales.json` allowing the system to boot and simulate connection states. These are strictly demo accounts with paper money.
5. Launch the application:
   ```bash
   python main.py
   ```

## 4. Evaluation Context
- **Localization:** The entire project has been fully localized to English, ensuring professional presentation for international academic review.
- **Fault Tolerance:** The engine features isolated node architecture. If an incorrect MT5 credential is provided, the specific node is isolated and marked with a failure, but the master engine continues to operate reliably.
- **Data Persistence:** Operational state is cached locally in RAM and periodically flushed to disk, while user configurations and metrics are synced via REST API to Supabase.

*This guide was generated to facilitate the grading process of Project 3.*
