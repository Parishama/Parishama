async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.headers.get('content-type')?.includes('application/json') ? res.json() : res.text();
}

function addMsg(who, text) {
  const log = document.getElementById('chat-log');
  const div = document.createElement('div');
  div.className = `msg ${who}`;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMsg('user', text);
  try {
    const res = await api('/api/chat', { method: 'POST', body: { text } });
    addMsg('bot', res.reply);
  } catch (e) {
    addMsg('bot', 'Error: ' + e.message);
  }
}

function setupChat() {
  document.getElementById('chat-send').addEventListener('click', sendChat);
  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendChat();
  });
}

async function submitAppForm(e) {
  e.preventDefault();
  const form = e.target;
  const data = Object.fromEntries(new FormData(form).entries());
  data.power_capacity_kw = Number(data.power_capacity_kw);
  data.connectors = (data.connectors || '').split(',').map(s => s.trim()).filter(Boolean);
  try {
    const rec = await api('/api/applications', { method: 'POST', body: data });
    document.getElementById('create-result').textContent = `Created ${rec.app_id}`;
    document.getElementById('lookup-id').value = rec.app_id;
    await lookup();
  } catch (e) {
    document.getElementById('create-result').textContent = 'Error: ' + e.message;
  }
}

async function lookup() {
  const appId = document.getElementById('lookup-id').value.trim();
  if (!appId) return;
  try {
    const rec = await api(`/api/applications/${encodeURIComponent(appId)}`);
    document.getElementById('app-json').textContent = JSON.stringify(rec, null, 2);
  } catch (e) {
    document.getElementById('app-json').textContent = 'Error: ' + e.message;
  }
}

async function updateStatus() {
  const appId = document.getElementById('lookup-id').value.trim();
  const status = document.getElementById('status-text').value.trim();
  if (!appId || !status) return;
  try {
    await api(`/api/applications/${encodeURIComponent(appId)}/status`, { method: 'POST', body: { status } });
    await lookup();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

async function addProgress() {
  const appId = document.getElementById('lookup-id').value.trim();
  const message = document.getElementById('progress-text').value.trim();
  if (!appId || !message) return;
  try {
    await api(`/api/applications/${encodeURIComponent(appId)}/progress`, { method: 'POST', body: { message } });
    await lookup();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

function setupAppForm() {
  document.getElementById('app-form').addEventListener('submit', submitAppForm);
  document.getElementById('lookup-btn').addEventListener('click', lookup);
  document.getElementById('status-btn').addEventListener('click', updateStatus);
  document.getElementById('progress-btn').addEventListener('click', addProgress);
}

window.addEventListener('DOMContentLoaded', () => {
  setupChat();
  setupAppForm();
});
