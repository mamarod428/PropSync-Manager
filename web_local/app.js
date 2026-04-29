let equityChartInst = null;
let directionChartInst = null;
let symbolChartInst = null;
let telemetriaInterval = null;

let logLineElements = [];
let currentLogFilter = 'ALL';
let editandoSlaveId = null; 
let editandoSlaveStartPnl = 0; 
let masterNetProfitAtStart = null; 
let masterNetProfitTotal = 0; 
let masterFloatingProfit = 0; 

// Cache de prop firms cargadas desde Supabase
let supabaseFirms = [];


window.log_sys = function(mensaje) {
    const consola = document.getElementById('system-console');
    if(!consola) return;
    
    const match = mensaje.match(/^\[(.*?)\]\s+\[(.*?)\]\s+(.*)/);
    
    let timeStr = "";
    let badgeStr = "INFO";
    let msgBody = mensaje;
    let badgeClass = "log-info";

    if (match) {
        timeStr = match[1];
        badgeStr = match[2];
        msgBody = match[3];
    } else {
        const timeMatch = mensaje.match(/^\[(.*?)\]\s+(.*)/);
        if (timeMatch) {
            timeStr = timeMatch[1];
            msgBody = timeMatch[2];
        }
    }

    const badgeStrUpper = badgeStr.toUpperCase();
    if (badgeStrUpper.includes("ERROR") || badgeStrUpper.includes("FALLO")) badgeClass = "log-error";
    else if (badgeStrUpper.includes("WARN")) badgeClass = "log-warn";
    else if (badgeStrUpper.includes("EXITO") || badgeStrUpper.includes("CRED")) badgeClass = "log-cred";
    else if (badgeStrUpper.includes("ACCION") || badgeStrUpper.includes("MODIFICACION") || badgeStrUpper.includes("CIERRE")) badgeClass = "log-accion";
    else if (badgeStrUpper.includes("NUBE")) badgeClass = "log-nube";
    else if (badgeStrUpper.includes("SISTEMA") || badgeStrUpper.includes("LIMPIEZA")) badgeClass = "log-sistem";

    const logEl = document.createElement('div');
    logEl.className = 'log-line';
    logEl.dataset.type = badgeStrUpper;
    
    let html = '';
    if (timeStr) html += `<span class="log-time">[${timeStr}]</span>`;
    html += `<span class="log-badge ${badgeClass}">${badgeStr}</span>`;
    html += `<span class="log-msg">${msgBody}</span>`;
    
    logEl.innerHTML = html;
    
    if (currentLogFilter !== 'ALL' && currentLogFilter !== badgeStrUpper && !badgeStrUpper.includes(currentLogFilter)) {
        logEl.style.display = 'none';
    }
    
    consola.appendChild(logEl);
    logLineElements.push(logEl);
    
    // Keep max 200 lines to avoid DOM lag
    if (logLineElements.length > 200) {
        let oldEl = logLineElements.shift();
        if (oldEl && oldEl.parentNode) oldEl.parentNode.removeChild(oldEl);
    }
    
    consola.scrollTop = consola.scrollHeight;
};

window.filtrarLogs = function(tipo) {
    currentLogFilter = tipo;
    document.querySelectorAll('.terminal-filter-btn').forEach(b => {
        if (b.innerText === tipo) b.classList.add('active');
        else b.classList.remove('active');
    });
    
    logLineElements.forEach(el => {
        if (tipo === 'ALL' || el.dataset.type.includes(tipo)) {
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    });
};

window.limpiarConsola = function() {
    const consola = document.getElementById('system-console');
    if(consola) consola.innerHTML = '';
    logLineElements = [];
};

window.exportarLogs = async function() {
    let text = "";
    logLineElements.forEach(el => {
        text += el.innerText + "\n";
    });
    if(!text) {
        log_sys("[ERROR] No hay logs para exportar.");
        return;
    }
    
    // Usamos el bridge de Python para un guardado nativo mas robusto
    const res = await window.pywebview.api.guardar_logs_en_archivo(text);
    if(res.status === 'error') {
        log_sys("[ERROR] Fallo al exportar logs: " + res.message);
    }
};

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

async function loginLocal() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const msgLabel = document.getElementById('auth-msg');
    
    if(!email || !password) {
        msgLabel.className = "text-warning auth-message";
        msgLabel.innerText = "Credentials required for access.";
        return;
    }

    msgLabel.className = "text-neutral auth-message";
    msgLabel.innerText = "Establishing secure connection...";

    const resultado = await window.pywebview.api.conectar(email, password);
    
    if (resultado.status === "success") {
        document.getElementById('auth-view').style.display = 'none';
        document.getElementById('dashboard-view').style.display = 'flex';
        
        const statusBadge = document.getElementById('sys-status');
        statusBadge.innerText = "OT LINK ACTIVE";
        statusBadge.style.background = "rgba(35, 134, 54, 0.1)";
        statusBadge.style.borderColor = "var(--success)";
        statusBadge.style.color = "var(--success)";
        
        mostrarTab('tab-dash', document.querySelector('.nav-btn'));
        iniciarTelemetria(); 
    } else {
        msgLabel.className = "text-danger auth-message";
        msgLabel.innerText = "Error: " + resultado.message;
    }
}

