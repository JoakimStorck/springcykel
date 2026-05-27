// js/main.js
// =============================================================================
// Springcykelns 3D-visualisering — orkestrering.
//
// Läser geometri-data (machine_geometry.json) och bygger upp scenen genom
// alla moduler, kopplar UI och startar animationsloopen.
//
// Data-flöde (engångs vid sidladdning):
//   machine_geometry.json (G) → setup, frame, driveline, legs, saddle, handlebar
//                            → mannequin/rider
//                            → animator
//                            → ui (+ video)
//
// Data-flöde (runtime):
//   UI-slider → sceneState/animator → uppdaterar moduler → renderer
// =============================================================================
import { createScene } from './setup.js';
import { buildFrame } from './frame.js';
import { buildDriveline } from './driveline.js';
import { buildLegs } from './legs.js';
import { buildSaddle, makeSaddleTopFn } from './saddle.js';
import { buildHandlebar } from './handlebar.js';
import { createRiderController } from './rider.js';
import { createAnimator } from './animation.js';
import { bindUI } from './ui.js';
import { bindVideo } from './video.js';
import { createSteering } from './steering.js';
import { buildSteeringRender } from './steering_render.js';

async function loadGeometry() {
  const url = './machine_geometry.json';
  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    // Vanlig fallgrop: dubbelklick på index.html ger file:// och CORS blockar
    // fetch. Visa ett tydligt fel snarare än en kryptisk JS-exception.
    document.body.innerHTML =
      `<div style="padding:20px;font-family:sans-serif;max-width:600px">
        <h2>Kunde inte ladda <code>${url}</code></h2>
        <p>${err.message}</p>
        <p>Kör en lokal webbserver i arbetskatalogen, t.ex.:</p>
        <pre style="background:#eee;padding:8px">python3 -m http.server 8000</pre>
        <p>och öppna sedan <code>http://localhost:8000/</code></p>
      </div>`;
    throw err;
  }
}

async function main() {
  const G = await loadGeometry();

  // ── Scen ───────────────────────────────────────────────────
  const { scene, camera, renderer, controls, gridHelper } = createScene();

  // ── State ──────────────────────────────────────────────────
  let currentHeight = G.rider.default_height_cm;
  let currentGender = G.rider.default_gender;
  let currentSittHeight = G.saddle.top_y;
  let currentSaddleMesh = null;
  let currentSaddleTopAt = makeSaddleTopFn(G, currentSittHeight);

  // ── Ram (Q-noden ritas dynamiskt med sadelstången) ─────────
  const frameAPI = buildFrame(G);
  scene.add(frameAPI.group);

  // ── Sadel ──────────────────────────────────────────────────
  function rebuildSaddle(newSittHeight) {
    currentSittHeight = newSittHeight;
    if (currentSaddleMesh) {
      scene.remove(currentSaddleMesh);
      currentSaddleMesh.geometry.dispose();
      currentSaddleMesh.material.dispose();
    }
    const built = buildSaddle(G, newSittHeight);
    currentSaddleMesh = built.mesh;
    currentSaddleTopAt = built.topAt;
    scene.add(currentSaddleMesh);
    frameAPI.rebuildSaddleStem(currentSaddleTopAt);
  }
  rebuildSaddle(currentSittHeight);

  // ── Styrning (skapas före legs eftersom de behöver B-positioner) ──
  const steering = createSteering(G);

  // ── Driveline, ben, styre ──────────────────────────────────
  const driveline = buildDriveline(scene, G);
  const legs = buildLegs(scene, G, steering);
  const handlebar = buildHandlebar(scene, G);

  // ── Styrmekanismens visualisering ─────────────────────────
  const steeringRender = buildSteeringRender(scene, G, steering);

  // ── Förare ─────────────────────────────────────────────────
  const rider = createRiderController(scene, G, () => currentSaddleTopAt, handlebar);

  // Auto-anpassa sadelhöjd till default-föraren INNAN vi skapar honom
  currentSittHeight = rider.autoSaddleHeight(currentHeight);
  rebuildSaddle(currentSittHeight);
  rider.createRider(currentGender, currentHeight, currentSittHeight);

  // ── sceneState för UI ──────────────────────────────────────
  const sceneState = {
    setHeight(h) { currentHeight = h; },
    setGender(g) {
      currentGender = g;
      rider.createRider(currentGender, currentHeight, currentSittHeight);
    },
    setSittHeight(h) {
      rebuildSaddle(h);
      rider.createRider(currentGender, currentHeight, currentSittHeight);
    },
  };

  // ── Animator ───────────────────────────────────────────────
  const animator = createAnimator({
    scene, camera, renderer, controls, G, gridHelper, steering,
    updateLegs: legs.updateLegs,
    updatePedalCranks: driveline.updatePedalCranks,
    updateRiderPose: (theta) => rider.updatePose(theta),
  });

  // När styret ändras: uppdatera benen och styrets vinkel direkt
  // (även om animationen är pausad). Max styrvinkel: 60° vid steer = ±1.
  const MAX_STEER_DEG = 60;
  steering.onChange(() => {
    const steerVal = steering.getSteer();  // -1..+1
    const steerRad = steerVal * MAX_STEER_DEG * Math.PI / 180;
    handlebar.setSteerAngle(steerRad);
    legs.updateLegs(animator.getTheta());
    rider.updatePose(animator.getTheta());
  });

  // ── UI ─────────────────────────────────────────────────────
  const ui_ctx = { G, animator, rider, sceneState, steering };
  bindUI(ui_ctx);

  // Animatorn anropar onTick varje frame när autoRotate är på.
  // UI-modulen har satt en synk-funktion på ui_ctx.animator_onTick som
  // uppdaterar theta-slidern.
  animator.onTick = (theta) => {
    if (ui_ctx.animator_onTick) ui_ctx.animator_onTick(theta);
  };

  // ── Video ──────────────────────────────────────────────────
  bindVideo({ G, animator, renderer, rider, sceneState, camera, controls });

  // ── Starta ─────────────────────────────────────────────────
  animator.start();
}

main();
