/**
 * @fileoverview PropSync Manager — Cloud Dashboard (web_dashboard/app.js)
 *
 * Handles the full lifecycle of the cloud web interface:
 * authentication (Supabase Auth), trade analytics rendering (Chart.js),
 * configuration management (user_configs table), prop firm rule tracking,
 * and network topology visualisation.
 *
 * This file is deployed as a standalone SPA on Netlify.
 * It communicates exclusively with Supabase — there is no Python backend
 * in this deployment mode.
 *
 * @module web_dashboard
 * @version 2.0.0
 * @license MIT
 */

/* ===================================================================
   PropSync Cloud — app.js v2.0
   Enterprise-grade Dashboard Logic
   Stack: Vanilla JS, Chart.js with gradients, Supabase Auth
   =================================================================== */

// --- Supabase Configuration ---
const SUPABASE_URL = 'https://xaaxnfkedtnnxalvifae.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhYXhuZmtlZHRubnhhbHZpZmFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU3Mzg2NDYsImV4cCI6MjA5MTMxNDY0Nn0.9fXrCGze69mlc6tDOe_GFrOxZixqwnMFVUbSGkf9w90';
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// --- State ---
let currentUserEmail = '';
let equityChartInst = null;
let directionChartInst = null;
let symbolChartInst = null;
let clockInterval = null;

let globalCloudConfig = null;
let globalCloudHistorial = null;

// --- CSS custom property reader ---
/**
 * Reads a CSS custom property value from the document root.
 * @param {string} name - The CSS variable name (e.g., '--brand').
 * @returns {string} The trimmed computed value of the CSS variable.
 */
function getCSSVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// --- Cloud Specific Database Sync ---
let cloudFirms = [];

/**
 * Fetches all prop firm records from the Supabase `prop_firms` table
 * and populates the firm selector dropdown in the configuration panel.
 * @async
 * @returns {Promise<void>}
 */
async function fetchCloudPropFirms() {
    const { data, error } = await supabaseClient.from('prop_firms').select('*');
    if (!error && data) {
        cloudFirms = data;
        let html = '<option value="" disabled selected>-- Choose a Firm --</option>';
        data.forEach(function(f) {
            html += '<option value="' + f.id + '">' + f.firm_name + ' (DD: ' + f.max_total_drawdown + '%, Daily: ' + f.max_daily_drawdown + '%)</option>';
        });
        html += '<option value="NEW">+ Add new Prop Firm...</option>';
        const sel = document.getElementById('cm_prop_id');
        if (sel) sel.innerHTML = html;
    }
}

/**
 * Shows or hides the prop firm selector rows based on the account type
 * selected in the master configuration form.
 * @returns {void}
 */
function toggleCloudPropType() {
    const sel = document.getElementById('cm_type');
    const fondeoRow = document.getElementById('fondeo-row-cloud');
    const phaseRow = document.getElementById('phase-row-cloud');
    if (sel.value === 'fondeo') {
        if(fondeoRow) fondeoRow.classList.remove('hidden');
        if(phaseRow) phaseRow.classList.remove('hidden');
        if (cloudFirms.length === 0) fetchCloudPropFirms();
    } else {
        if(fondeoRow) fondeoRow.classList.add('hidden');
        if(phaseRow) phaseRow.classList.add('hidden');
    }
}

/**
 * Checks whether the user selected 'Add new firm' in the prop firm dropdown
 * and opens the new firm modal if so.
 * @returns {void}
 */
function checkCloudNewFirm() {
    const sel = document.getElementById('cm_prop_id');
    if (sel.value === 'NEW') {
        document.getElementById('cloud-prop-firm-modal').classList.remove('hidden');
        sel.value = ''; // Reset so they can click it again if they cancel
    }
}

/**
 * Submits a new prop firm record to Supabase and refreshes the firm dropdown.
 * @async
 * @returns {Promise<void>}
 */
async function submitCloudNewFirm() {
    const name = document.getElementById('cpf_name').value;
    const ddD = parseFloat(document.getElementById('cpf_dd_diario').value);
    const ddT = parseFloat(document.getElementById('cpf_dd_total').value);
    const t1 = parseFloat(document.getElementById('cpf_target_f1').value) || 0;
    const t2 = parseFloat(document.getElementById('cpf_target_f2').value) || 0;
    if (!name) return;

    const { error } = await supabaseClient.from('prop_firms').insert({
        firm_name: name, max_daily_drawdown: ddD, max_total_drawdown: ddT, target_f1: t1, target_f2: t2
    });

    if (!error) {
        document.getElementById('cloud-prop-firm-modal').classList.add('hidden');
        await fetchCloudPropFirms();
    } else {
        alert('Error registering: ' + error.message);
    }
}

/**
 * Fetches the authenticated user's configuration from Supabase,
 * populates the configuration panel form fields, and triggers
 * network tree and prop firm tracker rendering.
 * @async
 * @returns {Promise<void>}
 */