async function registroLocal() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const msgLabel = document.getElementById('auth-msg');
    
    const resultado = await window.pywebview.api.registrar(email, password);
    
    if (resultado.status === "success") {
        msgLabel.className = "text-success auth-message";
        msgLabel.innerText = "Account provisioned successfully.";
    } else {
        msgLabel.className = "text-danger auth-message";
        msgLabel.innerText = "Registration failed: " + resultado.message;
    }
}

async function cerrarSesionLocal() {
    await window.pywebview.api.apagar_motor();
    window.close();
}

function mostrarTab(tabId, btnElement) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.getElementById(tabId).style.display = 'block';

    if(btnElement) {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
        document.getElementById('current-tab-title').innerText = btnElement.innerText;
    }

    if (tabId === 'tab-config') {
        cargarConfiguracionEnUI();
        cargarPropFirms();
    }
}

/* ===================================================================
   PROP FIRMS — SUPABASE INTEGRATION
   =================================================================== */

async function cargarPropFirms() {
    const listDiv = document.getElementById('prop-firms-list');
    if (listDiv) listDiv.innerHTML = '<p style="color:var(--text-muted); font-size:13px; padding:12px 0;">Syncing with Supabase...</p>';
    
    try {
        const firms = await window.pywebview.api.db_get_prop_firms();
        if (firms && firms.length > 0) {
            supabaseFirms = firms;
        } else {
            supabaseFirms = [
                { id: 'ftmo-default', firm_name: 'FTMO', target_f1: 10, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 },
                { id: 'fn-default', firm_name: 'FundedNext', target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 },
                { id: 'mff-default', firm_name: 'MyForexFunds', target_f1: 8, target_f2: 5, max_daily_drawdown: 4, max_total_drawdown: 8 },
            ];
        }
    } catch(e) {
        supabaseFirms = [
            { id: 'ftmo-default', firm_name: 'FTMO', target_f1: 10, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 },
        ];
    }
    
    poblarSelectorFirm('m_prop_id', supabaseFirms);
    poblarSelectorFirm('s_prop_id', supabaseFirms);
    renderPropFirmsList(supabaseFirms);
}

function poblarSelectorFirm(selectId, firms) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const valorActual = sel.value;
    sel.innerHTML = '';
    firms.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.firm_name;
        sel.appendChild(opt);
    });
    if (valorActual) sel.value = valorActual;
}

function filtrarSelectorFirm(selectId, query) {
    const filtradas = supabaseFirms.filter(f => f.firm_name.toLowerCase().includes(query.toLowerCase()));
    poblarSelectorFirm(selectId, filtradas);
}

function renderPropFirmsList(firms) {
    const listDiv = document.getElementById('prop-firms-list');
    if (!listDiv) return;
    if (firms.length === 0) {
        listDiv.innerHTML = '<p style="color:var(--text-muted); font-size:13px;">Sin datos. Sin conexion a Supabase o base vacia.</p>';
        return;
    }
    listDiv.innerHTML = firms.map(f => `
        <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 10px 14px; font-size: 12px; flex-shrink:0;">
            <div style="font-weight: 700; color: var(--text-main); margin-bottom: 4px;">🏦 ${f.firm_name}</div>
            <div style="color: var(--text-muted); line-height:1.8;">
                DD Diario: <span style="color:var(--warning)">${f.max_daily_drawdown}%</span> ·
                DD Total: <span style="color:var(--danger)">${f.max_total_drawdown}%</span><br>
                Obj. F1: <span style="color:var(--success)">${f.target_f1}%</span> ·
                Obj. F2: <span style="color:var(--success)">${f.target_f2}%</span>
            </div>
        </div>
    `).join('');
}

function onTipoChange(selectEl, propIdSelectorId, phaseId) {
    const val = selectEl.value;
    const propWrapId = propIdSelectorId + '_wrap';
    const propWrap = document.getElementById(propWrapId);
    const phaseEl = document.getElementById(phaseId);
    
    if (val === 'fondeo') {
        if (propWrap) propWrap.classList.remove('hidden');
        if (phaseEl) phaseEl.classList.remove('hidden');
        poblarSelectorFirm(propIdSelectorId, supabaseFirms);
    } else {
        if (propWrap) propWrap.classList.add('hidden');
        if (phaseEl) phaseEl.classList.add('hidden');
    }
}

function togglePanelNuevaPropFirm() {
    const panel = document.getElementById('panel-nueva-prop-firm');
    if (panel) panel.classList.toggle('hidden');
}

