// js/frame.js
// =============================================================================
// Ramen — 3D-konstruktion med sidoramar vid z=±5 och tvärbalkar.
//
// Sadelstolpen är dynamisk (längd beror på sadelhöjd). Den går från
// mittpunkten på A_rear-tvärbalken (x=0, y=A_rear.y, z=0) upp till sadelns
// undersida. För att stolpen ska anslutas till båda sidoramarna ritar vi
// dessutom korta stöd från A_rear_left/right till stolpens bas.
//
// Triangelstöden för styrmekanismen (P→B och M→B per ben) ritas separat
// av steering-renderaren — de hör inte till själva ramen.
// =============================================================================
import * as THREE from 'three';
import { makeTube, makeSphere } from './helpers.js';

const FRAME_COLOR = 0x4E342E;
const NODE_COLOR = 0x2E1A0E;

export function buildFrame(G) {
  const group = new THREE.Group();
  const radius = G.frame.tube_radius_cm;

  // Statiska ramlänkar (alla utom sadelstolpen)
  for (const [n1, n2] of G.frame.links) {
    const p1 = G.frame.nodes[n1];
    const p2 = G.frame.nodes[n2];
    if (!p1 || !p2) continue;
    const tube = makeTube(p1, p2, radius, FRAME_COLOR);
    if (tube) group.add(tube);
  }

  // Ramnoder som små bollar (utom Q som hör till sadelstolpen)
  for (const [name, pos] of Object.entries(G.frame.nodes)) {
    if (name === 'Q') continue;
    group.add(makeSphere(pos, radius * 1.6, NODE_COLOR));
  }

  // Sadelstolpens bas — vid mittpunkten mellan A_rear_left och A_rear_right
  const A_rear_left = G.frame.nodes['A_rear_left'];
  const A_rear_right = G.frame.nodes['A_rear_right'];
  const stemBase = [
    (A_rear_left[0] + A_rear_right[0]) / 2,
    (A_rear_left[1] + A_rear_right[1]) / 2,
    0,   // centralt vid z=0
  ];

  // Korta diagonala stöd från sidoramarna upp till sadelstolpens bas.
  // Dessa stabiliserar stolpen i z-led.
  // (Vi använder samma noder som tvärbalken redan ligger på, så detta är
  // egentligen två extra meshar i samma position som tvärbalken — vi
  // hoppar över dem för att undvika dubbelritning.)

  let stem = null;

  function rebuildSaddleStem(topAt) {
    if (stem) {
      group.remove(stem);
      stem.geometry.dispose();
      stem.material.dispose();
      stem = null;
    }
    const topAtStem = topAt(stemBase[0]);
    const bottomAtStem = topAtStem - G.saddle.thickness;
    const p2 = [stemBase[0], bottomAtStem, stemBase[2]];
    stem = makeTube(stemBase, p2, radius, FRAME_COLOR);
    if (stem) group.add(stem);
  }

  return { group, rebuildSaddleStem };
}