async function fetchUserConfig() {
    await fetchCloudPropFirms();
    const { data, error } = await supabaseClient
        .from('user_configs')
        .select('*')
        .eq('user_email', currentUserEmail);
    if (!error && data && data.length > 0) {
        const conf = JSON.parse(data[0].config_json);
        if(conf.master) {
            document.getElementById('cm_login').value = conf.master.login || '';
            document.getElementById('cm_pass').value = conf.master.password || '';
            document.getElementById('cm_server').value = conf.master.server || '';
            document.getElementById('cm_bal').value = conf.master.initial_balance || '';
            if(conf.master.type) {
                document.getElementById('cm_type').value = conf.master.type;
                if(conf.master.type === 'fondeo') {
                    document.getElementById('cm_prop_id').classList.remove('hidden');
                    const phaseSel = document.getElementById('cm_phase');
                    if(phaseSel) phaseSel.classList.remove('hidden');
                    if(conf.master.prop_firm_id) {
                        document.getElementById('cm_prop_id').value = conf.master.prop_firm_id;
                    }
                    if(conf.master.phase && phaseSel) {
                        phaseSel.value = conf.master.phase;
                    }
                }
            }
        }
        // Render network topology tree in dashboard
        renderCloudTree(conf);
        renderPropFirmTracker(conf);
        globalCloudConfig = conf;
        if (globalCloudConfig && globalCloudHistorial) {
            updateCloudPropMetrics(globalCloudConfig, globalCloudHistorial);
        }
    }
}

/**
 * Builds the HTML markup for prop firm metrics (profit target, daily DD,
 * total DD progress bars) for a single account node.
 * @param {Object} node - The account node config (master or slave).
 * @param {string} nodeKey - The unique key used for DOM element IDs ('master' or slave.id).
 * @returns {string} HTML string for the metrics block, or empty string if not applicable.
 */
function buildCloudPropMetrics(node, nodeKey) {
    if (node.type !== 'fondeo' || !node.prop_firm_id) return '';
    const firm = cloudFirms.find(function(f) { return f.id === node.prop_firm_id; });
    if (!firm) return '';
    const phaseNum  = node.phase || 1;
    const target    = phaseNum === 1 ? firm.target_f1 : (phaseNum === 2 ? firm.target_f2 : 0);
    const phaseText = phaseNum === 3 ? 'Funded Live' : ('Phase ' + phaseNum);
    return '<div class="prop-phase-badge">' + firm.firm_name + ' — ' + phaseText + '</div>' +
        '<div class="prop-metrics-box">' +
            '<div class="prop-progress-row">' +
                '<div class="prop-progress-label"><span>🎯 Target (' + target + '%)</span><span id="pb-val-p-' + nodeKey + '">—</span></div>' +
                '<div class="prop-progress-bg"><div class="prop-progress-fill profit" id="pb-fill-p-' + nodeKey + '" style="width:0%"></div></div>' +
            '</div>' +
            '<div class="prop-progress-row">' +
                '<div class="prop-progress-label"><span>📅 Daily DD (' + firm.max_daily_drawdown + '%)</span><span id="pb-val-dd-daily-' + nodeKey + '">—</span></div>' +
                '<div class="prop-progress-bg"><div class="prop-progress-fill dd-daily" id="pb-fill-dd-daily-' + nodeKey + '" style="width:0%"></div></div>' +
            '</div>' +
            '<div class="prop-progress-row">' +
                '<div class="prop-progress-label"><span>⚠️ Total DD (' + firm.max_total_drawdown + '%)</span><span id="pb-val-dd-' + nodeKey + '">—</span></div>' +
                '<div class="prop-progress-bg"><div class="prop-progress-fill dd" id="pb-fill-dd-' + nodeKey + '" style="width:0%"></div></div>' +
            '</div>' +
        '</div>';
}

/**
 * Renders the network topology tree (master node + slave nodes with SVG connectors)
 * into the `#network-tree-container` element.
 * @param {Object} config - The full app configuration object ({master, slaves}).
 * @returns {void}
 */
function renderCloudTree(config) {
    const treeContainer = document.getElementById('network-tree-container');
    if (!treeContainer) return;

    let treeHtml = '';
    if (config && config.master && config.master.login) {
        const masterFirmHtml = buildCloudPropMetrics(config.master, 'master');

        treeHtml += '<div class="tree-root">' +
            '<h4>[ MASTER NODE ]</h4>' +
            '<h2>ACC: ' + config.master.login + '</h2>' +
            '<div class="tree-sub">Balance: $' + (config.master.initial_balance || '—') + '</div>' +
            masterFirmHtml +
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

            treeHtml += '<svg class="tree-svg-connector" viewBox="0 0 ' + svgW + ' ' + (svgH + 10) + '" style="width:100%;height:' + (svgH + 10) + 'px;max-width:' + svgW + 'px;">' +
                '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L0,8 L8,4 z" fill="rgba(79,142,255,0.8)"/></marker></defs>' +
                svgPaths +
            '</svg>';

            treeHtml += '<div class="tree-branches">';
            config.slaves.forEach(function(s) {
                const slaveFirmHtml = buildCloudPropMetrics(s, s.id);
                treeHtml += '<div class="tree-node-wrapper"><div class="tree-node">' +
                    '<h4><span class="tree-node-status"></span>NODE: ' + s.id + '</h4>' +
                    '<h2>ACC: ' + s.login + '</h2>' +
                    '<span class="node-risk">' + (s.risk_factor || 1.0) + 'x Replication</span>' +
                    slaveFirmHtml +
                '</div></div>';
            });
            treeHtml += '</div>';
        } else {
            treeHtml += '<div style="margin-top:32px;color:var(--text-muted);font-size:13px;text-align:center;padding-bottom:16px;">No slave nodes detected in the cloud configuration.</div>';
        }
    } else {
        treeHtml = '<div style="color:var(--text-muted);padding:40px;text-align:center;font-size:14px;">⚙️ Configure the Master Node in the <strong>Settings</strong> tab to visualize the network topology.</div>';
    }

    treeContainer.innerHTML = treeHtml;
}