async function guardarNuevaPropFirm() {
    const name = document.getElementById('pf_name').value.trim();
    const dd_daily = parseFloat(document.getElementById('pf_dd_daily').value);
    const dd_total = parseFloat(document.getElementById('pf_dd_total').value);
    const target_f1 = parseFloat(document.getElementById('pf_target_f1').value);
    const target_f2 = parseFloat(document.getElementById('pf_target_f2').value);
    const msg = document.getElementById('prop-firm-msg');
    
    if (!name || isNaN(dd_daily) || isNaN(dd_total) || isNaN(target_f1) || isNaN(target_f2)) {
        msg.className = 'text-danger';
        msg.innerText = 'All fields are required.';
        return;
    }
    
    msg.className = 'text-neutral';
    msg.innerText = 'Publishing to Supabase...';
    
    const resultado = await window.pywebview.api.db_add_prop_firm({
        firm_name: name,
        max_daily_drawdown: dd_daily,
        max_total_drawdown: dd_total,
        target_f1: target_f1,
        target_f2: target_f2
    });
    
    if (resultado.status === 'success') {
        msg.className = 'text-success';
        msg.innerText = '✓ ' + name + ' registered successfully.';
        document.getElementById('pf_name').value = '';
        document.getElementById('pf_dd_daily').value = '';
        document.getElementById('pf_dd_total').value = '';
        document.getElementById('pf_target_f1').value = '';
        document.getElementById('pf_target_f2').value = '';
        await cargarPropFirms();
    } else {
        msg.className = 'text-danger';
        msg.innerText = 'Error: ' + (resultado.message || 'Failed to contact Supabase.');
    }
}

function getFirmsCache() {
    return supabaseFirms.length > 0 ? supabaseFirms : [
        { id: 1, firm_name: 'FTMO', target_f1: 10, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 },
        { id: 2, firm_name: 'FundedNext', target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 }
    ];
}


async function cargarConfiguracionEnUI() {
    const config = await window.pywebview.api.obtener_configuracion();
    
    if(config.master) {
        document.getElementById('m_login').value = config.master.login || '';
        document.getElementById('m_pass').value = config.master.password || '';
        document.getElementById('m_server').value = config.master.server || '';
        document.getElementById('m_bal').value = config.master.initial_balance || '';
    }

    const tbody = document.querySelector('#tabla-esclavas tbody');
    tbody.innerHTML = '';
    
    if(config.slaves) {
        config.slaves.forEach(s => {
            let row = `<tr>
                <td style="font-weight: 600; color: var(--text-main);">${s.id}</td>
                <td style="color: var(--text-muted);">${s.login}</td>
                <td style="color: var(--success);">$${s.initial_balance}</td>
                <td style="color: var(--warning); font-weight: bold;">${s.risk_factor}x</td>
                <td>
                    <div style="display:flex; gap:6px;">
                        <button onclick="editNode('${s.id}')" style="background:rgba(79, 142, 255, 0.1); color:var(--brand); border: 1px solid var(--brand); padding:6px 12px; border-radius:6px; cursor:pointer; font-size: 12px;">Edit</button>
                        <button onclick="eliminarEsclava('${s.id}')" style="background:rgba(218, 54, 51, 0.1); color:var(--danger); border: 1px solid var(--danger); padding:6px 12px; border-radius:6px; cursor:pointer; font-size: 12px;">Detach</button>
                    </div>
                </td>
            </tr>`;
            tbody.innerHTML += row;
        });
    }
}

async function guardarMaestra() {
    const datos = {
        login: parseInt(document.getElementById('m_login').value),
        password: document.getElementById('m_pass').value,
        server: document.getElementById('m_server').value,
        initial_balance: parseFloat(document.getElementById('m_bal').value)
    };
    await window.pywebview.api.guardar_maestra(datos);
}

async function guardarEsclava() {
    const id = document.getElementById('s_id').value;
    if(!id) return;

    const datos = {
        id: id,
        login: parseInt(document.getElementById('s_login').value),
        password: document.getElementById('s_pass').value,
        server: document.getElementById('s_server').value,
        initial_balance: parseFloat(document.getElementById('s_bal').value),
        risk_factor: parseFloat(document.getElementById('s_risk').value),
        start_pnl: (editandoSlaveId) ? editandoSlaveStartPnl : (masterNetProfitTotal + masterFloatingProfit) 
    };
    await window.pywebview.api.guardar_esclava(datos);
    
    document.getElementById('s_id').value = '';
    document.getElementById('s_id').readOnly = false;
    document.getElementById('s_login').value = '';
    document.getElementById('s_pass').value = '';
    document.getElementById('s_server').value = '';
    document.getElementById('s_bal').value = '';
    document.getElementById('s_risk').value = '';
    
    editandoSlaveId = null;
    document.getElementById('slave-form-title').innerText = "Add Target Node (Slave)";
    document.getElementById('btn-save-slave').innerText = "Attach Node to Network";
    document.getElementById('btn-cancel-edit').classList.add('hidden');
    
    cargarConfiguracionEnUI(); 
}

