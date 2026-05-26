// js/video.js
// =============================================================================
// Manuskriptbaserad videoinspelning.
//
// Ett "manuskript" är en lista av cues — tidsstyrda åtgärder. När man trycker
// "Spela" körs manuskriptet i realtid utan inspelning (förhandsgranskning).
// När man trycker "Spela in" körs samma manuskript och bilden fångas via
// MediaRecorder på renderer.domElement.captureStream(). När manuset är slut
// stoppas inspelningen och en .webm-fil laddas automatiskt ner.
//
// Cue-format:
//   { at: 2.5, action: 'setRPM', value: 80 }
//   { at: 0.0, action: 'setAutoRotate', value: true }
//   { at: 1.0, action: 'cameraTo', position: [..], target: [..], duration: 3 }
//
// Stödda actions:
//   setTheta(value)       — sätt vevvinkel (rad)
//   setAutoRotate(value)  — true/false
//   setRPM(value)         — pedal-rpm
//   setHeight(value)      — förarens längd (cm)
//   setGender(value)      — 'male' | 'female'
//   setSittHeight(value)  — sadelhöjd (cm)
//   setRiderVisible(value)— true/false
//   cameraTo(position, target, duration) — tween kamera+OrbitControls.target
// =============================================================================

const SCRIPTS = {
  // Default-manuskript: visar maskinen i 18 sekunder.
  // Börjar med en lugn vy snett framifrån, animationen startar, kamerarundan,
  // sedan en närbild på pedalpartiet, åter ut till översikt.
  default: {
    name: 'Översikt 18 s',
    duration: 18.0,
    cues: [
      { at: 0.0,  action: 'setRiderVisible', value: true },
      { at: 0.0,  action: 'setRPM', value: 50 },
      { at: 0.0,  action: 'setTheta', value: 0 },
      // Startposition: samma som grundinitialvyn i setup.js
      { at: 0.0,  action: 'cameraTo',
        position: [230, 160, 320], target: [20, 110, 0], duration: 0 },

      { at: 1.0,  action: 'setAutoRotate', value: true },

      // Långsam kamerarundan runt maskinen
      { at: 2.0,  action: 'cameraTo',
        position: [280, 110, 80], target: [20, 80, 0], duration: 4.0 },
      { at: 7.0,  action: 'cameraTo',
        position: [80, 90, -260], target: [20, 70, 0], duration: 4.0 },

      // Närbild pedalpartiet
      { at: 11.0, action: 'cameraTo',
        position: [40, 70, 110], target: [0, 50, 0], duration: 3.0 },

      // Ut igen — tillbaka till grundinitialvyn
      { at: 15.0, action: 'cameraTo',
        position: [230, 160, 320], target: [20, 110, 0], duration: 2.5 },

      { at: 17.5, action: 'setAutoRotate', value: false },
    ],
  },

  // Kort variant — för snabbtest av inspelningen
  kort: {
    name: 'Kort 6 s',
    duration: 6.0,
    cues: [
      { at: 0.0, action: 'setRPM', value: 60 },
      { at: 0.0, action: 'setAutoRotate', value: true },
      { at: 0.0, action: 'cameraTo',
        position: [230, 160, 320], target: [20, 110, 0], duration: 0 },
      { at: 1.0, action: 'cameraTo',
        position: [80, 90, -260], target: [20, 80, 0], duration: 4.5 },
      { at: 5.8, action: 'setAutoRotate', value: false },
    ],
  },

  // Antropometri-demo: visar olika förarlängder mot samma maskin
  antropometri: {
    name: 'Olika längder',
    duration: 16.0,
    cues: [
      { at: 0.0,  action: 'cameraTo',
        position: [230, 160, 320], target: [20, 110, 0], duration: 0 },
      { at: 0.0,  action: 'setAutoRotate', value: true },
      { at: 0.0,  action: 'setRPM', value: 45 },
      { at: 0.0,  action: 'setHeight', value: 150 },
      { at: 4.0,  action: 'setHeight', value: 170 },
      { at: 8.0,  action: 'setHeight', value: 190 },
      { at: 12.0, action: 'setHeight', value: 210 },
      { at: 15.5, action: 'setAutoRotate', value: false },
    ],
  },
};

