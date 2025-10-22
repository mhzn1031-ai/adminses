let ws, pc, localStream, pcRecord;
let callerName = '', callerId = '', sessionId = '';
let callStartTime = null, durationInterval = null, isIntercomMode = false;

const ICE_SERVERS = [{ urls: 'stun:stun.l.google.com:19302' }];

async function startServerRecording(stream, session_id) {
  pcRecord = new RTCPeerConnection({ iceServers: ICE_SERVERS });
  stream.getTracks().forEach(t => pcRecord.addTrack(t, stream));
  const offer = await pcRecord.createOffer();
  await pcRecord.setLocalDescription(offer);
  const res = await fetch('/api/record/offer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp: offer.sdp, type: offer.type, session_id, role: 'caller' })
  });
  if (res.ok) {
    const ans = await res.json();
    await pcRecord.setRemoteDescription({ type: ans.type, sdp: ans.sdp });
  }
}

async function stopServerRecording(session_id) {
  try {
    await fetch('/api/record/stop', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ session_id, role: 'caller' })
    });
  } catch (e) {}
}

const nameScreen = document.getElementById('nameScreen');
const callScreen = document.getElementById('callScreen');
const callerNameInput = document.getElementById('callerName');
const callBtn = document.getElementById('callBtn');
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

callBtn.onclick = async () => {
  callerName = callerNameInput.value.trim();
  if (!callerName) return alert('Lütfen adınızı girin');
  
  callerId = 'caller_' + Date.now();
  sessionId = 'session_' + Date.now();
  
  nameScreen.style.display = 'none';
  callScreen.style.display = 'block';
  callerNameDisplay.textContent = callerName;
  
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true });
    localVideo.srcObject = localStream;
    localVideo.style.display = 'none';
  } catch (err) {
    return alert('Medya erişimi reddedildi');
  }
  
  ws = new WebSocket(`ws://${location.host}/ws/${callerId}`);
  
  ws.onopen = async () => {
    await fetch('/api/call/notify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ caller_name: callerName, caller_id: callerId, session_id: sessionId })
    });
    ws.send(JSON.stringify({ type: 'join_session', session_id: sessionId }));
  };
  
  ws.onmessage = async (evt) => {
    const msg = JSON.parse(evt.data);
    if (msg.type === 'offer') {
      await handleOffer(msg.sdp);
      await startServerRecording(localStream, sessionId);
      startCallTimer();
    } else if (msg.type === 'ice_candidate' && pc) {
      await pc.addIceCandidate(new RTCIceCandidate(msg.candidate));
    } else if (msg.type === 'call_ended') {
      cleanup();
      location.reload();
    }
  };
  
  ws.onclose = () => cleanup();
};

async function handleOffer(sdp) {
  pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
  localStream.getTracks().forEach(t => pc.addTrack(t, localStream));
  pc.ontrack = (evt) => remoteVideo.srcObject = evt.streams[0];
  pc.onicecandidate = (evt) => {
    if (evt.candidate) ws.send(JSON.stringify({ type: 'ice_candidate', candidate: evt.candidate, target: sessionId }));
  };
  await pc.setRemoteDescription({ type: 'offer', sdp });
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  ws.send(JSON.stringify({ type: 'answer', sdp: answer.sdp, target: sessionId }));
}

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
  await stopServerRecording(sessionId);
  await fetch('/api/call/end', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
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
  if (pcRecord) pcRecord.close();
  if (ws) ws.close();
  if (localStream) localStream.getTracks().forEach(t => t.stop());
}