function editNode(slaveId) {
    window.pywebview.api.obtener_configuracion().then(config => {
        const s = config.slaves.find(x => x.id === slaveId);
        if(!s) return;
        
        mostrarTab('tab-config', document.querySelectorAll('.nav-btn')[2]); 
        
        editandoSlaveId = slaveId;
        editandoSlaveStartPnl = s.start_pnl || 0;
        document.getElementById('slave-form-title').innerText = "Modify Node: " + slaveId;
        document.getElementById('btn-save-slave').innerText = "Update Node Configuration";
        document.getElementById('btn-cancel-edit').classList.remove('hidden');
        
        document.getElementById('s_id').value = s.id;
        document.getElementById('s_id').readOnly = true; 
        document.getElementById('s_login').value = s.login;
        document.getElementById('s_pass').value = s.password || '';
        document.getElementById('s_server').value = s.server || '';
        document.getElementById('s_bal').value = s.initial_balance;
        document.getElementById('s_risk').value = s.risk_factor;
        
        if(s.type) document.getElementById('s_type').value = s.type;
        if(s.prop_firm_id) {
            const propSelect = document.getElementById('s_prop_id');
            propSelect.value = s.prop_firm_id;
            propSelect.classList.remove('hidden');
        }
    });
}

function cancelarEdicion() {
    editandoSlaveId = null;
    document.getElementById('slave-form-title').innerText = "Add Target Node (Slave)";
    document.getElementById('btn-save-slave').innerText = "Attach Node to Network";
    document.getElementById('btn-cancel-edit').classList.add('hidden');
    
    document.getElementById('s_id').value = '';
    document.getElementById('s_id').readOnly = false;
    document.getElementById('s_login').value = '';
    document.getElementById('s_pass').value = '';
    document.getElementById('s_server').value = '';
    document.getElementById('s_bal').value = '';
    document.getElementById('s_risk').value = '';
}

async function eliminarEsclava(id_borrar) {
    await window.pywebview.api.eliminar_esclava(id_borrar);
    cargarConfiguracionEnUI();
}

function iniciarTelemetria() {
    if (telemetriaInterval) clearInterval(telemetriaInterval);
    telemetriaInterval = setInterval(actualizarDashboard, 2000);
    actualizarDashboard();
}

