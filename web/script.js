const api = {
  chat: async (text) => {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error('Chat failed');
    return res.json();
  },
  createApp: async (payload) => {
    const res = await fetch('/api/applications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Create application failed');
    return res.json();
  },
  getApp: async (appId) => {
    const res = await fetch(`/api/applications/${encodeURIComponent(appId)}`);
    if (!res.ok) throw new Error('Application not found');
    return res.json();
  },
  addProgress: async (appId, message) => {
    const res = await fetch(`/api/applications/${encodeURIComponent(appId)}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error('Add progress failed');
    return res.json();
  }
};

// Chat UI
const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');

function addChat(sender, text) {
  const div = document.createElement('div');
  div.className = `msg ${sender}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

chatSend.addEventListener('click', async () => {
  const text = chatInput.value.trim();
  if (!text) return;
  addChat('user', text);
  chatInput.value = '';
  try {
    const res = await api.chat(text);
    addChat('bot', res.reply);
  } catch (e) {
    addChat('bot', 'Sorry, something went wrong.');
  }
});

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') chatSend.click();
});

// Application form
const submitAppBtn = document.getElementById('submit-app');
const appResult = document.getElementById('app-result');

submitAppBtn.addEventListener('click', async () => {
  const payload = {
    applicant: document.getElementById('applicant').value.trim(),
    site_address: document.getElementById('site_address').value.trim(),
    connectors: document.getElementById('connectors').value.trim(),
    power_kw: parseInt(document.getElementById('power_kw').value, 10) || undefined,
    notes: document.getElementById('notes').value.trim(),
  };
  if (!payload.applicant) {
    appResult.textContent = 'Applicant name is required';
    return;
  }
  try {
    const res = await api.createApp(payload);
    appResult.textContent = `Application submitted. ID: ${res.app_id} (status: ${res.status})`;
  } catch (e) {
    appResult.textContent = 'Failed to submit application';
  }
});

// Status check
const statusBtn = document.getElementById('check-status');
const statusInput = document.getElementById('status-app-id');
const statusResult = document.getElementById('status-result');

statusBtn.addEventListener('click', async () => {
  const appId = statusInput.value.trim();
  if (!appId) return;
  try {
    const rec = await api.getApp(appId);
    statusResult.textContent = JSON.stringify(rec, null, 2);
  } catch (e) {
    statusResult.textContent = 'Application not found';
  }
});

// Progress update
const progressBtn = document.getElementById('add-progress');
const progressAppId = document.getElementById('progress-app-id');
const progressMessage = document.getElementById('progress-message');
const progressResult = document.getElementById('progress-result');

progressBtn.addEventListener('click', async () => {
  const appId = progressAppId.value.trim();
  const message = progressMessage.value.trim();
  if (!appId || !message) return;
  try {
    await api.addProgress(appId, message);
    progressResult.textContent = 'Progress added.';
    progressMessage.value = '';
  } catch (e) {
    progressResult.textContent = 'Failed to add progress (check APP ID).';
  }
});
