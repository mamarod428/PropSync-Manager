let equityChartInst = null;
let directionChartInst = null;
let symbolChartInst = null;
let telemetriaInterval = null;

window.log_sys = function(mensaje) {
    const consola = document.getElementById('system-console');
    if(consola) {
        consola.value += mensaje + "\n";
        consola.scrollTop = consola.scrollHeight;
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
        msgLabel.innerText = "Credenciales requeridas para acceso.";
        return;
    }

    msgLabel.className = "text-neutral auth-message";
    msgLabel.innerText = "Estableciendo conexion segura...";

    const resultado = await window.pywebview.api.conectar(email, password);
    
    if (resultado.status === "success") {
        document.getElementById('auth-view').style.display = 'none';
        document.getElementById('dashboard-view').style.display = 'flex';
        
        const statusBadge = document.getElementById('sys-status');
        statusBadge.innerText = "ENLACE OT ACTIVO";
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
        msgLabel.innerText = "Cuenta aprovisionada con exito.";
    } else {
        msgLabel.className = "text-danger auth-message";
        msgLabel.innerText = "Fallo de registro: " + resultado.message;
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

    if (tabId === 'tab-config') cargarConfiguracionEnUI();
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
                    <button onclick="eliminarEsclava('${s.id}')" style="background:rgba(218, 54, 51, 0.1); color:var(--danger); border: 1px solid var(--danger); padding:6px 12px; border-radius:6px; cursor:pointer; font-size: 12px;">Desacoplar</button>
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
        risk_factor: parseFloat(document.getElementById('s_risk').value)
    };
    await window.pywebview.api.guardar_esclava(datos);
    
    document.getElementById('s_id').value = '';
    document.getElementById('s_login').value = '';
    document.getElementById('s_pass').value = '';
    document.getElementById('s_server').value = '';
    cargarConfiguracionEnUI(); 
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

    // Actualizar KPIs Flotantes (Live)
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
    renderNodeBalances(config, netProfit, flotante.profit);
}

function renderNodeBalances(config, netProfit, floatingProfit) {
    const grid = document.getElementById('node-balances-grid');
    if(!grid || !config) return;
    
    let html = "";
    
    if(config.master && config.master.initial_balance) {
        let masterBal = parseFloat(config.master.initial_balance);
        let totalMasterProfit = netProfit + floatingProfit;
        let masterSimEq = masterBal + totalMasterProfit;
        html += `<div class="node-card master">
            <h4>[Origen] Master</h4>
            <h2 class="${totalMasterProfit >= 0 ? 'text-success' : 'text-danger'}">$${masterSimEq.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
            <p style="color: var(--text-muted); font-size: 11px; margin-top: 5px;">P/L Total:$${totalMasterProfit.toFixed(2)} | Base: $${masterBal.toLocaleString()}</p>
        </div>`;
    }

    if(config.slaves) {
        config.slaves.forEach(s => {
            let baseBal = parseFloat(s.initial_balance);
            let factor = parseFloat(s.risk_factor || 1.0);
            let totalSlaveProfit = (netProfit + floatingProfit) * factor;
            let simEq = baseBal + totalSlaveProfit;
            
            html += `<div class="node-card">
                <h4>[Destino] ${s.id}</h4>
                <h2 class="${totalSlaveProfit >= 0 ? 'text-success' : 'text-danger'}">$${simEq.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
                <p style="color: var(--text-muted); font-size: 11px; margin-top: 5px;">P/L Total: $${totalSlaveProfit.toFixed(2)} | Riesgo: ${factor}x</p>
            </div>`;
        });
    }
    
    grid.innerHTML = html;
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
                label: 'Equidad Simulada Cerrada ($)',
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
        
        btn.innerText = "Encender Sistema";
        btn.className = "btn-primary"; // Lo volvemos azul
        
        statusBadge.innerText = "SISTEMA DETENIDO";
        statusBadge.style.background = "rgba(218, 54, 51, 0.1)";
        statusBadge.style.borderColor = "var(--danger)";
        statusBadge.style.color = "var(--danger)";
        log_sys("[SISTEMA] Motor detenido por el usuario.");
    } else {
        // Encender
        const res = await window.pywebview.api.encender_motor();
        if (res === "ok") {
            motorActivo = true;
            btn.innerText = "Apagar Sistema";
            btn.className = "btn-logout"; // Lo volvemos rojo
            
            statusBadge.innerText = "ENLACE OT ACTIVO";
            statusBadge.style.background = "rgba(35, 134, 54, 0.1)";
            statusBadge.style.borderColor = "var(--success)";
            statusBadge.style.color = "var(--success)";
        } else {
            alert("Error al arrancar el motor. Verifica tu terminal MT5.");
        }
    }
}