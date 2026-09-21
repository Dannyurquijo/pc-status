// PC Status Mobile Web Dashboard Client App

let serverUrl = localStorage.getItem('pc_status_server_url') || '';
let currentAction = null; // { type: 'kill' | 'restart' | 'shutdown' | 'stop', payload: {} }
let pollTimer = null;
let lastProcessesList = [];
let isUserInteractingWithTable = false;

document.addEventListener('DOMContentLoaded', () => {
  initUI();
  startPolling();
});

function getApiBaseUrl() {
  if (serverUrl && serverUrl.trim() !== '') {
    return serverUrl.replace(/\/+$/, '');
  }
  return window.location.origin;
}

function initUI() {
  const btnConfig = document.getElementById('btn-config');
  const configBanner = document.getElementById('config-banner');
  const serverInput = document.getElementById('server-url-input');
  const btnSaveConfig = document.getElementById('btn-save-config');
  
  serverInput.value = serverUrl;

  btnConfig.addEventListener('click', () => {
    configBanner.classList.toggle('hidden');
  });

  btnSaveConfig.addEventListener('click', () => {
    serverUrl = serverInput.value.trim();
    localStorage.setItem('pc_status_server_url', serverUrl);
    configBanner.classList.add('hidden');
    fetchTelemetry();
  });

  // Table Interaction Pause Listeners
  const tableContainer = document.getElementById('process-table-container');
  tableContainer.addEventListener('touchstart', () => { isUserInteractingWithTable = true; }, { passive: true });
  tableContainer.addEventListener('touchend', () => { setTimeout(() => { isUserInteractingWithTable = false; }, 3000); });
  tableContainer.addEventListener('mouseenter', () => { isUserInteractingWithTable = true; });
  tableContainer.addEventListener('mouseleave', () => { isUserInteractingWithTable = false; });

  // Process Search Input Listener
  const searchInput = document.getElementById('proc-search-input');
  searchInput.addEventListener('input', () => {
    renderProcesses(lastProcessesList);
  });

  document.getElementById('btn-refresh-procs').addEventListener('click', () => {
    isUserInteractingWithTable = false;
    fetchProcesses();
  });

  document.getElementById('btn-emergency-shutdown').addEventListener('click', () => {
    openPinModal({
      type: 'shutdown',
      text: '¿Estás seguro de APAGAR remotamente la PC de emergencia? (Tendrás 30 segundos para cancelar)'
    });
  });

  document.getElementById('btn-stop-agent').addEventListener('click', () => {
    openPinModal({
      type: 'stop',
      text: '¿Deseas deshabilitar/pausar el agente de monitoreo remoto?'
    });
  });

  document.getElementById('btn-modal-cancel').addEventListener('click', closePinModal);
  document.getElementById('btn-modal-confirm').addEventListener('click', executeModalAction);
}

function startPolling() {
  fetchTelemetry();
  pollTimer = setInterval(fetchTelemetry, 2500);
}

async function fetchTelemetry() {
  const baseUrl = getApiBaseUrl();
  const connStatus = document.getElementById('connection-status');

  try {
    const res = await fetch(`${baseUrl}/api/status`);
    if (!res.ok) throw new Error('HTTP Error ' + res.status);
    const json = await res.json();
    
    if (json.success && json.data) {
      updateDashboard(json.data);
      connStatus.className = 'status-badge online';
      connStatus.innerHTML = '<i class="fa-solid fa-circle pulse-dot"></i> Conectado';
    }
  } catch (err) {
    connStatus.className = 'status-badge offline';
    connStatus.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Sin Conexión';
    console.warn('Error al obtener telemetría:', err);
  }
}

function updateDashboard(data) {
  if (data.hostname) document.getElementById('hostname-display').innerText = data.hostname;
  if (data.uptime) document.getElementById('system-uptime').innerText = data.uptime;

  if (data.cpu) {
    const cpuPct = Math.round(data.cpu.percent || 0);
    document.getElementById('cpu-percent').innerText = `${cpuPct}%`;
    document.getElementById('cpu-gauge').style.setProperty('--percent', cpuPct);
    document.getElementById('cpu-cores').innerText = `${data.cpu.count || '--'} Cores`;
    document.getElementById('cpu-freq').innerText = data.cpu.freq_mhz ? `${data.cpu.freq_mhz} MHz` : '--';

    const tempBadge = document.getElementById('cpu-temp-badge');
    if (data.cpu.temp_c !== null && data.cpu.temp_c !== undefined) {
      const temp = data.cpu.temp_c;
      tempBadge.innerText = `${temp} °C`;
      tempBadge.className = 'temp-badge';
      if (temp > 80) tempBadge.classList.add('critical');
      else if (temp > 65) tempBadge.classList.add('warning');
    } else {
      tempBadge.innerText = 'Est. Normal';
    }
  }

  if (data.memory) {
    const ramPct = Math.round(data.memory.percent || 0);
    document.getElementById('ram-percent').innerText = `${ramPct}%`;
    document.getElementById('ram-gauge').style.setProperty('--percent', ramPct);
    document.getElementById('ram-used-text').innerText = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;
    document.getElementById('ram-avail').innerText = `${data.memory.available_gb} GB`;
  }

  if (data.battery) {
    const b = data.battery;
    document.getElementById('battery-percent').innerText = `${Math.round(b.percent)}%`;
    document.getElementById('battery-fill').style.width = `${b.percent}%`;
    document.getElementById('battery-status').innerText = b.plugged ? '⚡ Cargando / AC' : '🔋 Batería';
    document.getElementById('battery-time').innerText = b.time_left || '';
  }

  if (data.network) {
    document.getElementById('net-down').innerText = formatSpeed(data.network.download_kbs);
    document.getElementById('net-up').innerText = formatSpeed(data.network.upload_kbs);
  }

  if (data.disks && Array.isArray(data.disks)) {
    renderDisks(data.disks);
  }

  // Update process list only if not interacting and modal is hidden
  if (data.top_processes && Array.isArray(data.top_processes)) {
    lastProcessesList = data.top_processes;
    const isModalOpen = !document.getElementById('pin-modal').classList.contains('hidden');
    const isSearching = document.getElementById('proc-search-input').value.trim() !== '';

    if (!isUserInteractingWithTable && !isModalOpen && !isSearching) {
      renderProcesses(lastProcessesList);
    }
  }
}

