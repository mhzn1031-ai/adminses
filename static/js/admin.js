let ws, pc, localStream, pcRecordAgent;
let currentUsername = '', agentId = '', currentSessionId = '';
let callStartTime = null, durationInterval = null, isIntercomMode = false;

const ICE_SERVERS = [{ urls: 'stun:stun.l.google.com:19302' }];

async function startServerRecordingAgent(stream, session_id) {
  pcRecordAgent = new RTCPeerConnection({ iceServers: ICE_SERVERS });
  stream.getTracks().forEach(t => pcRecordAgent.addTrack(t, stream));
  const offer = await pcRecordAgent.createOffer();
  await pcRecordAgent.setLocalDescription(offer);
  const res = await fetch('/api/record/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp: offer.sdp, type: offer.type, session_id, role: 'agent' })
  });
  if (res.ok) {
    const ans = await res.json();
    await pcRecordAgent.setRemoteDescription({ type: ans.type, sdp: ans.sdp });
  }
}

async function stopServerRecordingAgent(session_id) {
  try {
    await fetch('/api/record/stop', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ session_id, role: 'agent' })
    });
  } catch (e) {}
}

const loginDiv = document.getElementById('loginDiv');
const otpDiv = document.getElementById('otpDiv');
const panel = document.getElementById('panel');
const usernameInput = document.getElementById('username');
const loginBtn = document.getElementById('loginBtn');
const loginStatus = document.getElementById('loginStatus');
const otpCodeInput = document.getElementById('otpCode');
const verifyOtpBtn = document.getElementById('verifyOtpBtn');
const otpStatus = document.getElementById('otpStatus');
const pendingCallsDiv = document.getElementById('pendingCalls');
const callHistoryDiv = document.getElementById('callHistory');
const pendingCountSpan = document.getElementById('pendingCount');
const activeCallDiv = document.getElementById('activeCallDiv');
const callerNameDisplay = document.getElementById('callerNameDisplay');
const callDurationEl = document.getElementById('callDuration');
const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const toggleAudioBtn = document.getElementById('toggleAudio');
const toggleVideoBtn = document.getElementById('toggleVideo');
const toggleSpeakerBtn = document.getElementById('toggleSpeaker');
const toggleIntercomBtn = document.getElementById('toggleIntercom');
const hangupBtn = document.getElementById('hangupBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');

loginBtn.onclick = async () => {
  const username = usernameInput.value.trim();
  if (!username) return loginStatus.textContent = 'Kullanıcı adı gerekli';
  currentUsername = username;
  const res = await fetch('/api/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  });
  if (res.ok) {
    loginDiv.style.display = 'none';
    otpDiv.style.display = 'block';
  } else {
    loginStatus.textContent = 'Kullanıcı bulunamadı';
  }
};

verifyOtpBtn.onclick = async () => {
  const otp = otpCodeInput.value.trim();
  if (otp.length !== 6) return otpStatus.textContent = '6 haneli kod girin';
  const res = await fetch('/api/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: currentUsername, otp })
  });
  if (res.ok) {
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    otpDiv.style.display = 'none';
    panel.style.display = 'block';
    initAdmin();
  } else {
    otpStatus.textContent = 'Geçersiz veya süresi dolmuş kod';
  }
};

async function initAdmin() {
  agentId = 'agent_' + Date.now();
  await loadPendingCalls();
  await loadCallHistory();
  setInterval(async () => {
    await loadPendingCalls();
    await loadCallHistory();
  }, 5000);
  
  ws = new WebSocket(`ws://${location.host}/ws/${agentId}`);
  ws.onopen = () => ws.send(JSON.stringify({ type: 'agent_ready', agent_id: agentId }));
  ws.onmessage = async (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.type === 'pending_update') {
      await loadPendingCalls();
      if (activeCallDiv.style.display !== 'none') showNotification('Yeni çağrı bekleniyor!');
    } else if (msg.type === 'answer' && pc) {
      await pc.setRemoteDescription({ type: 'answer', sdp: msg.sdp });
    } else if (msg.type === 'ice_candidate' && pc) {
      await pc.addIceCandidate(new RTCIceCandidate(msg.candidate));
    } else if (msg.type === 'call_ended') {
      cleanup();
      location.reload();
    }
  };
}

async function loadPendingCalls() {
  const res = await fetch('/api/calls/pending');
  if (!res.ok) return;
  const calls = await res.json();
  pendingCountSpan.textContent = calls.length;
  pendingCallsDiv.innerHTML = '';
  calls.forEach(call => {
    const div = document.createElement('div');
    div.className = 'call-item';
    div.innerHTML = `
      <div>
        <strong>${call.caller_name}</strong><br>
        <small>${new Date(call.start_time).toLocaleString('tr-TR')}</small>
      </div>
      <div>
        <button class="accept-btn" onclick="acceptCall('${call.session_id}', '${call.caller_name}')">Kabul Et</button>
        <button class="reject-btn" onclick="rejectCall('${call.session_id}')">Reddet</button>
      </div>
    `;
    pendingCallsDiv.appendChild(div);
  });
}

