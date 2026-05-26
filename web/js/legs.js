// js/legs.js
// =============================================================================
// Jansens benmekanism (4 instanser) + B-axlar, med 3D-fackverk OCH
// styrbar B-position (varje ben har sin egen B som styrs av steering.js).
//
// Kinematik: exakt motsvarighet till jansen.py — cirkelskärningsmetoden.
//
// 3D-fackverk: B/E/F/G dupliceras till z2-planet (z_offset_cm inåt mot
// ramen). D och H är spetsar som binder samman planen via apex-trianglar.
//
// Per-ben B-position: hämtas vid varje frame från steering.js. Detta
// gör att benen reagerar på styrutslag i realtid.
// =============================================================================
import * as THREE from 'three';
import { makeTube } from './helpers.js';

const LEG_COLOR_Z1 = 0x1565C0;
const LEG_COLOR_Z2 = 0x42A5F5;
const B_AXIS_COLOR = 0x222222;

const Z2_NODES = new Set(['B', 'E', 'F', 'G']);
const SIGNS = [-1, -1, +1, -1, +1];

function circleIntersect(c1, r1, c2, r2, sign) {
  const dx = c2[0] - c1[0], dy = c2[1] - c1[1];
  const d = Math.sqrt(dx * dx + dy * dy);
  if (d > r1 + r2 + 1e-9 || d < Math.abs(r1 - r2) - 1e-9) return null;
  const a = (r1 * r1 - r2 * r2 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, r1 * r1 - a * a));
  const mx = c1[0] + (a / d) * dx;
  const my = c1[1] + (a / d) * dy;
  return [mx + sign * h * (-dy) / d, my + sign * h * dx / d];
}

/**
 * Beräkna Jansen-pose med ett angivet B i lokala koordinater.
 * Detta är skillnaden mot tidigare: B var fix från G.leg.B_local, nu
 * får varje ben sin egen B beräknad från steering.js.
 */
export function jansenPose(theta, G, B_local) {
  const C = G.leg.constants;
  const B = B_local || G.leg.B_local;
  const A = [0, 0];
  const C_pt = [C.AC * Math.cos(theta), -C.AC * Math.sin(theta)];

  const D = circleIntersect(C_pt, C.CD, B, C.BD, SIGNS[0]); if (!D) return null;
  const E = circleIntersect(D, C.DE, B, C.BE, SIGNS[1]);    if (!E) return null;
  const F = circleIntersect(C_pt, C.CF, B, C.BF, SIGNS[2]); if (!F) return null;
  const G_pt = circleIntersect(E, C.EG, F, C.FG, SIGNS[3]); if (!G_pt) return null;
  const H = circleIntersect(F, C.FH, G_pt, C.GH, SIGNS[4]); if (!H) return null;
  return { A, B, C: C_pt, D, E, F, G: G_pt, H };
}

/**
 * Konvertera världs-B (från steering) till lokala (ABx, ABy) i Jansen-frame.
 *   Framben (yaw=0):   lokal x = +(världs-x - A.x), lokal y = -(världs-y - A.y)
 *   Bakben (yaw=180):  lokal x = -(världs-x - A.x), lokal y = -(världs-y - A.y)
 */
function worldBToLocal(BWorld, A_world, isRear) {
  const dx = BWorld[0] - A_world[0];
  const dy = BWorld[1] - A_world[1];
  return [isRear ? -dx : dx, -dy];
}

