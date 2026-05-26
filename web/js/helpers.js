// js/helpers.js
// =============================================================================
// Gemensamma mesh-primitiver: cylinder mellan två punkter, sfär, skiva.
// Inga geometri-data — bara Three.js-helpers.
// =============================================================================
import * as THREE from 'three';

/**
 * Cylinder mellan två punkter p1 och p2. Roteras automatiskt.
 * @returns {THREE.Mesh|null} null om punkterna sammanfaller.
 */
export function makeTube(p1, p2, radius, color) {
  const v1 = new THREE.Vector3(p1[0], p1[1], p1[2]);
  const v2 = new THREE.Vector3(p2[0], p2[1], p2[2]);
  const dir = new THREE.Vector3().subVectors(v2, v1);
  const len = dir.length();
  if (len < 0.001) return null;

  const geom = new THREE.CylinderGeometry(radius, radius, len, 12);
  const mat = new THREE.MeshStandardMaterial({
    color, roughness: 0.5, metalness: 0.3
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  mesh.position.copy(v1).add(v2).multiplyScalar(0.5);
  const up = new THREE.Vector3(0, 1, 0);
  const q = new THREE.Quaternion().setFromUnitVectors(up, dir.normalize());
  mesh.setRotationFromQuaternion(q);
  return mesh;
}

export function makeSphere(pos, radius, color) {
  const geom = new THREE.SphereGeometry(radius, 16, 12);
  const mat = new THREE.MeshStandardMaterial({
    color, roughness: 0.4, metalness: 0.4
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.set(pos[0], pos[1], pos[2]);
  mesh.castShadow = true;
  return mesh;
}

/**
 * Tunn skiva (cylinder med liten höjd) med axel längs `normal`.
 */
export function makeDisk(center, normal, radius, thickness, color) {
  const geom = new THREE.CylinderGeometry(radius, radius, thickness, 32);
  const mat = new THREE.MeshStandardMaterial({
    color, roughness: 0.5, metalness: 0.6
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.set(center[0], center[1], center[2]);
  mesh.castShadow = true;

  const up = new THREE.Vector3(0, 1, 0);
  const n = new THREE.Vector3(normal[0], normal[1], normal[2]).normalize();
  const q = new THREE.Quaternion().setFromUnitVectors(up, n);
  mesh.setRotationFromQuaternion(q);
  return mesh;
}