/**
 * Saves the master account configuration to Supabase `user_configs`,
 * preserving all existing slave node data.
 * @async
 * @returns {Promise<void>}
 */
async function saveCloudConfig() {
    const typeS = document.getElementById('cm_type').value;
    const propId = document.getElementById('cm_prop_id').value;
    const loginD = parseInt(document.getElementById('cm_login').value);
    const passD = document.getElementById('cm_pass').value;
    const serverD = document.getElementById('cm_server').value;
    const initialB = parseFloat(document.getElementById('cm_bal').value);
    const phaseS = document.getElementById('cm_phase') ? document.getElementById('cm_phase').value : 1;

    let oldConfig = { master: {}, slaves: [] };
    const { data:oldD } = await supabaseClient.from('user_configs').select('config_json').eq('user_email', currentUserEmail);
    if(oldD && oldD.length > 0) oldConfig = JSON.parse(oldD[0].config_json);
    
    oldConfig.master = {
        type: typeS,
        prop_firm_id: typeS === 'fondeo' ? parseInt(propId) : null,
        phase: typeS === 'fondeo' ? parseInt(phaseS) : null,
        login: loginD,
        password: passD,
        server: serverD,
        initial_balance: initialB
    };

    const { error } = await supabaseClient.from('user_configs').upsert({
        user_email: currentUserEmail,
        config_json: JSON.stringify(oldConfig)
    });
    
    if(!error) alert('Cloud Credentials updated successfully.');
    else alert('Error: ' + error.message);
}


/**
 * Renders the full Prop Firm Tracker section with a card per funded account
 * (master and all funded slaves). Cards include profit target and drawdown
 * progress bars that are updated by `updateCloudPropMetrics`.
 * @param {Object} config - The full app configuration object.
 * @returns {void}
 */