function formatSpeed(kbs) {
  if (kbs >= 1024) {
    return `${(kbs / 1024).toFixed(1)} MB/s`;
  }
  return `${kbs.toFixed(1)} KB/s`;
}

function renderDisks(disks) {
  const container = document.getElementById('disks-list');
  container.innerHTML = disks.map(disk => `
    <div class="disk-item">
      <div class="disk-info">
        <span><strong>${disk.mountpoint}</strong> (${disk.used_gb} GB / ${disk.total_gb} GB)</span>
        <span>${disk.percent}%</span>
      </div>
      <div class="disk-bar-bg">
        <div class="disk-bar-fill" style="width: ${disk.percent}%;"></div>
      </div>
    </div>
  `).join('');
}

function renderProcesses(processes) {
  const filterText = document.getElementById('proc-search-input').value.toLowerCase().trim();
  const tbody = document.getElementById('process-table-body');
  
  const filtered = processes.filter(p => {
    if (!filterText) return true;
    return p.name.toLowerCase().includes(filterText) || String(p.pid).includes(filterText);
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:16px;">Sin resultados para "${escapeHtml(filterText)}"</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(proc => `
    <tr>
      <td><strong>${escapeHtml(proc.name)}</strong> <small style="color:#94a3b8">(PID ${proc.pid})</small></td>
      <td>${proc.cpu_percent}%</td>
      <td>${proc.memory_percent}%</td>
      <td>
        <div class="action-buttons-cell">
          <button class="restart-btn" onclick="requestRestartProcess(${proc.pid}, '${escapeHtml(proc.name)}')">
            <i class="fa-solid fa-rotate-right"></i> Reiniciar
          </button>
          <button class="kill-btn" onclick="requestKillProcess(${proc.pid}, '${escapeHtml(proc.name)}')">
            <i class="fa-solid fa-xmark"></i> Cerrar
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function fetchProcesses() {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/api/processes`);
    const json = await res.json();
    if (json.success && json.processes) {
      lastProcessesList = json.processes;
      renderProcesses(lastProcessesList);
    }
  } catch (err) {
    console.error('Error al actualizar procesos:', err);
  }
}

function requestRestartProcess(pid, name) {
  openPinModal({
    type: 'restart',
    payload: { pid, name },
    text: `¿Deseas REINICIAR el programa "${name}" (PID ${pid})?`
  });
}

function requestKillProcess(pid, name) {
  openPinModal({
    type: 'kill',
    payload: { pid, name },
    text: `¿Cerrar la aplicación "${name}" (PID ${pid})?`
  });
}

function openPinModal(actionObj) {
  currentAction = actionObj;
  document.getElementById('modal-action-text').innerText = actionObj.text;
  document.getElementById('pin-input').value = '';
  document.getElementById('modal-error').classList.add('hidden');
  document.getElementById('pin-modal').classList.remove('hidden');
  document.getElementById('pin-input').focus();
}

function closePinModal() {
  currentAction = null;
  document.getElementById('pin-modal').classList.add('hidden');
}

async function executeModalAction() {
  if (!currentAction) return;

  const pin = document.getElementById('pin-input').value.trim();
  const errorEl = document.getElementById('modal-error');

  if (!pin) {
    errorEl.innerText = 'Debes ingresar el PIN';
    errorEl.classList.remove('hidden');
    return;
  }

  const baseUrl = getApiBaseUrl();
  let endpoint = '';
  let bodyData = { pin };

  if (currentAction.type === 'kill') {
    endpoint = '/api/kill-process';
    bodyData.pid = currentAction.payload.pid;
  } else if (currentAction.type === 'restart') {
    endpoint = '/api/restart-process';
    bodyData.pid = currentAction.payload.pid;
    bodyData.name = currentAction.payload.name;
  } else if (currentAction.type === 'shutdown') {
    endpoint = '/api/shutdown';
  } else if (currentAction.type === 'stop') {
    endpoint = '/api/stop-agent';
  }

  try {
    const res = await fetch(`${baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyData)
    });

    const json = await res.json();

    if (!json.success) {
      errorEl.innerText = json.error || 'PIN incorrecto o error en la acción';
      errorEl.classList.remove('hidden');
      return;
    }

    alert(json.message || 'Acción ejecutada exitosamente');
    closePinModal();

    if (currentAction.type === 'kill' || currentAction.type === 'restart') {
      setTimeout(fetchProcesses, 2000);
    }
  } catch (err) {
    errorEl.innerText = 'Error al enviar comando al agente';
    errorEl.classList.remove('hidden');
  }
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