export function bindVideo(ctx) {
  const { animator, renderer, rider, sceneState, camera, controls } = ctx;

  // ── Skapa UI-element (knapppanel under info-rutan) ──────────
  const panel = document.createElement('div');
  panel.id = 'video-panel';
  panel.style.cssText =
    'position:absolute;top:10px;right:10px;background:rgba(255,255,255,0.85);' +
    'padding:10px 14px;border-radius:6px;font-size:13px;line-height:1.5;' +
    'box-shadow:0 2px 8px rgba(0,0,0,0.1);font-family:sans-serif;min-width:200px';
  panel.innerHTML = `
    <div style="font-weight:bold;margin-bottom:4px">Video</div>
    <label style="display:block">Manus:
      <select id="video-script">${
        Object.entries(SCRIPTS)
          .map(([k, s]) => `<option value="${k}">${s.name} (${s.duration}s)</option>`)
          .join('')
      }</select>
    </label>
    <div style="margin-top:6px;display:flex;gap:6px">
      <button id="video-play">▶ Spela</button>
      <button id="video-record">⬤ Spela in</button>
      <button id="video-stop" disabled>■ Stopp</button>
    </div>
    <div id="video-status" style="margin-top:6px;font-size:11px;color:#555;min-height:14px"></div>
  `;
  document.body.appendChild(panel);

  const scriptSelect = panel.querySelector('#video-script');
  const playBtn = panel.querySelector('#video-play');
  const recordBtn = panel.querySelector('#video-record');
  const stopBtn = panel.querySelector('#video-stop');
  const statusEl = panel.querySelector('#video-status');

  // ── Playback-state ──────────────────────────────────────────
  let playback = null;     // { startTime, script, cuesPending, tweens, recorder, ... }

  // Tween-hanterare: körs varje frame av rAF-loopen i playRun
  const tweens = [];

  /**
   * Tween en kamera+target från nuvarande till nya värden över `duration` sek.
   * Kameran roteras runt OrbitControls.target, så vi tween:ar BÅDA.
   * duration=0 betyder omedelbar.
   */
  function startCameraTween(position, target, duration) {
    const fromPos = camera.position.clone();
    const fromTgt = controls.target.clone();
    const toPos = { x: position[0], y: position[1], z: position[2] };
    const toTgt = { x: target[0], y: target[1], z: target[2] };

    if (duration <= 0) {
      camera.position.set(toPos.x, toPos.y, toPos.z);
      controls.target.set(toTgt.x, toTgt.y, toTgt.z);
      camera.lookAt(controls.target);
      return;
    }

    const startMs = performance.now();
    const endMs = startMs + duration * 1000;

    // easeInOut (cosinus) för mjukare rörelse
    function ease(t) { return 0.5 - 0.5 * Math.cos(Math.PI * t); }

    tweens.push(function step(now) {
      const t = Math.max(0, Math.min(1, (now - startMs) / (endMs - startMs)));
      const e = ease(t);
      camera.position.set(
        fromPos.x + (toPos.x - fromPos.x) * e,
        fromPos.y + (toPos.y - fromPos.y) * e,
        fromPos.z + (toPos.z - fromPos.z) * e,
      );
      controls.target.set(
        fromTgt.x + (toTgt.x - fromTgt.x) * e,
        fromTgt.y + (toTgt.y - fromTgt.y) * e,
        fromTgt.z + (toTgt.z - fromTgt.z) * e,
      );
      camera.lookAt(controls.target);
      return t >= 1;   // klar?
    });
  }

  function tickTweens() {
    const now = performance.now();
    for (let i = tweens.length - 1; i >= 0; i--) {
      if (tweens[i](now)) tweens.splice(i, 1);
    }
  }

  // ── Cue-actions ─────────────────────────────────────────────
  // Varje action får sin cue och har tillgång till ctx via closure.
  const ACTIONS = {
    setTheta:         (cue) => animator.setTheta(cue.value),
    setAutoRotate:    (cue) => {
      animator.setAutoRotate(cue.value);
      const cb = document.getElementById('auto-rotate');
      if (cb) cb.checked = cue.value;
    },
    setRPM:           (cue) => {
      animator.setRPM(cue.value);
      const s = document.getElementById('rpm-slider');
      const v = document.getElementById('rpm-value');
      if (s) s.value = cue.value;
      if (v) v.textContent = cue.value;
    },
    setHeight:        (cue) => {
      sceneState.setHeight(cue.value);
      // Auto-justera sadelhöjd (samma logik som UI:ns slider gör)
      const newSitt = rider.autoSaddleHeight(cue.value);
      sceneState.setSittHeight(newSitt);
      const hs = document.getElementById('height-slider');
      const hv = document.getElementById('height-value');
      const ss = document.getElementById('saddle-slider');
      const sv = document.getElementById('saddle-value');
      if (hs) hs.value = cue.value;
      if (hv) hv.textContent = cue.value;
      if (ss) ss.value = Math.round(newSitt);
      if (sv) sv.textContent = Math.round(newSitt);
    },
    setGender:        (cue) => {
      sceneState.setGender(cue.value);
      const sel = document.getElementById('gender-select');
      if (sel) sel.value = cue.value;
    },
    setSittHeight:    (cue) => {
      sceneState.setSittHeight(cue.value);
      const s = document.getElementById('saddle-slider');
      const v = document.getElementById('saddle-value');
      if (s) s.value = cue.value;
      if (v) v.textContent = cue.value;
    },
    setRiderVisible:  (cue) => {
      rider.setVisible(cue.value);
      const cb = document.getElementById('show-rider');
      if (cb) cb.checked = cue.value;
    },
    cameraTo:         (cue) => startCameraTween(cue.position, cue.target, cue.duration || 0),
  };

  function runCue(cue) {
    const fn = ACTIONS[cue.action];
    if (!fn) {
      console.warn(`video: okänd action "${cue.action}"`);
      return;
    }
    fn(cue);
  }

  // ── Playback-loop ───────────────────────────────────────────
  function startPlayback(scriptKey, { record }) {
    if (playback) return;   // redan igång

    const script = SCRIPTS[scriptKey];
    if (!script) {
      statusEl.textContent = `Okänt manus: ${scriptKey}`;
      return;
    }

    const cuesPending = [...script.cues].sort((a, b) => a.at - b.at);
    const startTime = performance.now();
    let recorder = null;
    let chunks = [];

    if (record) {
      // Kontrollera att MediaRecorder och captureStream finns
      if (typeof renderer.domElement.captureStream !== 'function') {
        statusEl.textContent =
          'Inspelning stöds inte: canvas.captureStream() saknas i denna webbläsare.';
        return;
      }
      const stream = renderer.domElement.captureStream(60);
      // Försök hitta en codec som funkar
      const candidates = [
        'video/webm;codecs=vp9',
        'video/webm;codecs=vp8',
        'video/webm',
      ];
      const mimeType = candidates.find(c => MediaRecorder.isTypeSupported?.(c)) || '';
      try {
        recorder = mimeType
          ? new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 8_000_000 })
          : new MediaRecorder(stream, { videoBitsPerSecond: 8_000_000 });
      } catch (e) {
        statusEl.textContent = `MediaRecorder-fel: ${e.message}`;
        return;
      }
      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) chunks.push(ev.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: chunks[0]?.type || 'video/webm' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        a.href = url;
        a.download = `springcykel-${scriptKey}-${ts}.webm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        // Behåll URL ett tag så nedladdningen hinner starta
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        statusEl.textContent = `Sparad: ${a.download} (${(blob.size/1e6).toFixed(1)} MB)`;
      };
      recorder.start(250);   // emit chunk var 250 ms
    }

    playback = { script, cuesPending, startTime, recorder, recording: !!record };

    playBtn.disabled = true;
    recordBtn.disabled = true;
    stopBtn.disabled = false;
    statusEl.textContent = record ? 'Spelar in...' : 'Spelar...';

    // Hak in i animator-loopen: animator har redan en rAF-loop som körs
    // ständigt, så vi behöver bara en separat lättviktig loop som kollar
    // tid och triggar cues + driver tweens. Renderingen sköts av animator.
    function pump() {
      if (!playback) return;
      const elapsed = (performance.now() - playback.startTime) / 1000;

      while (playback.cuesPending.length && playback.cuesPending[0].at <= elapsed) {
        const cue = playback.cuesPending.shift();
        try { runCue(cue); } catch (e) { console.error('cue-fel:', cue, e); }
      }

      tickTweens();

      if (elapsed >= playback.script.duration) {
        finishPlayback();
        return;
      }
      requestAnimationFrame(pump);
    }
    requestAnimationFrame(pump);
  }

  function finishPlayback() {
    if (!playback) return;
    const wasRecording = playback.recording;
    if (playback.recorder && playback.recorder.state !== 'inactive') {
      playback.recorder.stop();
    }
    // Stoppa fortsatt rotation om manuset lämnat den på
    animator.setAutoRotate(false);
    const cb = document.getElementById('auto-rotate');
    if (cb) cb.checked = false;
    playback = null;
    playBtn.disabled = false;
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    if (!wasRecording) statusEl.textContent = 'Klar.';
    // Om recording: statusEl uppdateras i recorder.onstop med filinfo.
  }

  playBtn.addEventListener('click', () => {
    startPlayback(scriptSelect.value, { record: false });
  });
  recordBtn.addEventListener('click', () => {
    startPlayback(scriptSelect.value, { record: true });
  });
  stopBtn.addEventListener('click', () => {
    if (playback) finishPlayback();
  });

  return { startPlayback, scripts: SCRIPTS };
}