function renderPropFirmTracker(config) {
    const section = document.getElementById('prop-firm-tracker-section');
    const grid    = document.getElementById('prop-firm-tracker-grid');
    if (!section || !grid) return;

    // Collect all fondeo nodes
    const nodes = [];
    if (config && config.master && config.master.type === 'fondeo' && config.master.prop_firm_id) {
        nodes.push({ node: config.master, label: 'Master · ACC: ' + config.master.login });
    }
    if (config && config.slaves) {
        config.slaves.forEach(function(s) {
            if (s.type === 'fondeo' && s.prop_firm_id) {
                nodes.push({ node: s, label: s.id + ' · ACC: ' + s.login });
            }
        });
    }

    if (nodes.length === 0) {
        section.classList.remove('hidden');
        grid.innerHTML = '<div style="padding:1rem; opacity:0.6; color:var(--text-muted);">No active evaluated accounts configured.</div>';
        return;
    }
    section.classList.remove('hidden');

    grid.innerHTML = nodes.map(function(item) {
        const n    = item.node;
        let firm = cloudFirms.find(function(f) { return f.id == n.prop_firm_id; });
        if (!firm) {
            firm = { firm_name: "Firm ID " + n.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
        }
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
                        '<span class="lp-tracker-val text-success" id="pft-p-' + nodeKey + '">—</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-profit" id="pft-fill-p-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
                '<div class="lp-tracker-row">' +
                    '<div class="lp-tracker-label">' +
                        '<span>📅 Max Daily Drawdown (' + firm.max_daily_drawdown + '%)</span>' +
                        '<span class="lp-tracker-val text-warning" id="pft-dd-daily-' + nodeKey + '">—</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-daily" id="pft-fill-dd-daily-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
                '<div class="lp-tracker-row">' +
                    '<div class="lp-tracker-label">' +
                        '<span>⚠️ Max Total Drawdown (' + firm.max_total_drawdown + '%)</span>' +
                        '<span class="lp-tracker-val text-danger" id="pft-dd-' + nodeKey + '">—</span>' +
                    '</div>' +
                    '<div class="lp-tracker-bar-bg">' +
                        '<div class="lp-tracker-bar-fill lp-bar-total" id="pft-fill-dd-' + nodeKey + '" style="width:0%"></div>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
    }).join('');
}


/**
 * Updates all Prop Firm Tracker progress bars with current profit and drawdown
 * percentages, calculated from the closed trade history.
 * @param {Object} config - The full app configuration object.
 * @param {Array<Object>} historial - Array of closed trade records from Supabase.
 * @returns {void}
 */
function updateCloudPropMetrics(config, historial) {
    if (!config || !config.master) return;

    const _updateDOM = (idContext, firm, phaseNum, fProfit, fDd) => {
        const target = phaseNum === 1 ? firm.target_f1 : (phaseNum === 2 ? firm.target_f2 : 0);
        const limit  = firm.max_total_drawdown;
        const dLimit = firm.max_daily_drawdown;

        // Daily DD estimation
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

    const calculateStats = (initialBal, riskFactor = 1.0) => {
        // The dashboard historial always comes from the master account.
        const trades = historial;
        let net = 0, peak = 0, maxDD = 0;
        trades.forEach(t => {
            net += parseFloat(t.profit);
            if (net > peak) peak = net;
            let dd = peak - net;
            if (dd > maxDD) maxDD = dd;
        });
        
        const scaledNet = net * riskFactor;
        const scaledMaxDD = maxDD * riskFactor;

        const profitPct = initialBal > 0 ? (scaledNet / initialBal) * 100 : 0;
        const ddPct = initialBal > 0 ? (scaledMaxDD / initialBal) * 100 : 0;
        return { profitPct, ddPct };
    };

    // Master
    if (config.master.type === 'fondeo' && config.master.prop_firm_id) {
        let firm = cloudFirms.find(f => f.id == config.master.prop_firm_id);
        if (!firm) firm = { firm_name: "Firm ID " + config.master.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
        let stats = calculateStats(config.master.initial_balance, 1.0);
        _updateDOM('master', firm, config.master.phase || 1, stats.profitPct, stats.ddPct);
    }

    // Slaves
    if (config.slaves) {
        config.slaves.forEach(s => {
            if (s.type === 'fondeo' && s.prop_firm_id) {
                let firm = cloudFirms.find(f => f.id == s.prop_firm_id);
                if (!firm) firm = { firm_name: "Firm ID " + s.prop_firm_id, target_f1: 8, target_f2: 5, max_daily_drawdown: 5, max_total_drawdown: 10 };
                let riskFactor = parseFloat(s.risk_factor || 1.0);
                let stats = calculateStats(s.initial_balance, riskFactor);
                _updateDOM(s.id, firm, s.phase || 1, stats.profitPct, stats.ddPct);
            }
        });
    }
}


/* ===================================================================
   SECTION 1: AUTHENTICATION
   =================================================================== */

/**
 * Authenticates the user against Supabase Auth and transitions to the dashboard.
 * Displays validation errors and loading states inline.
 * @async
 * @returns {Promise<void>}
 */
async function loginCloud() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const msgLabel = document.getElementById('auth-msg');

    if (!email || !password) {
        msgLabel.className = 'text-warning auth-message';
        msgLabel.innerText = 'Please fill out all fields.';
        return;
    }

    msgLabel.className = 'text-neutral auth-message';
    msgLabel.innerText = 'Authenticating…';

    try {
        const { data, error } = await supabaseClient.auth.signInWithPassword({
            email: email,
            password: password,
        });

        if (error) {
            msgLabel.className = 'text-danger auth-message';
            msgLabel.innerText = 'Error: ' + error.message;
        } else {
            currentUserEmail = data.user.email;
            transitionToDashboard();
        }
    } catch (err) {
        console.error('Critical Failure in Login:', err);
        msgLabel.className = 'text-danger auth-message';
        msgLabel.innerText = 'Connection failure. Check the console (F12).';
    }
}

/**
 * Signs the current user out of Supabase and reloads the page to show the login screen.
 * @async
 * @returns {Promise<void>}
 */
async function logoutCloud() {
    await supabaseClient.auth.signOut();
    if (clockInterval) {
        clearInterval(clockInterval);
        clockInterval = null;
    }
    location.reload();
}

/**
 * Registers a new Supabase account with email/password validation.
 * Switches back to the login tab on success.
 * @async
 * @returns {Promise<void>}
 */
async function registroCloud() {
    const email    = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm  = document.getElementById('reg-confirm').value;
    const msgLabel = document.getElementById('auth-msg');

    if (!email || !password || !confirm) {
        msgLabel.className = 'text-warning auth-message';
        msgLabel.innerText = 'Please fill out all fields.';
        return;
    }
    if (password !== confirm) {
        msgLabel.className = 'text-danger auth-message';
        msgLabel.innerText = 'Passwords do not match.';
        return;
    }
    if (password.length < 6) {
        msgLabel.className = 'text-warning auth-message';
        msgLabel.innerText = 'Password must be at least 6 characters.';
        return;
    }

    msgLabel.className = 'text-neutral auth-message';
    msgLabel.innerText = 'Creating account…';

    try {
        const { data, error } = await supabaseClient.auth.signUp({ email, password });
        if (error) {
            msgLabel.className = 'text-danger auth-message';
            msgLabel.innerText = 'Error: ' + error.message;
        } else {
            msgLabel.className = 'text-success auth-message';
            msgLabel.innerText = '✅ Account created. Check your email to confirm and then login.';
            // Switch back to login tab after 2s
            setTimeout(function() { switchAuthTab('login'); }, 2000);
        }
    } catch (err) {
        msgLabel.className = 'text-danger auth-message';
        msgLabel.innerText = 'Connection failure. Check the console (F12).';
    }
}

/**
 * Switches between the Login and Register panels in the authentication screen.
 * @param {'login'|'register'} tab - The tab identifier to display.
 * @returns {void}
 */
function switchAuthTab(tab) {
    const loginPanel = document.getElementById('auth-panel-login');
    const regPanel   = document.getElementById('auth-panel-register');
    const loginBtn   = document.getElementById('tab-login-btn');
    const regBtn     = document.getElementById('tab-reg-btn');
    const msgLabel   = document.getElementById('auth-msg');
    if (msgLabel) msgLabel.innerText = '';

    if (tab === 'login') {
        if (loginPanel) loginPanel.style.display = '';
        if (regPanel)   regPanel.style.display   = 'none';
        if (loginBtn)   loginBtn.classList.add('active');
        if (regBtn)     regBtn.classList.remove('active');
    } else {
        if (loginPanel) loginPanel.style.display = 'none';
        if (regPanel)   regPanel.style.display   = '';
        if (regBtn)     regBtn.classList.add('active');
        if (loginBtn)   loginBtn.classList.remove('active');
    }
}

/**
 * Animates the transition from the authentication view to the main dashboard.
 * Starts the live clock, shows skeleton loaders, and fetches all cloud data.
 * @returns {void}
 */
function transitionToDashboard() {
    const authView = document.getElementById('auth-view');
    const dashView = document.getElementById('dashboard-view');

    authView.style.opacity = '0';
    authView.style.transition = 'opacity 0.35s ease';

    setTimeout(function () {
        authView.style.display = 'none';
        dashView.style.display = 'flex';
        dashView.style.opacity = '0';
        dashView.style.transition = 'opacity 0.45s ease';

        requestAnimationFrame(function () {
            dashView.style.opacity = '1';
        });

        startClock();
        showSkeletons();
        fetchCloudData();
        fetchUserConfig();
    }, 350);
}


/* ===================================================================
   SECTION 2: SKELETON LOADING STATES
   =================================================================== */

/**
 * Adds CSS skeleton loading classes to all KPI cards and chart boxes
 * while data is being fetched from Supabase.
 * @returns {void}
 */
function showSkeletons() {
    const kpiGrid = document.getElementById('kpi-grid');
    const chartsGrid = document.getElementById('charts-grid');

    // Add skeleton overlays to KPI cards
    const kpiCards = kpiGrid.querySelectorAll('.kpi-card-small');
    kpiCards.forEach(function (card) {
        card.classList.add('skeleton');
    });

    // Add skeleton overlays to chart boxes
    const chartBoxes = chartsGrid.querySelectorAll('.chart-box');
    chartBoxes.forEach(function (box) {
        box.classList.add('skeleton');
    });
}

/**
 * Removes all skeleton loading CSS classes from cards and chart boxes.
 * @returns {void}
 */
function hideSkeletons() {
    document.querySelectorAll('.skeleton').forEach(function (el) {
        el.classList.remove('skeleton');
    });
}

function showLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.remove('hidden');
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    overlay.classList.add('hidden');
}


/* ===================================================================
   SECTION 3: NAVIGATION
   =================================================================== */

/**
 * Switches the visible content tab and updates the top-bar title.
 * @param {string} tabId - The ID of the tab content element to show.
 * @param {HTMLElement|null} btnElement - The nav button element to mark as active.
 * @returns {void}
 */
function mostrarTab(tabId, btnElement) {
    const titleMap = {
        'tab-dash': 'Analytics Dashboard',
        'tab-stats': 'Backtest History',
        'tab-config': 'Network Configuration'
    };

    document.querySelectorAll('.tab-content').forEach(function (t) {
        t.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';

    if (btnElement) {
        document.querySelectorAll('.nav-btn').forEach(function (b) {
            b.classList.remove('active');
        });
        btnElement.classList.add('active');
    }

    // Update top bar title
    const titleEl = document.getElementById('current-tab-title');
    if (titleEl && titleMap[tabId]) {
        titleEl.textContent = titleMap[tabId];
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}


/* ===================================================================
   SECTION 4: LIVE CLOCK
   =================================================================== */

/**
 * Starts the real-time clock in the top navigation bar, updating every second.
 * @returns {void}
 */
function startClock() {
    const clockEl = document.getElementById('top-bar-clock');
    if (!clockEl) return;

    function updateClock() {
        const now = new Date();
        const options = {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        };
        clockEl.textContent = now.toLocaleDateString('en-US', options) + '  ' + now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    }

    updateClock();
    clockInterval = setInterval(updateClock, 1000);
}


/* ===================================================================
   SECTION 5: DATA FETCHING
   =================================================================== */

/**
 * Fetches all closed trade records for the authenticated user from Supabase,
 * computes analytics KPIs (win rate, max drawdown, streaks), updates the
 * trade history table, and renders all three analytics charts.
 * @async
 * @returns {Promise<void>}
 */
async function fetchCloudData() {
    const { data: historial, error } = await supabaseClient
        .from('trades')
        .select('*')
        .eq('user_email', currentUserEmail)
        .order('id', { ascending: true });

    // Remove skeletons after data arrives
    hideSkeletons();

    if (error) {
        console.error('Error fetching data:', error);
        return;
    }
    globalCloudHistorial = historial;

    let netProfit = 0;
    let wins = 0;
    let longs = 0;
    let shorts = 0;
    let assetMap = {};
    let equityCurve = [];
    let currentEquity = 0;
    let htmlTabla = '';

    // Advanced Metrics
    let maxWin = 0, maxLoss = 0;
    let sumWin = 0, sumLoss = 0;
    let currentStreakW = 0, currentStreakL = 0;
    let maxStreakW = 0, maxStreakL = 0;
    let maxDrawdownAbs = 0, peakEquity = 0; 
    let mockInitialBalance = 100000; // Will be properly bound in Phase 3

    historial.forEach(function (op) {
        let pnl = parseFloat(op.profit);
        netProfit += pnl;
        currentEquity += pnl;
        equityCurve.push(currentEquity);

        if (pnl >= 0) {
            wins++;
            if (pnl > maxWin) maxWin = pnl;
            sumWin += pnl;
            currentStreakL = 0;
            currentStreakW++;
            if (currentStreakW > maxStreakW) maxStreakW = currentStreakW;
        } else {
            if (pnl < maxLoss) maxLoss = pnl;
            sumLoss += pnl;
            currentStreakW = 0;
            currentStreakL++;
            if (currentStreakL > maxStreakL) maxStreakL = currentStreakL;
        }

        let simCurrentTotal = mockInitialBalance + currentEquity;
        if (simCurrentTotal > (mockInitialBalance + peakEquity)) peakEquity = currentEquity;
        let currentDD = (mockInitialBalance + peakEquity) - simCurrentTotal;
        if (currentDD > maxDrawdownAbs) maxDrawdownAbs = currentDD;

        let tipoStr = op.type.toUpperCase();
        if (tipoStr === 'BUY') { longs++; } else { shorts++; }

        if (assetMap[op.symbol]) { assetMap[op.symbol]++; }
        else { assetMap[op.symbol] = 1; }

        let colorPnl = pnl >= 0 ? 'text-success' : 'text-danger';
        let colorDir = tipoStr === 'BUY' ? 'var(--brand)' : 'var(--warning)';

        htmlTabla = '<tr>' +
            '<td style="color: var(--text-muted); font-variant-numeric: tabular-nums;">' + op.ticket + '</td>' +
            '<td style="font-weight: 600; color: var(--text-main);">' + op.symbol + '</td>' +
            '<td style="color: ' + colorDir + '; font-weight: 600;">' + tipoStr + '</td>' +
            '<td class="' + colorPnl + '" style="font-weight: 700; font-variant-numeric: tabular-nums;">$' + pnl.toFixed(2) + '</td>' +
            '</tr>' + htmlTabla;
    });

    let totalOps = historial.length;
    let winRate = totalOps > 0 ? (wins / totalOps) * 100 : 0;

    // Update KPI values with animation
    animateKPI('kpi-profit', '$' + netProfit.toFixed(2), netProfit >= 0 ? 'text-success' : 'text-danger');
    animateKPI('kpi-winrate', winRate.toFixed(1) + '%', 'text-neutral');
    animateKPI('kpi-trades', totalOps.toString(), 'text-neutral');

    const kpiMaxWin = document.getElementById('kpi-max-win');
    if (kpiMaxWin) kpiMaxWin.innerText = '$' + maxWin.toFixed(2);
    
    const kpiMaxLoss = document.getElementById('kpi-max-loss');
    if (kpiMaxLoss) kpiMaxLoss.innerText = '$' + maxLoss.toFixed(2);

    const kpiStreakW = document.getElementById('kpi-streak-w');
    if (kpiStreakW) kpiStreakW.innerText = maxStreakW;
    
    const kpiStreakL = document.getElementById('kpi-streak-l');
    if (kpiStreakL) kpiStreakL.innerText = maxStreakL;
    
    const kpiMaxDd = document.getElementById('kpi-max-dd');
    if (kpiMaxDd) {
        let ddPercent = (maxDrawdownAbs / mockInitialBalance) * 100;
        kpiMaxDd.innerText = ddPercent.toFixed(2) + '%';
        if (ddPercent > 10) kpiMaxDd.className = "text-danger";
        else kpiMaxDd.className = "text-warning";
    }

    document.querySelector('#tabla-historial tbody').innerHTML = htmlTabla;

    // Render charts with enhanced gradients
    renderEquityChart(equityCurve, totalOps);
    renderDirectionChart(longs, shorts);
    renderSymbolChart(assetMap);

    if (globalCloudConfig && globalCloudHistorial) {
        updateCloudPropMetrics(globalCloudConfig, globalCloudHistorial);
    }
}

/**
 * Animates a KPI card value with a fade-and-slide-up transition.
 * @param {string} elementId - The DOM ID of the KPI value element.
 * @param {string} value - The formatted string value to display (e.g., '$1,234.56').
 * @param {string} cssClass - The CSS class to apply for colour coding.
 * @returns {void}
 */
function animateKPI(elementId, value, cssClass) {
    const el = document.getElementById(elementId);
    if (!el) return;

    el.style.opacity = '0';
    el.style.transform = 'translateY(6px)';

    setTimeout(function () {
        el.innerText = value;
        el.className = cssClass;
        el.style.transition = 'opacity 0.4s cubic-bezier(0.22,1,0.36,1), transform 0.4s cubic-bezier(0.22,1,0.36,1)';
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
    }, 100);
}


/* ===================================================================
   SECTION 6: CHART.JS CONFIGURATION
   Global defaults for dark theme consistency
   =================================================================== */

Chart.defaults.color = '#64748b';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.weight = 500;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.92)';
Chart.defaults.plugins.tooltip.titleColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.bodyColor = '#94a3b8';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(148, 163, 184, 0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.displayColors = false;
Chart.defaults.plugins.tooltip.titleFont = { weight: 600, size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };


/* ===================================================================
   SECTION 7: EQUITY CHART (Line with Gradient Fill)
   =================================================================== */

/**
 * Renders the equity curve line chart with a gradient fill.
 * Destroys the previous chart instance before creating a new one.
 * @param {number[]} dataPoints - Array of cumulative P&L values.
 * @param {number} totalOps - Total number of closed operations (used for x-axis labels).
 * @returns {void}
 */
function renderEquityChart(dataPoints, totalOps) {
    const ctx = document.getElementById('equityChart');
    if (!ctx) return;

    let labels = Array.from({ length: totalOps }, function (_, i) { return 'Op ' + (i + 1); });
    let isPositive = (dataPoints.length === 0 || dataPoints[dataPoints.length - 1] >= 0);
    let lineColor = isPositive ? '#34d399' : '#f87171';
    let glowColor = isPositive ? 'rgba(52, 211, 153,' : 'rgba(248, 113, 113,';

    // Create gradient
    let context2d = ctx.getContext('2d');
    let gradient = context2d.createLinearGradient(0, 0, 0, ctx.parentElement.clientHeight || 320);
    gradient.addColorStop(0, glowColor + '0.25)');
    gradient.addColorStop(0.5, glowColor + '0.08)');
    gradient.addColorStop(1, glowColor + '0.0)');

    if (equityChartInst) {
        equityChartInst.data.labels = labels;
        equityChartInst.data.datasets[0].data = dataPoints;
        equityChartInst.data.datasets[0].borderColor = lineColor;
        equityChartInst.data.datasets[0].backgroundColor = gradient;
        equityChartInst.update('none');
        return;
    }

    equityChartInst = new Chart(context2d, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Simulated Closed Equity ($)',
                data: dataPoints,
                borderColor: lineColor,
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: lineColor,
                pointHoverBorderColor: '#0b1120',
                pointHoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        title: function (items) {
                            return items[0].label;
                        },
                        label: function (context) {
                            let val = context.parsed.y;
                            let sign = val >= 0 ? '+' : '';
                            return 'Equity: ' + sign + '$' + val.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.06)',
                        drawBorder: false
                    },
                    ticks: {
                        padding: 8,
                        callback: function (value) {
                            return '$' + value.toFixed(0);
                        }
                    },
                    border: { display: false }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        maxTicksLimit: 12,
                        padding: 8
                    },
                    border: { display: false }
                }
            }
        }
    });
}


