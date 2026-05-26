// js/ui.js
// =============================================================================
// UI: kopplar alla DOM-element till state. Slider för theta, rpm, längd, sadel.
// Checkbox för auto-rotate och förare-synlighet. Dropdown för kön.
// =============================================================================
import { speedFromRPM } from './animation.js';

export function bindUI(ctx) {
  const { G, animator, rider, sceneState } = ctx;
  // sceneState: { rebuildSaddle(newHeight): void, currentHeight, currentGender,
  //               currentSittHeight, setHeight(h), setGender(g), setSittHeight(h) }

  const thetaSlider = document.getElementById('theta-slider');
  const thetaValueEl = document.getElementById('theta-value');
  const autoRotateEl = document.getElementById('auto-rotate');
  const rpmSlider = document.getElementById('rpm-slider');
  const rpmValueEl = document.getElementById('rpm-value');
  const speedValueEl = document.getElementById('speed-value');
  const heightSlider = document.getElementById('height-slider');
  const heightValueEl = document.getElementById('height-value');
  const saddleSlider = document.getElementById('saddle-slider');
  const saddleValueEl = document.getElementById('saddle-value');
  const showRiderEl = document.getElementById('show-rider');
  const genderEl = document.getElementById('gender-select');

  // Synka rpm-slider med JSON-default
  rpmSlider.min = G.mechanics.rpm_range[0];
  rpmSlider.max = G.mechanics.rpm_range[1];
  rpmSlider.value = G.mechanics.default_rpm;
  rpmValueEl.textContent = G.mechanics.default_rpm;
  speedValueEl.textContent = speedFromRPM(G.mechanics.default_rpm, G).toFixed(1);

  // Synka längd-slider och sadel-slider med JSON
  heightSlider.min = G.rider.height_range_cm[0];
  heightSlider.max = G.rider.height_range_cm[1];
  heightSlider.value = G.rider.default_height_cm;
  heightValueEl.textContent = G.rider.default_height_cm;
  saddleSlider.min = G.saddle.height_range_cm[0];
  saddleSlider.max = G.saddle.height_range_cm[1];

  // === Theta-slider (anger PEDAL-vinkeln, 0-360°) ===
  thetaSlider.addEventListener('input', (e) => {
    const pedalDeg = parseFloat(e.target.value);
    const pedalAngle = pedalDeg * Math.PI / 180;
    const theta = pedalAngle * G.mechanics.gear_ratio;
    thetaValueEl.textContent = pedalDeg.toFixed(0) + '°';
    animator.setTheta(theta);
  });

  // === Auto-rotate ===
  autoRotateEl.addEventListener('change', (e) => {
    animator.setAutoRotate(e.target.checked);
  });

  // === Rpm ===
  rpmSlider.addEventListener('input', (e) => {
    const newRpm = parseInt(e.target.value);
    rpmValueEl.textContent = newRpm;
    animator.setRPM(newRpm);
    speedValueEl.textContent = speedFromRPM(newRpm, G).toFixed(1);
  });

  // === Kön ===
  genderEl.addEventListener('change', (e) => {
    sceneState.setGender(e.target.value);
  });

  // === Längd (auto-justerar sadelhöjd) ===
  heightSlider.addEventListener('input', (e) => {
    const newHeight = parseInt(e.target.value);
    heightValueEl.textContent = newHeight;
    sceneState.setHeight(newHeight);
    // Auto-uppdatera sadelhöjd och slider
    const newSitt = rider.autoSaddleHeight(newHeight);
    saddleSlider.value = Math.round(newSitt);
    saddleValueEl.textContent = Math.round(newSitt);
    sceneState.setSittHeight(newSitt);
  });

  // === Sadelhöjd manuell ===
  saddleSlider.addEventListener('input', (e) => {
    const newSitt = parseInt(e.target.value);
    saddleValueEl.textContent = newSitt;
    sceneState.setSittHeight(newSitt);
  });

  // === Visa/dölja förare ===
  showRiderEl.addEventListener('change', (e) => {
    rider.setVisible(e.target.checked);
  });

  // === Styrning ===
  const steerSlider = document.getElementById('steer-slider');
  const steerValueEl = document.getElementById('steer-value');
  const steerInfoEl = document.getElementById('steer-info');
  const steering = ctx.steering;
  if (steerSlider && steering) {
    steerSlider.addEventListener('input', (e) => {
      const v = parseInt(e.target.value) / 100;   // -1 till +1
      steering.setSteer(v);
      // Uppdatera visning
      steerValueEl.textContent = v.toFixed(2);
      // Beräkna info-rad: AB-offset för aktiva sidan + uppskattad svängradie
      let activeOffset = 0;
      let activeLabel = '';
      if (v > 0) {
        activeOffset = steering.getABOffset('front_left');
        activeLabel = 'vänster';
      } else if (v < 0) {
        activeOffset = steering.getABOffset('front_right');
        activeLabel = 'höger';
      }
      const dir = v === 0 ? '' : ` (${activeLabel})`;
      // Grov svängradie-uppskattning. Vid offset > 0 är inre stegen kortare.
      // Använd interpolation från tabellen i whitepapret.
      let radiusStr = '∞';
      if (Math.abs(v) > 0.01) {
        // Approximera steglängd-asymmetri som linjär mot offset, från tabellen:
        // offset 1→1.5cm, 2→3.1cm, 3→4.8cm, 4→6.5cm asymmetri
        const offsetMag = Math.abs(activeOffset);
        const asym = offsetMag * 1.6;   // grov approximation
        const stepOuter = 67.9;
        const stepInner = stepOuter - asym;
        if (stepInner > 0 && asym > 0.1) {
          const ratio = stepOuter / stepInner;
          const trackWidth = G.track_width;
          const R = (trackWidth / 2) * (ratio + 1) / (ratio - 1);
          radiusStr = (R / 100).toFixed(2) + ' m';
        }
      }
      steerInfoEl.textContent = `AB-offset: ${Math.abs(activeOffset).toFixed(1)} cm${dir} · svängradie: ${radiusStr}`;
    });
  }

  // Trigga animationsloopen att uppdatera UI när theta löper
  ctx.animator_onTick = (theta) => {
    const pedalAngle = theta / G.mechanics.gear_ratio;
    const pedalDeg = ((pedalAngle * 180 / Math.PI) % 360 + 360) % 360;
    thetaSlider.value = pedalDeg.toFixed(0);
    thetaValueEl.textContent = pedalDeg.toFixed(0) + '°';
  };
}
