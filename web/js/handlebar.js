// js/handlebar.js
// =============================================================================
// Styret + styrstolpen — ritas i en gemensam Group som kan rotera kring
// den vertikala axeln genom N (styraxelns nedre fästpunkt).
//
// Styrstolpen (N→H) och styret med handtag adderas till samma group.
// Gruppen pivoterar runt N, så styret roterar tillsammans med stolpen.
//
// setSteerAngle(rad) roterar gruppen. Positiv vinkel = vänstersväng (samma
// konvention som steer=+1 i steering.js).
//
// handlebarPosWorld(side, currentSteerRad) returnerar var ett handtag är
// i world-koordinater givet aktuell styrvinkel — används av rider.js för
// IK till händerna.
// =============================================================================
import * as THREE from 'three';
import { makeTube, makeSphere } from './helpers.js';

const FRAME_COLOR = 0x4E342E;       // samma som ramen för styrstolpen
const HANDLEBAR_COLOR = 0x222222;
const GRIP_COLOR = 0x000000;

export function buildHandlebar(scene, G) {
  const h = G.handlebar;
  const cx = h.center[0], cy = h.center[1];
  const N = G.frame.nodes['N'];
  const H = G.frame.nodes['H'];
  const frameTubeRadius = G.frame.tube_radius_cm;

  // Pivoten är vid N (där styrstolpen möter ramen). Gruppen roterar kring
  // den vertikala axeln genom N.
  const group = new THREE.Group();
  group.position.set(N[0], N[1], N[2]);   // gruppens origo vid N
  scene.add(group);

  // Lokala koordinater inom gruppen är relativa N. Komponenter byggs i
  // dessa lokala koordinater så att rotation runt y-axeln roterar allt
  // korrekt kring N.

  // ── Styrstolpen (N → H), uttryckt lokalt ──
  const stemLocalEnd = [H[0] - N[0], H[1] - N[1], H[2] - N[2]];
  const stem = makeTube([0, 0, 0], stemLocalEnd, frameTubeRadius, FRAME_COLOR);
  if (stem) group.add(stem);

  // ── Tvärröret vid H, lokalt ──
  const Hlocal = stemLocalEnd;
  const bar = makeTube(
    [Hlocal[0], Hlocal[1], -h.half_width],
    [Hlocal[0], Hlocal[1], +h.half_width],
    h.tube_radius_cm, HANDLEBAR_COLOR
  );
  if (bar) group.add(bar);

  // ── Handtag (bollar) i ändarna ──
  group.add(makeSphere(
    [Hlocal[0], Hlocal[1], -h.half_width], h.grip_radius_cm, GRIP_COLOR
  ));
  group.add(makeSphere(
    [Hlocal[0], Hlocal[1], +h.half_width], h.grip_radius_cm, GRIP_COLOR
  ));

  // Spara den lokala positionen för handtagen så vi kan räkna ut deras
  // world-position vid given styrvinkel.
  const gripLocalLeft  = [Hlocal[0], Hlocal[1], -h.half_width];
  const gripLocalRight = [Hlocal[0], Hlocal[1], +h.half_width];

  let currentSteerRad = 0;

  function setSteerAngle(rad) {
    currentSteerRad = rad;
    group.rotation.y = rad;
  }

  function getSteerAngle() {
    return currentSteerRad;
  }

  function gripWorld(side) {
    // side: -1 (vänster) eller +1 (höger)
    const local = side < 0 ? gripLocalLeft : gripLocalRight;
    // Rotera kring lokal y med currentSteerRad och översätt till world
    const c = Math.cos(currentSteerRad), s = Math.sin(currentSteerRad);
    const rotated = [
      c * local[0] + s * local[2],
      local[1],
      -s * local[0] + c * local[2],
    ];
    return [N[0] + rotated[0], N[1] + rotated[1], N[2] + rotated[2]];
  }

  return { group, setSteerAngle, getSteerAngle, gripWorld };
}