/* ===================================================================
   SECTION 8: DIRECTION CHART (Doughnut)
   =================================================================== */

function renderDirectionChart(longs, shorts) {
    const ctx = document.getElementById('directionChart');
    if (!ctx || (longs === 0 && shorts === 0)) return;

    const brandColor = '#6395ff';
    const warningColor = '#fbbf24';

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
                backgroundColor: [brandColor, warningColor],
                borderWidth: 0,
                hoverOffset: 6,
                borderRadius: 4,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 10,
                        borderRadius: 3,
                        useBorderRadius: true,
                        padding: 16,
                        font: { size: 12, weight: 500 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            let pct = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' (' + pct + '%)';
                        }
                    }
                }
            }
        }
    });
}


/* ===================================================================
   SECTION 9: SYMBOL CHART (Doughnut)
   =================================================================== */

function renderSymbolChart(assetMap) {
    const ctx = document.getElementById('symbolChart');
    if (!ctx || Object.keys(assetMap).length === 0) return;

    let labels = Object.keys(assetMap);
    let data = Object.values(assetMap);

    // Curated palette — professional & harmonious
    const palette = [
        '#6395ff', // brand blue
        '#34d399', // emerald
        '#a78bfa', // violet
        '#fbbf24', // amber
        '#f87171', // rose
        '#38bdf8', // sky
        '#fb923c', // orange
        '#e879f9'  // fuchsia
    ];

    if (symbolChartInst) {
        symbolChartInst.data.labels = labels;
        symbolChartInst.data.datasets[0].data = data;
        symbolChartInst.data.datasets[0].backgroundColor = palette.slice(0, labels.length);
        symbolChartInst.update('none');
        return;
    }

    symbolChartInst = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: palette.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 6,
                borderRadius: 4,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        boxHeight: 10,
                        borderRadius: 3,
                        useBorderRadius: true,
                        padding: 16,
                        font: { size: 12, weight: 500 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            let pct = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' ops (' + pct + '%)';
                        }
                    }
                }
            }
        }
    });
}


