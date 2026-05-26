// js/handlebar.js
// =============================================================================
// Styret: ett tvärgående rör med två tjockare handtag i ändarna.
// Geometri från G.handlebar (center, half_width, tube_radius_cm, grip_radius_cm).
// =============================================================================
import * as THREE from 'three';
import { makeTube, makeSphere } from './helpers.js';

const HANDLEBAR_COLOR = 0x222222;
const GRIP_COLOR = 0x000000;

export function buildHandlebar(scene, G) {
  const h = G.handlebar;
  const cx = h.center[0], cy = h.center[1];

  const bar = makeTube(
    [cx, cy, -h.half_width],
    [cx, cy, +h.half_width],
    h.tube_radius_cm, HANDLEBAR_COLOR
  );
  if (bar) scene.add(bar);

  scene.add(makeSphere([cx, cy, -h.half_width], h.grip_radius_cm, GRIP_COLOR));
  scene.add(makeSphere([cx, cy, +h.half_width], h.grip_radius_cm, GRIP_COLOR));
}