async function actualizarDashboard() {
    const datos = await window.pywebview.api.obtener_telemetria();
    const config = await window.pywebview.api.obtener_configuracion();
    
    if (!datos) return;
    
    let historial = datos.historial || [];
    let flotante = datos.flotante || { equity: 0, balance: 0, profit: 0 };

    let netProfit = 0, grossProfit = 0, grossLoss = 0;
    let wins = 0;
    let longs = 0, shorts = 0;
    let assetMap = {}; 
    let equityCurve = [];
    let currentEquity = 0;
    let htmlTabla = "";

    historial.forEach((op) => {
        let pnl = parseFloat(op.profit);
        netProfit += pnl;
        currentEquity += pnl;
        equityCurve.push(currentEquity);

        if (pnl >= 0) { wins++; grossProfit += pnl; }
        else { grossLoss += Math.abs(pnl); }

        if (op.type.toUpperCase() === "BUY") longs++;
        else shorts++;

        if (assetMap[op.symbol]) assetMap[op.symbol]++;
        else assetMap[op.symbol] = 1;

        let colorPnl = pnl >= 0 ? "text-success" : "text-danger";
        let dirStr = op.type.toUpperCase();
        let colorDir = dirStr === "BUY" ? "var(--brand)" : "var(--warning)";

        htmlTabla = `<tr>
            <td style="color: var(--text-muted);">${op.ticket}</td>
            <td style="font-weight: 600; color: var(--text-main);">${op.symbol}</td>
            <td style="color: ${colorDir}; font-weight: bold;">${dirStr}</td>
            <td class="${colorPnl}" style="font-weight: bold;">$${pnl.toFixed(2)}</td>
        </tr>` + htmlTabla; 
    });

    let totalOps = historial.length;
    let profitFactor = grossLoss > 0 ? (grossProfit / grossLoss) : grossProfit;
    let winRate = totalOps > 0 ? (wins / totalOps) * 100 : 0;

    masterNetProfitTotal = netProfit;
    masterFloatingProfit = flotante.profit;
    
    if (masterNetProfitAtStart === null) {
        masterNetProfitAtStart = netProfit;
    }

    const kpiBal = document.getElementById('kpi-balance');
    if(kpiBal) kpiBal.innerText = `$${flotante.balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const kpiEq = document.getElementById('kpi-equity');
    if(kpiEq) kpiEq.innerText = `$${flotante.equity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const kpiFloatPnl = document.getElementById('kpi-floating-pnl');
    if(kpiFloatPnl) {
        kpiFloatPnl.innerText = `$${flotante.profit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        kpiFloatPnl.className = flotante.profit >= 0 ? "text-success" : "text-danger";
    }

    // Actualizar KPIs Cerrados
    const profitEl = document.getElementById('kpi-profit');
    if(profitEl) {
        profitEl.innerText = `$${netProfit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        profitEl.className = netProfit >= 0 ? "text-success" : "text-danger";
    }
    
    const wrEl = document.getElementById('kpi-winrate');
    if(wrEl) {
        wrEl.innerText = `${winRate.toFixed(1)}%`;
        wrEl.className = winRate >= 50 ? "text-success" : (winRate > 0 ? "text-warning" : "text-danger");
    }

    const pfEl = document.getElementById('kpi-pf');
    if(pfEl) {
        pfEl.innerText = profitFactor.toFixed(2);
        pfEl.className = profitFactor >= 1.5 ? "text-success" : (profitFactor >= 1.0 ? "text-warning" : "text-danger");
    }

    const opsEl = document.getElementById('kpi-trades');
    if(opsEl) opsEl.innerText = totalOps;

    const gProfEl = document.getElementById('kpi-gross-profit');
    if(gProfEl) gProfEl.innerText = `$${grossProfit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const gLossEl = document.getElementById('kpi-gross-loss');
    if(gLossEl) gLossEl.innerText = `$${grossLoss.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const tbody = document.querySelector('#tabla-historial tbody');
    if(tbody) tbody.innerHTML = htmlTabla;

    renderEquityChart(equityCurve, totalOps);
    renderDirectionChart(longs, shorts);
    renderSymbolChart(assetMap);
    
    // We need peak equity to pass to the prop metrics updater
    let peakEquity = flotante.balance;
    let tempEq = flotante.balance;
    historial.forEach(op => {
        tempEq += parseFloat(op.profit);
        if (tempEq > peakEquity) peakEquity = tempEq;
    });
    // Consider current floating in peak if it exceeds
    if (flotante.equity > peakEquity) peakEquity = flotante.equity;

    renderNodeBalances(config, netProfit, flotante.profit, flotante.balance, flotante.equity);
    
    renderNetworkTree(config);
    renderLocalPropFirmTracker(config);
    updateLocalPropMetrics(config, historial, flotante, peakEquity);

    // NUEVO: Calcular Capital Total Gestionado
    let totalEquity = flotante.equity;
    if(config.slaves) {
        config.slaves.forEach(s => {
            let baseBal = parseFloat(s.initial_balance);
            let factor = parseFloat(s.risk_factor || 1.0);
            
            // Lógica Sesión-Base: Solo sumamos beneficio generado desde que se abrió el motor
            let sessionPnl = (netProfit - masterNetProfitAtStart); 
            let slaveEq = baseBal + ((sessionPnl + flotante.profit) * factor);
            totalEquity += slaveEq;
        });
    }
    const kpiTotalCap = document.getElementById('kpi-total-capital');
    if(kpiTotalCap) kpiTotalCap.innerText = `$${totalEquity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

function renderNodeBalances(config, netProfit, floatingProfit, realMasterBalance, realMasterEquity) {
    const grid = document.getElementById('node-balances-grid');
    if(!grid || !config) return;
    
    let html = "";
    
    if(config.master && config.master.initial_balance) {
        let baseBal = parseFloat(config.master.initial_balance);
        let masterEq = realMasterEquity || (baseBal + netProfit + floatingProfit);
        let totalMasterProfit = netProfit + floatingProfit;
        html += `<div class="node-card master">
            <h4>[Source] Master</h4>
            <h2 class="${totalMasterProfit >= 0 ? 'text-success' : 'text-danger'}">$${masterEq.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
            <p style="color: var(--text-muted); font-size: 11px; margin-top: 5px;">Total P/L: $${totalMasterProfit.toFixed(2)} | Base Balance: $${baseBal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
        </div>`;
    }

    if(config.slaves) {
        config.slaves.forEach(s => {
            let baseBal = parseFloat(s.initial_balance);
            let factor = parseFloat(s.risk_factor || 1.0);
            
            let sessionPnl = (netProfit - (masterNetProfitAtStart || netProfit));
            let currentPnl = sessionPnl + floatingProfit;
            let slaveEq = baseBal + (currentPnl * factor);
            let totalSlaveProfit = (currentPnl * factor);
            
            html += `<div class="node-card">
                <h4>[Target] ${s.id}</h4>
                <h2 class="${totalSlaveProfit >= 0 ? 'text-success' : 'text-danger'}">$${slaveEq.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
                <p style="color: var(--text-muted); font-size: 11px; margin-top: 5px;">Session P/L: $${totalSlaveProfit.toFixed(2)} | Base Balance: $${baseBal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
            </div>`;
        });
    }
    
    grid.innerHTML = html;
}

/* ===================================================================
   NETWORK TOPOLOGY TREE (Local)
   =================================================================== */
function renderNetworkTree(config) {
    const treeContainer = document.getElementById('network-tree-container');
    if (!treeContainer) return;

    let treeHtml = '';
    if (config && config.master && config.master.login) {
        treeHtml += '<div class="tree-root">' +
            '<h4>[ MASTER NODE ]</h4>' +
            '<h2>ACC: ' + config.master.login + '</h2>' +
            '<div class="tree-sub">Balance: $' + (config.master.initial_balance || '-') + '</div>' +
        '</div>';

        if (config.slaves && config.slaves.length > 0) {
            const slaveCount  = config.slaves.length;
            const svgW        = Math.max(slaveCount * 280, 300);
            const svgH        = 60;
            const centerX     = svgW / 2;
            const vertLen     = 28;
            const groupY      = svgH - 2;
            const slaveSpacing = svgW / slaveCount;
            const slaveXs     = config.slaves.map(function(_, i) { return slaveSpacing * i + slaveSpacing / 2; });

            let svgPaths = '';
            svgPaths += '<line class="tree-connector-line" x1="' + centerX + '" y1="0" x2="' + centerX + '" y2="' + vertLen + '"/>';
            svgPaths += '<line class="tree-connector-animated" x1="' + centerX + '" y1="0" x2="' + centerX + '" y2="' + vertLen + '" style="animation-delay:0s"/>';

            if (slaveCount > 1) {
                const barLeft  = Math.min.apply(null, slaveXs);
                const barRight = Math.max.apply(null, slaveXs);
                svgPaths += '<line class="tree-connector-line" x1="' + barLeft + '" y1="' + vertLen + '" x2="' + barRight + '" y2="' + vertLen + '"/>';
            }

            slaveXs.forEach(function(sx, i) {
                const delay = (i * 0.4).toFixed(1);
                svgPaths += '<line class="tree-connector-line" x1="' + sx + '" y1="' + vertLen + '" x2="' + sx + '" y2="' + groupY + '"/>';
                svgPaths += '<line class="tree-connector-animated" x1="' + sx + '" y1="' + vertLen + '" x2="' + sx + '" y2="' + groupY + '" style="animation-delay:' + delay + 's"/>';
                svgPaths += '<polygon class="tree-connector-arrowhead" points="' + sx + ',' + (groupY + 8) + ' ' + (sx - 5) + ',' + groupY + ' ' + (sx + 5) + ',' + groupY + '"/>';
            });

            treeHtml += '<svg class="tree-svg-connector" viewBox="0 0 ' + svgW + ' ' + (svgH + 10) + '" style="width:100%; height:' + (svgH + 10) + 'px; max-width:' + svgW + 'px;">' +
                '<defs>' +
                    '<marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">' +
                        '<path d="M0,0 L0,8 L8,4 z" fill="rgba(79,142,255,0.8)"/>' +
                    '</marker>' +
                '</defs>' +
                svgPaths +
            '</svg>';

            treeHtml += '<div class="tree-branches">';
            config.slaves.forEach(function(s) {
                treeHtml += '<div class="tree-node-wrapper">' +
                    '<div class="tree-node">' +
                        '<h4><span class="tree-node-status"></span>NODE: ' + s.id + '</h4>' +
                        '<h2>ACC: ' + s.login + '</h2>' +
                        '<span class="node-risk">' + (s.risk_factor || 1.0) + 'x Replication</span>' +
                    '</div>' +
                '</div>';
            });
            treeHtml += '</div>';
        } else {
            treeHtml += '<div style="margin-top:32px; color:var(--text-muted); font-size:13px; text-align:center; padding-bottom:16px;">' +
                'No slave nodes connected to the logical network.' +
            '</div>';
        }
    } else {
        treeHtml = '<div style="color:var(--danger); padding:20px;">Master node is not configured. Topology is inoperative.</div>';
    }
    treeContainer.innerHTML = treeHtml;
}

/* ===================================================================
   PROP FIRM TRACKER (Local)
   =================================================================== */

// Demo firms for local tracking if backend is unavailable
const localFirms = [
    { id: 1, firm_name: "FTMO", target_f1: 10, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 },
    { id: 2, firm_name: "FundedNext", target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 }
];

function renderLocalPropFirmTracker(config) {
    const section = document.getElementById('prop-firm-tracker-section');
    const grid    = document.getElementById('prop-firm-tracker-grid');
    if (!section || !grid) return;

    const nodes = [];
    if (config && config.master && config.master.type === 'fondeo' && config.master.prop_firm_id) {
        nodes.push({ node: config.master, label: 'Master · ACC: ' + config.master.login });
    }
    if (config && config.slaves) {
        config.slaves.forEach(s => {
            if (s.type === 'fondeo' && s.prop_firm_id) {
                nodes.push({ node: s, label: 'Slave (' + s.id + ') · ACC: ' + s.login });
            }
        });
    }

    if (nodes.length === 0) {
        section.classList.add('hidden');
        return;
    }
    section.classList.remove('hidden');

    grid.innerHTML = nodes.map(item => {
        const n = item.node;
        const firms = getFirmsCache();
        let firm = firms.find(f => String(f.id) === String(n.prop_firm_id) || f.firm_name === n.prop_firm_id);
        if (!firm) firm = { firm_name: "Firma ID " + n.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
        
        const phaseNum  = n.phase || 1;
        const target    = phaseNum === 1 ? firm.target_f1 : (phaseNum === 2 ? firm.target_f2 : 0);
        const phaseText = phaseNum === 3 ? 'Funded' : 'Phase ' + phaseNum;
        const nodeKey   = n.id || 'master';
        
        return '<div class="lp-demo-tracker-card">' +
            '<div class="lp-demo-tracker-header">' +
                '<div class="lp-demo-tracker-badge">' +
                    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' +
                    firm.firm_name + ' · ' + phaseText +
                '</div>' +
                '<span style="font-size:11px; font-weight:700; color:var(--text-muted); background:rgba(255,255,255,0.05); padding:4px 8px; border-radius:4px; letter-spacing:0.5px;">' + item.label + '</span>' +
            '</div>' +
            '<div class="lp-demo-tracker-rows">' +
                '<div class="lp-tracker-row">' +
                    '<div class="lp-tracker-label">' +
                        '<span>🎯 Profit Target (' + target + '%)</span>' +
                        '<span class="lp-tracker-val text-success" id="pft-p-' + nodeKey + '">-</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-profit" id="pft-fill-p-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
                '<div class="lp-tracker-row">' +
                    '<div class="lp-tracker-label">' +
                        '<span>📅 Max Daily Drawdown (' + firm.max_daily_drawdown + '%)</span>' +
                        '<span class="lp-tracker-val text-warning" id="pft-dd-daily-' + nodeKey + '">-</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-daily" id="pft-fill-dd-daily-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
                '<div class="lp-tracker-row">' +
                    '<div class="lp-tracker-label">' +
                        '<span>⚠️ Max Total Drawdown (' + firm.max_total_drawdown + '%)</span>' +
                        '<span class="lp-tracker-val text-danger" id="pft-dd-' + nodeKey + '">-</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-total" id="pft-fill-dd-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
    }).join('');
}

function updateLocalPropMetrics(config, historial, flotante, peakEquity) {
    if (!config || !config.master) return;

    const _updateDOM = (idContext, firm, phaseNum, fProfit, fDd) => {
        const target = phaseNum === 1 ? firm.target_f1 : (phaseNum === 2 ? firm.target_f2 : 0);
        const limit  = firm.max_total_drawdown;
        const dLimit = firm.max_daily_drawdown;
        
        const fDaily = fDd * 0.42; 

        const pVal = document.getElementById(`pft-p-${idContext}`);
        const pFill = document.getElementById(`pft-fill-p-${idContext}`);
        if (pFill && pVal) {
            let pp = target > 0 ? Math.max(0, (fProfit / target) * 100) : 100;
            pFill.style.width = Math.min(pp, 100) + "%";
            pVal.innerText = (fProfit >= 0 ? '+' : '') + fProfit.toFixed(2) + "%";
        }

        const dVal = document.getElementById(`pft-dd-${idContext}`);
        const dFill = document.getElementById(`pft-fill-dd-${idContext}`);
        if (dFill && dVal) {
            let dp = limit > 0 ? Math.max(0, (fDd / limit) * 100) : 0;
            dFill.style.width = Math.min(dp, 100) + "%";
            dVal.innerText = fDd.toFixed(2) + "%";
        }

        const dailyVal = document.getElementById(`pft-dd-daily-${idContext}`);
        const dailyFill = document.getElementById(`pft-fill-dd-daily-${idContext}`);
        if (dailyFill && dailyVal) {
            let ddp = dLimit > 0 ? Math.max(0, (fDaily / dLimit) * 100) : 0;
            dailyFill.style.width = Math.min(ddp, 100) + "%";
            dailyVal.innerText = fDaily.toFixed(2) + "%";
        }
    };

    const calculateStats = (nodeConfig) => {
        let net = 0;
        historial.forEach(t => { net += parseFloat(t.profit); });
        
        let initialBal = parseFloat(nodeConfig.initial_balance);
        let riskFactor = parseFloat(nodeConfig.risk_factor || 1.0);

        let currentEquity = flotante.equity;
        let dd = 0;
        if (peakEquity > 0 && currentEquity < peakEquity) {
            dd = peakEquity - currentEquity;
        }

        // Beneficio Sesión: Solo lo capturado desde el inicio del programa
        const sessionNet = net + flotante.profit - (masterNetProfitAtStart || (net + flotante.profit));

        const scaledNet = sessionNet * riskFactor;
        const scaledDD = dd * riskFactor;

        const profitPct = initialBal > 0 ? (scaledNet / initialBal) * 100 : 0;
        const ddPct = initialBal > 0 ? (scaledDD / initialBal) * 100 : 0;
        return { profitPct, ddPct };
    };

    if (config.master.type === 'fondeo' && config.master.prop_firm_id) {
        const firms = getFirmsCache();
        let firm = firms.find(f => String(f.id) === String(config.master.prop_firm_id) || f.firm_name === config.master.prop_firm_id);
        if (!firm) firm = { firm_name: "Firm ID " + config.master.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
        let stats = calculateStats(config.master);
        _updateDOM('master', firm, config.master.phase || 1, stats.profitPct, stats.ddPct);
    }

    if (config.slaves) {
        config.slaves.forEach(s => {
            if (s.type === 'fondeo' && s.prop_firm_id) {
                const firms = getFirmsCache();
                let firm = firms.find(f => String(f.id) === String(s.prop_firm_id) || f.firm_name === s.prop_firm_id);
                if (!firm) firm = { firm_name: "Firm ID " + s.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
                let stats = calculateStats(s);
                _updateDOM(s.id, firm, s.phase || 1, stats.profitPct, stats.ddPct);
            }
        });
    }
}

Chart.defaults.color = '#8B949E';
Chart.defaults.font.family = "'Inter', sans-serif";

function renderEquityChart(dataPoints, totalOps) {
    const ctx = document.getElementById('equityChart');
    if (!ctx) return;
    let labels = Array.from({length: totalOps}, (_, i) => i + 1);
    let colorFondo = (dataPoints[dataPoints.length-1] >= 0 || dataPoints.length === 0) ? '#238636' : '#DA3633';

    if (equityChartInst) {
        equityChartInst.data.labels = labels;
        equityChartInst.data.datasets[0].data = dataPoints;
        equityChartInst.data.datasets[0].borderColor = colorFondo;
        equityChartInst.data.datasets[0].backgroundColor = colorFondo + '20';
        equityChartInst.update('none');
        return;
    }

    equityChartInst = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Closed Simulated Equity ($)',
                data: dataPoints,
                borderColor: colorFondo,
                backgroundColor: colorFondo + '20',
                borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1, pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: {
                y: { grid: { color: '#30363D', drawBorder: false } },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderDirectionChart(longs, shorts) {
    const ctx = document.getElementById('directionChart');
    if (!ctx || (longs === 0 && shorts === 0)) return;

    if (directionChartInst) {
        directionChartInst.data.datasets[0].data = [longs, shorts];
        directionChartInst.update('none');
        return;
    }

    directionChartInst = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Longs (Buy)', 'Shorts (Sell)'],
            datasets: [{
                data: [longs, shorts],
                backgroundColor: ['#2F81F7', '#D29922'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '75%',
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 15 } } }
        }
    });
}

function renderSymbolChart(assetMap) {
    const ctx = document.getElementById('symbolChart');
    if (!ctx || Object.keys(assetMap).length === 0) return;

    let labels = Object.keys(assetMap);
    let data = Object.values(assetMap);
    let colors = ['#238636', '#2F81F7', '#8957E5', '#D29922', '#DA3633', '#00B4D8', '#F43F5E'];

    if (symbolChartInst) {
        symbolChartInst.data.labels = labels;
        symbolChartInst.data.datasets[0].data = data;
        symbolChartInst.update('none');
        return;
    }

    symbolChartInst = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '75%',
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 15 } } }
        }
    });
}

let motorActivo = true;

async function toggleMotor() {
    const btn = document.getElementById('btn-toggle-motor');
    const statusBadge = document.getElementById('sys-status');
    
    if (motorActivo) {
        // Apagar
        await window.pywebview.api.apagar_motor();
        motorActivo = false;
        
        btn.innerText = "Start System";
        btn.className = "btn-primary"; // Turn blue
        
        statusBadge.innerText = "SYSTEM STOPPED";
        statusBadge.style.background = "rgba(218, 54, 51, 0.1)";
        statusBadge.style.borderColor = "var(--danger)";
        statusBadge.style.color = "var(--danger)";
        log_sys("[SYSTEM] Engine stopped by user.");
    } else {
        // Encender
        const res = await window.pywebview.api.encender_motor();
        if (res === "ok") {
            motorActivo = true;
            btn.innerText = "Shutdown System";
            btn.className = "btn-logout"; // Turn red
            
            statusBadge.innerText = "OT LINK ACTIVE";
            statusBadge.style.background = "rgba(35, 134, 54, 0.1)";
            statusBadge.style.borderColor = "var(--success)";
            statusBadge.style.color = "var(--success)";
        } else {
            alert("Error starting the engine. Check your MT5 terminal.");
        }
    }
}