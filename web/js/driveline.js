// js/driveline.js
// =============================================================================
// Drivlinan: pedalvev, fram- och bakvevaxlar med drev, kedjor och
// pedalvevarmar med pedalplattor.
//
// Z-stack (driver av Python via G.drivelines_z, ny geometri):
//   ramcentrum vid z=0
//   drev        z=±3
//   sidoram     z=±10 (RAM_Z)  — lagring för alla tre vevaxlar
//   ben-vevarm  z=±10..±15     (fram/bak-vevaxlarna)
//   pedal-vevarm z=±10..±12   (utanpå sidoramen)
//   pedaltapp   z=±12..±22    (10 cm utstick från pedal-vevarm)
//   pedalplatta z=±17 (mitten av pedaltappen — där foten vilar)
//
// Pedalvevarmen sticker ut radiellt från pedalaxeln (vid x=P) i x-y-planet
// och roterar med pedalvinkeln. Pedalplattan följer med vevarmens spets men
// förblir horisontell (inte roterad).
// =============================================================================
import * as THREE from 'three';
import { makeTube, makeDisk } from './helpers.js';

const AXLE_COLOR = 0x222222;
const DREV_COLOR = 0x1565C0;
const LAGER_COLOR = 0x444444;
const ARM_COLOR = 0x424242;
const CHAIN_COLOR = 0x444444;
const PLATE_COLOR = 0x212121;

export function buildDriveline(scene, G) {
  const group = new THREE.Group();
  const Z = G.drivelines_z;
  const ramZ = Z.ram_z;                  // = 10.0
  const pedalVevarmZ = Z.pedal_vevarm_z; // = 12.0
  const pedalTappOuterZ = Z.pedal_tapp_outer_z; // = 22.0
  const benVevarmZ = Z.ben_vevarm_z;     // = 15.0

  // ── Statiska delar: axlar, lagerhus, drev ────────────────────
  for (const axleName of ['pedal', 'rear', 'front']) {
    const axle = G.axles[axleName];
    const cx = axle.center[0], cy = axle.center[1];

    // Yttre ände för axeln:
    //   pedal: pedalVevarmZ (=12) — där pedalvevarmen sätts på
    //   fram/bak: benVevarmZ (=15) — där C-punkten ankrar på benet
    const axleOuterZ = (axleName === 'pedal') ? pedalVevarmZ : benVevarmZ;

    const axleMesh = makeTube(
      [cx, cy, -axleOuterZ], [cx, cy, +axleOuterZ], 0.7, AXLE_COLOR
    );
    if (axleMesh) group.add(axleMesh);

    // Lagerhus — ETT per sidoram, vid z=±ramZ för alla tre axlar.
    // (Alla tre vevaxlar passerar nu genom sidoramen vid z=±10.)
    const lagerHalfWidth = 1.5;
    const lagerLeft = makeTube(
      [cx, cy, -ramZ - lagerHalfWidth], [cx, cy, -ramZ + lagerHalfWidth],
      2.0, LAGER_COLOR
    );
    if (lagerLeft) group.add(lagerLeft);
    const lagerRight = makeTube(
      [cx, cy, +ramZ - lagerHalfWidth], [cx, cy, +ramZ + lagerHalfWidth],
      2.0, LAGER_COLOR
    );
    if (lagerRight) group.add(lagerRight);

    if (axle.drev_left_z !== null) {
      group.add(makeDisk(
        [cx, cy, axle.drev_left_z], [0, 0, 1], axle.drev_r, 0.8, DREV_COLOR
      ));
    }
    if (axle.drev_right_z !== null) {
      group.add(makeDisk(
        [cx, cy, axle.drev_right_z], [0, 0, 1], axle.drev_r, 0.8, DREV_COLOR
      ));
    }
  }

  // ── Kedjor (förenklade: bara övre och undre tangentlinjer) ───
  group.add(makeChain(
    G.axles.pedal.center, G.axles.pedal.drev_r, G.axles.pedal.drev_left_z,
    G.axles.rear.center, G.axles.rear.drev_r, G.axles.rear.drev_left_z
  ));
  group.add(makeChain(
    G.axles.pedal.center, G.axles.pedal.drev_r, G.axles.pedal.drev_right_z,
    G.axles.front.center, G.axles.front.drev_r, G.axles.front.drev_right_z
  ));

  scene.add(group);

  // ── Pedalvevarmar och pedalplattor (animerade) ───────────────
  const left = buildPedalCrank(scene, G, -1);
  const right = buildPedalCrank(scene, G, +1);

  function updatePedalCranks(pedalAngle) {
    const cx = G.axles.pedal.center[0];
    const cy = G.axles.pedal.center[1];
    const armLen = G.pedal.crank_radius_cm;
    const plateZ = G.pedal.plate_z_cm;

    const leftRotZ = -pedalAngle;
    const rightRotZ = -pedalAngle + Math.PI;

    left.group.rotation.z = leftRotZ;
    right.group.rotation.z = rightRotZ;

    left.plate.position.set(
      cx - armLen * Math.sin(leftRotZ),
      cy + armLen * Math.cos(leftRotZ),
      -plateZ
    );
    left.plate.rotation.set(0, 0, 0);

    right.plate.position.set(
      cx - armLen * Math.sin(rightRotZ),
      cy + armLen * Math.cos(rightRotZ),
      +plateZ
    );
    right.plate.rotation.set(0, 0, 0);
  }

  updatePedalCranks(0);

  return { group, updatePedalCranks };
}