export function buildLegs(scene, G, steering) {
  const legGroups = [];
  const tubeRadius = G.leg.tube_radius_cm;
  const zOffset = G.leg.z_offset_cm;

  const allLinks = [
    ...G.leg.links_z1.map(([a, b]) => ({ a, b, color: LEG_COLOR_Z1 })),
    ...G.leg.links_z2.map(([a, b]) => ({ a, b, color: LEG_COLOR_Z2 })),
    ...G.leg.links_cross.map(([a, b]) => ({ a, b, color: LEG_COLOR_Z2 })),
    ...G.leg.links_apex.map(([a, b]) => ({ a, b, color: LEG_COLOR_Z2 })),
  ];

  // Bygg mesh-strukturen för varje ben
  for (const leg of G.legs) {
    const group = new THREE.Group();
    group.userData = { ...leg, linkMeshes: {} };

    for (const link of allLinks) {
      const geom = new THREE.CylinderGeometry(tubeRadius, tubeRadius, 1, 12);
      const mat = new THREE.MeshStandardMaterial({
        color: link.color, roughness: 0.5, metalness: 0.3
      });
      const mesh = new THREE.Mesh(geom, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      group.add(mesh);
      group.userData.linkMeshes[link.a + link.b] = mesh;
    }
    scene.add(group);
    legGroups.push(group);
  }

  // B-axlar: nu DYNAMISKA — varje ben har sin egen axel som rör sig med B.
  // Vi skapar ett mesh per ben och uppdaterar dess position/rotation varje frame.
  const bAxisMeshes = {};   // keyed by leg.label
  for (const leg of G.legs) {
    // Skapa en placeholder-cylinder; position och längd uppdateras dynamiskt
    const geom = new THREE.CylinderGeometry(0.7, 0.7, 1, 12);
    const mat = new THREE.MeshStandardMaterial({
      color: B_AXIS_COLOR, roughness: 0.5, metalness: 0.5
    });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.castShadow = true;
    scene.add(mesh);
    bAxisMeshes[leg.label] = mesh;
  }

  function zFor(nodeName, legZ) {
    if (nodeName.endsWith('2')) {
      return legZ > 0 ? legZ - zOffset : legZ + zOffset;
    }
    return legZ;
  }

  /**
   * Uppdatera ett mesh så att det blir en cylinder mellan två punkter.
   * Återanvänds för B-axeln vid varje frame.
   */
  function updateMeshAsCylinder(mesh, p1, p2) {
    const v1 = new THREE.Vector3(p1[0], p1[1], p1[2]);
    const v2 = new THREE.Vector3(p2[0], p2[1], p2[2]);
    const dir = new THREE.Vector3().subVectors(v2, v1);
    const len = dir.length();
    mesh.position.copy(v1).add(v2).multiplyScalar(0.5);
    const up = new THREE.Vector3(0, 1, 0);
    const q = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
    mesh.setRotationFromQuaternion(q);
    mesh.scale.y = len;
  }

  function updateLegs(theta_global) {
    // Hämta aktuella B-positioner från steering (alla fyra ben)
    const bPositions = steering.getAllBPositions();

    for (const group of legGroups) {
      const leg = group.userData;
      const yawRad = leg.yaw_deg * Math.PI / 180;
      const phaseRad = leg.phase_offset_deg * Math.PI / 180;
      const isRear = leg.label.startsWith('rear');

      // Hitta benets nuvarande B-position i världen från steering
      const BWorld = bPositions[leg.label];
      if (!BWorld) continue;
      // Konvertera till lokala Jansen-koordinater
      const B_local = worldBToLocal(BWorld, leg.A_world, isRear);

      let theta_for_leg = leg.reverse ? -theta_global : theta_global;
      theta_for_leg += phaseRad;

      const pose = jansenPose(theta_for_leg, G, B_local);
      if (!pose) continue;

      const mirror_x = Math.cos(yawRad);
      const ax = leg.A_world[0], ay = leg.A_world[1], legZ = leg.z;

      const world = {};
      for (const [name, p] of Object.entries(pose)) {
        const x = mirror_x * p[0] + ax;
        const y = -p[1] + ay;
        world[name] = [x, y, legZ];
        if (Z2_NODES.has(name)) {
          world[name + '2'] = [x, y, zFor(name + '2', legZ)];
        }
      }

      for (const link of allLinks) {
        const mesh = leg.linkMeshes[link.a + link.b];
        const p1 = world[link.a], p2 = world[link.b];
        if (!p1 || !p2) continue;
        updateMeshAsCylinder(mesh, p1, p2);
      }

      // Uppdatera B-axeln: går från sidoramen (där pivoten sitter, z=±SIDE_Z)
      // ut till B1 (vid leg.z), passerar genom B2 (på vägen vid SIDE_Z*sign).
      // Egentligen sticker den ut från sidoramen som är vid samma z som B2.
      // Här utgår vi från att axeln går från B2 till B1 — det är samma
      // (x,y) men olika z. Sidoramen själv stöttar B-axeln vid B2:s z-läge.
      const b1Pos = world['B'];
      const b2Pos = world['B2'];
      if (b1Pos && b2Pos) {
        updateMeshAsCylinder(bAxisMeshes[leg.label], b1Pos, b2Pos);
      }
    }
  }

  updateLegs(0);
  return { legGroups, updateLegs };
}
