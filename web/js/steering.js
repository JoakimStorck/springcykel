// js/steering.js
// =============================================================================
// Styrmekanism — triangelmekanism för per-ben B-leder.
//
// Varje ben har sin egen B-led som rör sig i en cirkulär båge kring en
// pivot på ramen (P för bakben, M för framben). Båda sidor av maskinen
// har separata triangelstöd. Vid styrutslag förlängs den aktiva sidans
// AB-länk, vilket vrider B-leden längs bågen.
//
// Konvention för styrutslag (steerValue):
//   -1.0  = full högersväng (höger sida förlänger AB)
//    0.0  = rakt (båda sidor vid baseline)
//   +1.0  = full vänstersväng (vänster sida förlänger AB)
//
// Endast förlängning av AB stöds (Jansens kinematik tål inte förkortning
// — se whitepaper).
// =============================================================================

/**
 * Cirkelskärning: hitta punkt på cirkeln (c1, r1) och cirkeln (c2, r2)
 * som ligger närmast en referenspunkt. Båda cirklarna är 2D.
 *
 * Returnerar null om cirklarna inte skär varandra.
 */
function circleIntersectNear(c1, r1, c2, r2, refPoint) {
  const dx = c2[0] - c1[0], dy = c2[1] - c1[1];
  const d = Math.sqrt(dx * dx + dy * dy);
  if (d > r1 + r2 + 1e-9 || d < Math.abs(r1 - r2) - 1e-9) return null;
  const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, r1 * r1 - a * a));
  const dirx = dx / d, diry = dy / d;
  const perpx = -diry, perpy = dirx;
  const midx = c1[0] + a * dirx, midy = c1[1] + a * diry;
  const cand1 = [midx + h * perpx, midy + h * perpy];
  const cand2 = [midx - h * perpx, midy - h * perpy];
  const d1 = Math.hypot(cand1[0] - refPoint[0], cand1[1] - refPoint[1]);
  const d2 = Math.hypot(cand2[0] - refPoint[0], cand2[1] - refPoint[1]);
  return d1 < d2 ? cand1 : cand2;
}

/**
 * Skapa en styrningskontroller. Returnerar API för:
 *   - setSteer(value): sätt styrutslag i [-1, +1]
 *   - getSteer(): aktuellt styrutslag
 *   - getBPosition(supportLabel): returnera nuvarande B-position i världen
 *     för givet ben ('rear_left', 'rear_right', 'front_left', 'front_right')
 *   - getABOffset(supportLabel): aktuell AB-förlängning för det benet (cm)
 *   - onChange(callback): registrera lyssnare som körs när styret ändras
 */
export function createSteering(G) {
  const cfg = G.steering;
  let steerValue = cfg.steer_default;
  const listeners = [];

  // Indexera supports efter label för snabb uppslagning
  const supportsByLabel = {};
  for (const s of cfg.supports) supportsByLabel[s.label] = s;

  /**
   * Beräkna AB-offset för ett givet ben givet aktuellt styrutslag.
   *   - Vänstersväng (steerValue > 0): vänster sida förlänger, höger vid baseline
   *   - Högersväng (steerValue < 0): höger sida förlänger, vänster vid baseline
   *   - Rakt (steerValue = 0): båda vid baseline
   */
  function abOffsetForSide(side, steer) {
    if (steer > 0 && side === 'left')  return steer * cfg.AB_max_offset_cm;
    if (steer < 0 && side === 'right') return -steer * cfg.AB_max_offset_cm;
    return 0;
  }

  /**
   * Beräkna B-position i världen (x, y) för ett triangelstöd.
   * B ligger på cirkeln kring A med radie AB_baseline + offset, och
   * på cirkeln kring pivoten med fast längd support_length.
   * Vi väljer den lösning som ligger närmast B_baseline.
   */
  function computeBPosition(support, abOffset) {
    const AB = cfg.AB_baseline_cm + abOffset;
    return circleIntersectNear(
      support.A_xy, AB,
      support.pivot_xy, support.support_length_cm,
      support.B_baseline_xy
    );
  }

  function getABOffset(label) {
    const s = supportsByLabel[label];
    if (!s) return 0;
    return abOffsetForSide(s.side, steerValue);
  }

  function getBPosition(label) {
    const s = supportsByLabel[label];
    if (!s) return null;
    const offset = abOffsetForSide(s.side, steerValue);
    const bxy = computeBPosition(s, offset);
    if (!bxy) return null;
    return [bxy[0], bxy[1], s.z];
  }

  /**
   * Returnera B-positionerna för alla fyra ben i ett enda objekt.
   * Praktiskt för legs.js att hämta in en sväng vid varje frame.
   */
  function getAllBPositions() {
    const out = {};
    for (const s of cfg.supports) {
      out[s.label] = getBPosition(s.label);
    }
    return out;
  }

  function setSteer(value) {
    const clamped = Math.max(cfg.steer_range[0],
                             Math.min(cfg.steer_range[1], value));
    if (clamped !== steerValue) {
      steerValue = clamped;
      for (const cb of listeners) cb(steerValue);
    }
  }

  function getSteer() { return steerValue; }

  function onChange(cb) { listeners.push(cb); }

  return {
    setSteer,
    getSteer,
    getBPosition,
    getABOffset,
    getAllBPositions,
    onChange,
    supports: cfg.supports,   // exponera för UI/visualisering
    config: cfg,
  };
}
