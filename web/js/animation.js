// js/animation.js
// =============================================================================
// Animationsloop. Driver vevvinkeln theta över tid med tids-baserad rörelse
// (dt × ω) så hastigheten är oberoende av framerate.
//
// Globalt theta är VEVVINKEL (Jansens vinkel — driver benen).
// Pedalvinkeln = theta / gear_ratio (utväxlingen).
//
// Speed-beräkning:
//   speed_cmPerMin = pedal_rpm × gear_ratio × step_length_cm
//   speed_kmh      = speed_cmPerMin × 0.0006
// =============================================================================

export function speedFromRPM(rpm, G) {
  const cmPerMin = rpm * G.mechanics.gear_ratio * G.mechanics.step_length_cm;
  return cmPerMin * 0.0006;
}

/**
 * Skapa animationscontroller.
 *
 * @param ctx kontextobjekt:
 *   { scene, camera, renderer, controls,
 *     G,
 *     updateLegs(theta),
 *     updatePedalCranks(pedalAngle),
 *     updateRiderPose(theta) }
 *
 * @returns { start(), setTheta(thetaCrank), getTheta(),
 *            setRPM(rpm), getRPM(),
 *            setAutoRotate(bool), isAutoRotate() }
 */
export function createAnimator(ctx) {
  const { scene, camera, renderer, controls, G } = ctx;
  let theta = 0;             // vevvinkel (rad)
  let rpm = G.mechanics.default_rpm;
  let autoRotate = false;
  const gearRatio = G.mechanics.gear_ratio;

  function applyTheta() {
    const pedalAngle = theta / gearRatio;
    ctx.updateLegs(theta);
    ctx.updatePedalCranks(pedalAngle);
    ctx.updateRiderPose(theta);
  }

  let lastFrameTime = performance.now();
  const api = {
    onTick: null,   // valfri callback (theta) => void, sätts av main/ui
    start() {
      applyTheta();
      loop();
    },
    setTheta(thetaCrank) { theta = thetaCrank; applyTheta(); },
    getTheta() { return theta; },
    setRPM(newRpm) { rpm = newRpm; },
    getRPM() { return rpm; },
    setAutoRotate(b) { autoRotate = b; lastFrameTime = performance.now(); },
    isAutoRotate() { return autoRotate; },
  };

  function loop() {
    requestAnimationFrame(loop);
    const now = performance.now();
    const dt = (now - lastFrameTime) / 1000;
    lastFrameTime = now;

    if (autoRotate) {
      const crankOmega = rpm * gearRatio * 2 * Math.PI / 60;
      theta += crankOmega * dt;
      applyTheta();
      if (api.onTick) api.onTick(theta);
    }
    controls.update();
    renderer.render(scene, camera);
  }

  return api;
}
