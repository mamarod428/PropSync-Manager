const SUPABASE_URL = 'https://xaaxnfkedtnnxalvifae.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhYXhuZmtlZHRubnhhbHZpZmFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3Mzg2NDYsImV4cCI6MjA5MTMxNDY0Nn0.9fXrCGze69mlc6tDOe_GFrOxZixqwnMFVUbSGkf9w90';
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

let currentUserEmail = "";
let equityChartInst = null;
let directionChartInst = null;
let symbolChartInst = null;

async function loginCloud() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const msgLabel = document.getElementById('auth-msg');
    
    msgLabel.innerText = "Autenticando...";
    
    const { data, error } = await supabase.auth.signInWithPassword({
        email: email,
        password: password,
    });

    if (error) {
        msgLabel.className = "text-danger auth-message";
        msgLabel.innerText = "Credenciales incorrectas.";
    } else {
        currentUserEmail = data.user.email;
        document.getElementById('auth-view').style.display = 'none';
        document.getElementById('dashboard-view').style.display = 'flex';
        
        // Descargar datos iniciales
        fetchCloudData();
        // Opcional: setInterval(fetchCloudData, 5000); para refrescar cada 5s
    }
}

async function logoutCloud() {
    await supabase.auth.signOut();
    location.reload(); // Recarga la página para limpiar memoria
}

function mostrarTab(tabId, btnElement) {
    document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
    document.getElementById(tabId).style.display = 'block';
    if(btnElement) {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
    }
}

async function fetchCloudData() {
    // Descargar solo los trades de este usuario
    const { data: historial, error } = await supabase
        .from('trades')
        .select('*')
        .eq('user_email', currentUserEmail)
        .order('id', { ascending: true });

    if (error) {
        console.error("Error obteniendo datos:", error);
        return;
    }

    let netProfit = 0;
    let wins = 0, longs = 0, shorts = 0;
    let assetMap = {}; 
    let equityCurve = [];
    let currentEquity = 0;
    let htmlTabla = "";

    historial.forEach((op) => {
        let pnl = parseFloat(op.profit);
        netProfit += pnl;
        currentEquity += pnl;
        equityCurve.push(currentEquity);

        if (pnl >= 0) wins++;
        
        let tipoStr = op.type.toUpperCase();
        if (tipoStr === "BUY") longs++; else shorts++;

        if (assetMap[op.symbol]) assetMap[op.symbol]++;
        else assetMap[op.symbol] = 1;

        let colorPnl = pnl >= 0 ? "text-success" : "text-danger";
        let colorDir = tipoStr === "BUY" ? "var(--brand)" : "var(--warning)";

        htmlTabla = `<tr>
            <td style="color: var(--text-muted);">${op.ticket}</td>
            <td style="font-weight: 600; color: var(--text-main);">${op.symbol}</td>
            <td style="color: ${colorDir}; font-weight: bold;">${tipoStr}</td>
            <td class="${colorPnl}" style="font-weight: bold;">$${pnl.toFixed(2)}</td>
        </tr>` + htmlTabla; 
    });

    let totalOps = historial.length;
    let winRate = totalOps > 0 ? (wins / totalOps) * 100 : 0;

    document.getElementById('kpi-profit').innerText = `$${netProfit.toFixed(2)}`;
    document.getElementById('kpi-profit').className = netProfit >= 0 ? "text-success" : "text-danger";
    document.getElementById('kpi-winrate').innerText = `${winRate.toFixed(1)}%`;
    document.getElementById('kpi-trades').innerText = totalOps;
    document.querySelector('#tabla-historial tbody').innerHTML = htmlTabla;

    renderEquityChart(equityCurve, totalOps);
    renderDirectionChart(longs, shorts);
    renderSymbolChart(assetMap);
}

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
                label: 'Equidad ($)', data: dataPoints, borderColor: colorFondo, backgroundColor: colorFondo + '20', borderWidth: 2, fill: true, tension: 0.3, pointRadius: 1
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { grid: { color: '#30363D' } }, x: { grid: { display: false } } } }
    });
}

function renderDirectionChart(longs, shorts) {
    const ctx = document.getElementById('directionChart');
    if (!ctx || (longs === 0 && shorts === 0)) return;
    if (directionChartInst) { directionChartInst.data.datasets[0].data = [longs, shorts]; directionChartInst.update('none'); return; }
    directionChartInst = new Chart(ctx.getContext('2d'), {
        type: 'doughnut', data: { labels: ['Longs', 'Shorts'], datasets: [{ data: [longs, shorts], backgroundColor: ['#2F81F7', '#D29922'], borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: { legend: { position: 'bottom' } } }
    });
}

function renderSymbolChart(assetMap) {
    const ctx = document.getElementById('symbolChart');
    if (!ctx || Object.keys(assetMap).length === 0) return;
    let labels = Object.keys(assetMap), data = Object.values(assetMap), colors = ['#238636', '#2F81F7', '#8957E5', '#D29922', '#DA3633', '#00B4D8'];
    if (symbolChartInst) { symbolChartInst.data.labels = labels; symbolChartInst.data.datasets[0].data = data; symbolChartInst.update('none'); return; }
    symbolChartInst = new Chart(ctx.getContext('2d'), {
        type: 'doughnut', data: { labels: labels, datasets: [{ data: data, backgroundColor: colors.slice(0, labels.length), borderWidth: 0 }] },
        options: { responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: { legend: { position: 'bottom' } } }
    });
}