/* ===================================================================
   SECTION 10: KEYBOARD SHORTCUT — Enter to Login
   =================================================================== */

document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
        const authView = document.getElementById('auth-view');
        if (authView && authView.style.display !== 'none') {
            loginCloud();
        }
    }
});


/* ===================================================================
   SECTION 11: LANDING PAGE PUBLIC PREVIEW
   =================================================================== */

// Toggle Dropdown for Login
function toggleAuthDropdown() {
    const btn = document.querySelector('.lp-btn-access');
    const dropdown = document.getElementById('auth-dropdown');
    if (!btn || !dropdown) return;
    
    btn.classList.toggle('open');
    dropdown.classList.toggle('hidden');
}

// Close Dropdown correctly when clicking outside
document.addEventListener('click', function(e) {
    const wrapper = document.querySelector('.lp-auth-dropdown-wrapper');
    if (wrapper && !wrapper.contains(e.target)) {
        const btn = document.querySelector('.lp-btn-access');
        const dropdown = document.getElementById('auth-dropdown');
        if (btn && dropdown) {
            btn.classList.remove('open');
            dropdown.classList.add('hidden');
        }
    }
});

let demoChartInst = null;

async function loadLandingDemo() {
    try {
        const response = await fetch('mapa_operaciones.json');
        if (!response.ok) return;
        const data = await response.json();
        
        // 1. Populate KPIs
        const elProfit = document.getElementById('dk-profit');
        if(elProfit) elProfit.textContent = `$${data.kpis.net_profit.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        
        const elWinrate = document.getElementById('dk-winrate');
        if(elWinrate) elWinrate.textContent = `${data.kpis.win_rate}%`;
        
        const elTrades = document.getElementById('dk-trades');
        if(elTrades) elTrades.textContent = data.kpis.total_trades;
        
        const elDD = document.getElementById('dk-dd');
        if(elDD) elDD.textContent = `${data.kpis.max_drawdown_pct}%`;
        
        const elPF = document.getElementById('dk-pf');
        if(elPF) elPF.textContent = data.kpis.profit_factor;
        
        // 2. Progress bar calculation
        const initialBal = data.meta.initial_balance || 100000;
        const profitVal  = data.kpis.net_profit;
        const profitPct  = (profitVal / initialBal) * 100;
        
        const targetPctLimit = data.meta.target_profit_pct || 8.0;
        const targetProgress = Math.min((profitPct / targetPctLimit) * 100, 100);

        // Daily DD Simulation (just for demo aesthetic if not in JSON)
        const dailyDDVal = 1.12; // Simulated current 1.12% drawdown today
        const maxDailyLimit = data.meta.max_daily_dd_pct || 5.0;
        const dailyProgress = Math.min((dailyDDVal / maxDailyLimit) * 100, 100);

        // Total DD
        const totalDDVal = data.kpis.max_drawdown_pct || 0;
        const maxTotalLimit = data.meta.max_total_dd_pct || 10.0;
        const totalProgress = Math.min((totalDDVal / maxTotalLimit) * 100, 100);
        
        // Update elements
        const elTargetVal = document.getElementById('dk-target-val');
        const elTargetFill = document.getElementById('dk-target-fill');
        if (elTargetVal) elTargetVal.textContent = (profitVal >= 0 ? '+' : '') + profitPct.toFixed(2) + '%';
        if (elTargetFill) elTargetFill.style.width = targetProgress + '%';

        const elDDDailyVal = document.getElementById('dk-dd-daily');
        const elDDDailyFill = document.getElementById('dk-dd-daily-fill');
        if (elDDDailyVal) elDDDailyVal.textContent = dailyDDVal.toFixed(2) + '%';
        if (elDDDailyFill) elDDDailyFill.style.width = dailyProgress + '%';

        const elDDTotalVal = document.getElementById('dk-dd-total');
        const elDDTotalFill = document.getElementById('dk-dd-total-fill');
        if (elDDTotalVal) elDDTotalVal.textContent = totalDDVal.toFixed(2) + '%';
        if (elDDTotalFill) elDDTotalFill.style.width = totalProgress + '%';
        
        // 3. Populate Mini Trades Table
        const tbody = document.getElementById('demo-trades-body');
        if (tbody) {
            tbody.innerHTML = '';
            data.trades.forEach(t => {
                let isProfit = t.profit >= 0;
                let colorClass = isProfit ? 'text-success' : 'text-danger';
                let sign = isProfit ? '+' : '';
                tbody.innerHTML += `
                    <tr>
                        <td style="color:var(--text-muted)">#${t.ticket}</td>
                        <td style="font-weight:600">${t.symbol}</td>
                        <td>
                            <span style="font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600; background:rgba(255,255,255,0.05)">${t.type}</span>
                        </td>
                        <td class="${colorClass}" style="font-weight:bold">${sign}$${Math.abs(t.profit).toFixed(2)}</td>
                    </tr>
                `;
            });
        }
        
        // 4. Render demo equity chart using Chart.js
        const ctx = document.getElementById('demo-equity-chart');
        if (ctx) {
            if (demoChartInst) demoChartInst.destroy();
            
            // Generate glowing gradient for line
            let gradBg = ctx.getContext('2d').createLinearGradient(0, 0, 0, 220);
            gradBg.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
            gradBg.addColorStop(1, 'rgba(16, 185, 129, 0.0)');
            
            demoChartInst = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.equity_curve.map((_, i) => i),
                    datasets: [{
                        label: 'Profit ($)',
                        data: data.equity_curve,
                        borderColor: '#10b981',
                        backgroundColor: gradBg,
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        tension: 0.35
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(9, 14, 31, 0.95)',
                            titleColor: '#94a3b8',
                            bodyColor: '#10b981',
                            borderColor: 'rgba(148, 163, 184, 0.2)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: function(context) {
                                    return '$' + context.parsed.y.toLocaleString(undefined, {minimumFractionDigits: 2});
                                },
                                title: function(contexts) {
                                    return 'Trade #' + contexts[0].label;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: {
                            display: true,
                            position: 'right',
                            grid: { color: 'rgba(148, 163, 184, 0.05)', drawBorder: false },
                            border: { display: false },
                            ticks: {
                                color: '#94a3b8',
                                font: { size: 11, family: "'Inter', sans-serif" },
                                callback: function(value) {
                                    return '$' + value;
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Error loading / parsing mapa_operaciones.json:", err);
    }
}

// Automatically load demo preview if auth-view is currently visible
document.addEventListener("DOMContentLoaded", () => {
    const authView = document.getElementById('auth-view');
    if (authView && authView.style.display !== 'none') {
        loadLandingDemo();
    }
});