async function loadCallHistory() {
  const res = await fetch('/api/calls/history?limit=20');
  if (!res.ok) return;
  const calls = await res.json();
  callHistoryDiv.innerHTML = '';
  calls.filter(c => c.status !== 'pending').forEach(call => {
    const div = document.createElement('div');
    div.className = 'call-item';
    const duration = call.duration ? `${Math.floor(call.duration / 60)}:${(call.duration % 60).toString().padStart(2, '0')}` : '-';
    div.innerHTML = `
      <div>
        <strong>${call.caller_name}</strong> - ${call.status}<br>
        <small>${new Date(call.start_time).toLocaleString('tr-TR')} | Süre: ${duration}</small>
      </div>
    `;
    callHistoryDiv.appendChild(div);
  });
}

window.acceptCall = async (sessionId, callerName) => {
  currentSessionId = sessionId;
  await fetch('/api/call/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, action: 'accept', agent_id: agentId })
  });
  document.getElementById('callsSection').style.display = 'none';
  activeCallDiv.style.display = 'block';
  callerNameDisplay.textContent = callerName;
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true });
    localVideo.srcObject = localStream;
    localVideo.style.display = 'none';
  } catch (err) {
    return alert('Medya erişimi reddedildi');
  }
  pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
  localStream.getTracks().forEach(t => pc.addTrack(t, localStream));
  pc.ontrack = (evt) => remoteVideo.srcObject = evt.streams[0];
  pc.onicecandidate = (evt) => {
    if (evt.candidate) ws.send(JSON.stringify({ type: 'ice_candidate', candidate: evt.candidate, target: sessionId }));
  };
  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  ws.send(JSON.stringify({ type: 'offer', sdp: offer.sdp, target: sessionId }));
  await startServerRecordingAgent(localStream, sessionId);
  startCallTimer();
};

window.rejectCall = async (sessionId) => {
  await fetch('/api/call/respond', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, action: 'reject' })
  });
  await loadPendingCalls();
};

toggleAudioBtn.onclick = () => {
  const audioTrack = localStream.getAudioTracks()[0];
  if (audioTrack) {
    audioTrack.enabled = !audioTrack.enabled;
    toggleAudioBtn.classList.toggle('active', audioTrack.enabled);
    toggleAudioBtn.textContent = audioTrack.enabled ? '🔊 Ses' : '🔇 Ses';
  }
};

toggleVideoBtn.onclick = async () => {
  const videoTrack = localStream.getVideoTracks()[0];
  if (videoTrack) {
    videoTrack.enabled = !videoTrack.enabled;
    toggleVideoBtn.classList.toggle('active', videoTrack.enabled);
    localVideo.style.display = videoTrack.enabled ? 'block' : 'none';
  } else {
    try {
      const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
      const newTrack = videoStream.getVideoTracks()[0];
      localStream.addTrack(newTrack);
      localVideo.srcObject = localStream;
      localVideo.style.display = 'block';
      if (pc) pc.addTrack(newTrack, localStream);
      toggleVideoBtn.classList.add('active');
    } catch (err) {
      alert('Kamera erişimi reddedildi');
    }
  }
};

toggleSpeakerBtn.onclick = () => {
  if (isIntercomMode) return;
  remoteVideo.muted = !remoteVideo.muted;
  toggleSpeakerBtn.classList.toggle('active', !remoteVideo.muted);
  toggleSpeakerBtn.textContent = remoteVideo.muted ? '🔇 Hoparlör' : '🔊 Hoparlör';
};

toggleIntercomBtn.onclick = () => {
  isIntercomMode = !isIntercomMode;
  toggleIntercomBtn.classList.toggle('active', isIntercomMode);
  if (isIntercomMode) {
    remoteVideo.muted = true;
    toggleSpeakerBtn.classList.remove('active');
    toggleSpeakerBtn.disabled = true;
  } else {
    remoteVideo.muted = false;
    toggleSpeakerBtn.classList.add('active');
    toggleSpeakerBtn.disabled = false;
  }
};

fullscreenBtn.onclick = () => {
  const container = document.getElementById('videoContainer');
  if (!document.fullscreenElement) container.requestFullscreen();
  else document.exitFullscreen();
};

hangupBtn.onclick = async () => {
  await stopServerRecordingAgent(currentSessionId);
  await fetch('/api/call/end', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: currentSessionId })
  });
  cleanup();
  location.reload();
};

function startCallTimer() {
  callStartTime = Date.now();
  durationInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - callStartTime) / 1000);
    const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
    const secs = (elapsed % 60).toString().padStart(2, '0');
    callDurationEl.textContent = `${mins}:${secs}`;
  }, 1000);
}

function cleanup() {
  if (durationInterval) clearInterval(durationInterval);
  if (pc) pc.close();
  if (pcRecordAgent) pcRecordAgent.close();
  if (ws) ws.close();
  if (localStream) localStream.getTracks().forEach(t => t.stop());
}

function showNotification(message) {
  const notif = document.createElement('div');
  notif.style.cssText = 'position:fixed;top:20px;right:20px;background:#4CAF50;color:white;padding:15px 20px;border-radius:8px;z-index:9999;box-shadow:0 4px 8px rgba(0,0,0,0.2);';
  notif.textContent = message;
  document.body.appendChild(notif);
  setTimeout(() => notif.remove(), 3000);
}
