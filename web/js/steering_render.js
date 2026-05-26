// js/steering_render.js
// =============================================================================
// Visuell rendering av styrmekanismen: triangelstöd och teleskop.
//
// Per ben ritas:
//   - Teleskop (A → B): heldraget rör vars längd ändras med AB-offset
//   - Triangelstöd (pivot → B): fast längd, gångjärn vid pivoten
//
// Inga av dessa hör till ramen (ramen byter inte form med styret), så de
// måste uppdateras varje frame separat. Vi använder samma cylinder-mesh-
// strategi som legs.js — en mesh per element, uppdatera position/rotation/
// scale varje frame.
//
// Lägger även till stolpar vid varje B-position (små bollar) så det syns
// var leden ligger.
// =============================================================================
import * as THREE from 'three';

const TELESCOPE_COLOR = 0x8B4513;      // brunaktig, för att skilja från ramen
const SUPPORT_COLOR = 0x5D4037;
const B_NODE_COLOR = 0xC62828;          // röd boll för B-positionen
const PIVOT_NODE_COLOR = 0x2E1A0E;

export function buildSteeringRender(scene, G, steering) {
  const meshes = {};   // keyed by support.label, each has { telescope, support, bNode, pivotNode }

  for (const sup of steering.supports) {
    // Teleskop: cylinder från A till B (uppdateras varje frame)
    const telescopeGeom = new THREE.CylinderGeometry(0.8, 0.8, 1, 12);
    const telescopeMat = new THREE.MeshStandardMaterial({
      color: TELESCOPE_COLOR, roughness: 0.4, metalness: 0.4
    });
    const telescope = new THREE.Mesh(telescopeGeom, telescopeMat);
    telescope.castShadow = true;
    scene.add(telescope);

    // Stödstång: cylinder från pivot till B (uppdateras varje frame)
    const supportGeom = new THREE.CylinderGeometry(0.7, 0.7, 1, 12);
    const supportMat = new THREE.MeshStandardMaterial({
      color: SUPPORT_COLOR, roughness: 0.5, metalness: 0.3
    });
    const support = new THREE.Mesh(supportGeom, supportMat);
    support.castShadow = true;
    scene.add(support);

    // Pivotbollen (fix position)
    const pivotGeom = new THREE.SphereGeometry(1.5, 16, 12);
    const pivotMat = new THREE.MeshStandardMaterial({
      color: PIVOT_NODE_COLOR, roughness: 0.4, metalness: 0.4
    });
    const pivotNode = new THREE.Mesh(pivotGeom, pivotMat);
    pivotNode.position.set(sup.pivot_xy[0], sup.pivot_xy[1], sup.z);
    pivotNode.castShadow = true;
    scene.add(pivotNode);

    // B-bollen (rörlig position)
    const bGeom = new THREE.SphereGeometry(1.8, 16, 12);
    const bMat = new THREE.MeshStandardMaterial({
      color: B_NODE_COLOR, roughness: 0.4, metalness: 0.4
    });
    const bNode = new THREE.Mesh(bGeom, bMat);
    bNode.castShadow = true;
    scene.add(bNode);

    meshes[sup.label] = { telescope, support, pivotNode, bNode, supportData: sup };
  }

  function updateMeshAsCylinder(mesh, p1, p2) {
    const v1 = new THREE.Vector3(p1[0], p1[1], p1[2]);
    const v2 = new THREE.Vector3(p2[0], p2[1], p2[2]);
    const dir = new THREE.Vector3().subVectors(v2, v1);
    const len = dir.length();
    if (len < 0.001) return;
    mesh.position.copy(v1).add(v2).multiplyScalar(0.5);
    const up = new THREE.Vector3(0, 1, 0);
    const q = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
    mesh.setRotationFromQuaternion(q);
    mesh.scale.y = len;
  }

  function updateSteering() {
    for (const sup of steering.supports) {
      const m = meshes[sup.label];
      const BWorld = steering.getBPosition(sup.label);
      if (!BWorld) continue;

      const A = [sup.A_xy[0], sup.A_xy[1], sup.z];
      const pivot = [sup.pivot_xy[0], sup.pivot_xy[1], sup.z];

      // Teleskopet (A → B)
      updateMeshAsCylinder(m.telescope, A, BWorld);
      // Stödstången (pivot → B)
      updateMeshAsCylinder(m.support, pivot, BWorld);
      // B-bollen
      m.bNode.position.set(BWorld[0], BWorld[1], BWorld[2]);
    }
  }

  updateSteering();
  // Lyssna på steerings förändringar
  steering.onChange(() => updateSteering());

  return { updateSteering };
}