function buildPedalCrank(scene, G, side) {
  // side = -1 (vänster) eller +1 (höger).
  // Vevarmen sitter UTANPÅ ramen, med innerkanten vid z=±vevarmAnchorZ
  // (= 12). Vevarmen är 2 cm tjock i z-led, så centrum vid z=±13.
  const armLen = G.pedal.crank_radius_cm;
  const armWidth = G.pedal.arm_width_cm;
  const armThickness = G.pedal.arm_thickness_z_cm;
  const vevarmAnchorZ = G.pedal.vevarm_anchor_z;   // = 12.0
  const armCenterZ = side * (vevarmAnchorZ + armThickness / 2);  // ±13

  const group = new THREE.Group();
  group.position.set(G.axles.pedal.center[0], G.axles.pedal.center[1], 0);

  const armGeom = new THREE.BoxGeometry(armWidth, armLen, armThickness);
  const armMat = new THREE.MeshStandardMaterial({
    color: ARM_COLOR, roughness: 0.4, metalness: 0.7
  });
  const arm = new THREE.Mesh(armGeom, armMat);
  arm.castShadow = true;
  arm.position.set(0, armLen / 2, armCenterZ);
  group.add(arm);
  scene.add(group);

  const [plateLen, plateThick, plateZExt] = G.pedal.plate_size_cm;
  const plateGeom = new THREE.BoxGeometry(plateLen, plateThick, plateZExt);
  const plateMat = new THREE.MeshStandardMaterial({
    color: PLATE_COLOR, roughness: 0.6, metalness: 0.3
  });
  const plate = new THREE.Mesh(plateGeom, plateMat);
  plate.castShadow = true;
  scene.add(plate);

  return { group, plate };
}

function makeChain(p1, r1, z1, p2, r2, z2) {
  const z = z1;
  const cx1 = p1[0], cy1 = p1[1];
  const cx2 = p2[0], cy2 = p2[1];
  const dx = cx2 - cx1, dy = cy2 - cy1;
  const d = Math.sqrt(dx * dx + dy * dy);
  const px = -dy / d, py = dx / d;

  const t1 = [cx1 + r1 * px, cy1 + r1 * py, z];
  const t2 = [cx2 + r2 * px, cy2 + r2 * py, z];
  const b1 = [cx1 - r1 * px, cy1 - r1 * py, z];
  const b2 = [cx2 - r2 * px, cy2 - r2 * py, z];

  const upper = makeTube(t1, t2, 0.4, CHAIN_COLOR);
  const lower = makeTube(b1, b2, 0.4, CHAIN_COLOR);
  const grp = new THREE.Group();
  if (upper) grp.add(upper);
  if (lower) grp.add(lower);
  return grp;
}
