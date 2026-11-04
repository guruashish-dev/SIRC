// SIRC Frontend Application Logic

let ws = null;

document.addEventListener("DOMContentLoaded", () => {
    connectWebSocket();
    fetchStats();
    fetchIncidents();

    // Poll stats and incidents every 3 seconds as a robust fallback
    setInterval(() => {
        fetchStats();
        fetchIncidents();
    }, 3000);
});

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        appendLog("SYSTEM", "WebSocket telemetry channel successfully connected.");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.message) {
                appendLog(data.level || "INFO", data.message);
            }
        } catch (e) {
            console.error("Failed to parse WS message:", e);
        }
    };

    ws.onclose = () => {
        appendLog("WARN", "WebSocket disconnected. Reconnecting in 3 seconds...");
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket error:", err);
    };
}

async function fetchStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        
        document.getElementById('stat-total').innerText = data.total_incidents;
        document.getElementById('stat-mitigated').innerText = data.mitigated_count;
        document.getElementById('stat-active').innerText = data.active_threats;
        document.getElementById('stat-tps').innerText = data.api_exchange_rate_tps.toFixed(1);
        document.getElementById('stat-tokens').innerText = data.total_tokens_processed.toLocaleString();

        const badge = document.getElementById('ollama-badge');
        const text = document.getElementById('ollama-text');
        const dot = document.getElementById('ollama-dot');
        const ping = document.getElementById('ollama-ping');

        if (data.ollama_status.includes("ONLINE")) {
            dot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500";
            ping.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75";
            text.innerText = `Ollama (${data.model_name}): Online`;
        } else {
            dot.className = "relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500";
            ping.className = "animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75";
            text.innerText = `Ollama: Offline (Fallback AI)`;
        }
    } catch (e) {
        console.error("Error fetching stats:", e);
    }
}

async function fetchIncidents() {
    try {
        const res = await fetch('/api/incidents');
        const incidents = await res.json();
        
        const tbody = document.getElementById('incidents-table-body');
        if (!incidents || incidents.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="px-6 py-8 text-center text-slate-500"><i class="fa-solid fa-shield-check mr-2 text-emerald-500"></i> No security incidents recorded yet. Click 'Simulate Attack' above to test.</td></tr>`;
            return;
        }

        tbody.innerHTML = incidents.map(inc => {
            let badgeClass = "bg-blue-500/10 text-blue-400 border-blue-500/30";
            if (inc.severity === "CRITICAL") badgeClass = "bg-red-500/10 text-red-400 border-red-500/30 animate-pulse";
            else if (inc.severity === "HIGH") badgeClass = "bg-orange-500/10 text-orange-400 border-orange-500/30";
            else if (inc.severity === "MEDIUM") badgeClass = "bg-amber-500/10 text-amber-400 border-amber-500/30";

            return `
                <tr class="hover:bg-dark-700/50 transition-colors border-b border-dark-700/50">
                    <td class="px-6 py-3 font-mono text-xs font-semibold text-cyan-400">${inc.id}</td>
                    <td class="px-6 py-3 text-xs text-slate-400">${new Date(inc.timestamp).toLocaleTimeString()}</td>
                    <td class="px-6 py-3 font-mono text-xs text-slate-300">${inc.source_ip}</td>
                    <td class="px-6 py-3 font-medium text-white">${inc.attack_type}</td>
                    <td class="px-6 py-3">
                        <span class="px-2 py-0.5 rounded text-xs font-bold border ${badgeClass}">${inc.severity}</span>
                    </td>
                    <td class="px-6 py-3 text-slate-300 text-xs" title="${inc.ai_analysis || ''}">
                        <div class="font-medium text-emerald-400"><i class="fa-solid fa-robot mr-1"></i> ${inc.playbook_action || 'Mitigated'}</div>
                        <div class="text-slate-400 truncate max-w-xs mt-0.5">${inc.ai_analysis || ''}</div>
                    </td>
                    <td class="px-6 py-3 text-right font-mono text-xs text-slate-300">${(inc.confidence * 100).toFixed(0)}%</td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Error fetching incidents:", e);
    }
}

async function triggerSimulation(attackType) {
    appendLog("INFO", `Initiating security attack simulation (${attackType})...`);
    try {
        const res = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ attack_type: attackType, count: 1 })
        });
        const data = await res.json();
        fetchStats();
        fetchIncidents();
    } catch (e) {
        appendLog("ERROR", `Failed to trigger simulation: ${e}`);
    }
}

async function clearLogs() {
    if (!confirm("Are you sure you want to clear all security incidents and statistics?")) return;
    try {
        await fetch('/api/clear', { method: 'POST' });
        fetchStats();
        fetchIncidents();
        appendLog("WARN", "Security logs cleared.");
    } catch (e) {
        console.error("Error clearing logs:", e);
    }
}

function clearConsoleLogs() {
    document.getElementById('terminal-logs').innerHTML = `<div class="text-slate-500">[SYSTEM] Console logs cleared.</div>`;
}

function appendLog(level, message) {
    const terminal = document.getElementById('terminal-logs');
    const timeStr = new Date().toLocaleTimeString();
    
    let colorClass = "text-slate-300";
    if (level === "SUCCESS") colorClass = "text-emerald-400";
    else if (level === "WARN") colorClass = "text-amber-400";
    else if (level === "ERROR") colorClass = "text-red-400";
    else if (level === "AI") colorClass = "text-cyan-400";
    else if (level === "SYSTEM") colorClass = "text-purple-400";

    const div = document.createElement('div');
    div.className = colorClass;
    div.innerHTML = `<span class="text-slate-500">[${timeStr}]</span> <span class="font-bold">[${level}]</span> ${escapeHtml(message)}`;
    
    terminal.appendChild(div);
    terminal.scrollTop = terminal.scrollHeight;

    // Limit log rows to 300
    while (terminal.children.length > 300) {
        terminal.removeChild(terminal.firstChild);
    }
}

function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
