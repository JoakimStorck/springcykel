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
  const { scene, camera, renderer, controls, G, gridHelper, steering } = ctx;
  let theta = 0;             // vevvinkel (rad)
  let rpm = G.mechanics.default_rpm;
  let autoRotate = false;
  const gearRatio = G.mechanics.gear_ratio;
  const stepLengthCm = G.mechanics.step_length_cm;

  // GridHelper-tillstånd. Marken roterar och translaterar för att skapa
  // illusionen av att maskinen färdas genom rummet.
  // Vid rak körning: ren translation i -x, med modulo så det wrappar.
  // Vid sväng: rotation runt svängcentrum (en punkt åt sidan om maskinen).
  let groundShiftStraight = 0;
  const GRID_CELL_CM = 10;
  const GRID_SIZE_CM = 400;   // gridHelper är 400 cm bred

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
      const dTheta = crankOmega * dt;
      theta += dTheta;

      // Framdrift per frame (cm)
      const dShift = (dTheta / (2 * Math.PI)) * stepLengthCm;

      // Markens rörelse beror på om vi svänger eller kör rakt
      if (gridHelper && steering) {
        const steerVal = steering.getSteer();
        const R = steering.getTurningRadius();   // cm, Infinity vid rak

        if (Math.abs(steerVal) > 1e-3 && isFinite(R)) {
          // Sväng: rotera marken kring svängcentrum.
          // Svängcentrum i världen: åt sidan om maskinen. Vid steerVal > 0
          // (vänstersväng) ligger centrum i world -z; vid < 0 i world +z.
          // Maskinen färdas i +x, så svängcentrum är vid (0, 0, ±R).
          const dPhi = dShift / R;  // vinkeländring (rad)
          // Marken roterar i motsatt riktning som maskinens rörelse genom 
          // världen; för vänstersväng (steer > 0) ska marken under maskinen
          // sopa förbi från höger till vänster, vilket motsvarar rotation 
          // av marken i positiv y-led.
          const sign = steerVal > 0 ? +1 : -1;
          const centerZ = sign * R;
          const rotAngle = sign * dPhi;
          rotateGridAround(gridHelper, 0, centerZ, rotAngle);
          // Återställ "rak" translation gradvis så det inte hoppar när vi 
          // går från sväng till rak
          groundShiftStraight = 0;
        } else {
          // Rak körning: ren translation i -x med modulo
          // Återställ rotation om vi tidigare svängde
          if (gridHelper.rotation.y !== 0 || gridHelper.position.z !== 0) {
            gridHelper.rotation.y = 0;
            gridHelper.position.z = 0;
            gridHelper.position.x = 0;
          }
          groundShiftStraight = (groundShiftStraight + dShift) % GRID_CELL_CM;
          gridHelper.position.x = -groundShiftStraight;
        }

        // Wrappa position så marken aldrig glider för långt från origo
        // (visuellt omöjligt att skilja eftersom rutmönstret är repetitivt)
        wrapGridPosition(gridHelper);
      }

      applyTheta();
      if (api.onTick) api.onTick(theta);
    }
    controls.update();
    renderer.render(scene, camera);
  }

  return api;
}

/**
 * Rotera gridHelper med vinkel `angle` (rad) kring punkten (cx, 0, cz) i världen,
 * runt y-axeln. Tar hand om både position och rotation.
 */
function rotateGridAround(gridHelper, cx, cz, angle) {
  // Translatera position relativt centrum
  const px = gridHelper.position.x - cx;
  const pz = gridHelper.position.z - cz;
  const c = Math.cos(angle), s = Math.sin(angle);
  // R_y(angle): (x, z) → (x·c + z·s, -x·s + z·c)
  const npx = px * c + pz * s;
  const npz = -px * s + pz * c;
  gridHelper.position.x = npx + cx;
  gridHelper.position.z = npz + cz;
  gridHelper.rotation.y += angle;
}

/**
 * Wrappa gridHelper position så den hålls nära origo. Rutmönstret är 
 * repetitivt så det är osynligt så länge vi wrappar med multiplar av 
 * GRID_CELL_CM. Men vid rotation kan gridens linjer inte wrappas perfekt 
 * eftersom de inte längre är axel-aligned. Vi accepterar att vid stora 
 * roterade förflyttningar kan kanten av griden bli synlig — då räcker 
 * med en grövre wrap som behåller den nära maskinen.
 */
function wrapGridPosition(gridHelper) {
  const LIMIT = 100;   // cm; wrap när positionen är mer än så här långt bort
  const STEP = 100;    // wrap-steg
  while (gridHelper.position.x > LIMIT) gridHelper.position.x -= STEP;
  while (gridHelper.position.x < -LIMIT) gridHelper.position.x += STEP;
  while (gridHelper.position.z > LIMIT) gridHelper.position.z -= STEP;
  while (gridHelper.position.z < -LIMIT) gridHelper.position.z += STEP;
}
