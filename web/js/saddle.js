// js/saddle.js
// =============================================================================
// Sadelns 3D-form. Tunnelformad mesh med tapering och konkavitet vid
// sittpunkten. Bakdelen är förhöjd för att gå fri över bakvevpartiet.
//
// Sadelns form (relativ till sittHeight) styrs av parametrar i G.saddle:
//   sit_x_cm, back_offset_cm, dip_sigma_cm, front_rise_slope
// Allt detta ligger i Python-export och drivs av JSON — inga magiska tal här.
//
// Exporterar:
//   makeSaddleTopFn(G, sittHeight) → x → y    [ren funktion, ingen mesh]
//   buildSaddle(G, sittHeight)     → THREE.Mesh
//
// `makeSaddleTopFn` används av frame.js (sadelstolpe) och rider.js
// (förarens x-placering) utan att behöva bygga meshen.
// =============================================================================
import * as THREE from 'three';

const SADDLE_COLOR = 0x6D4C41;

/**
 * Returnerar en ren funktion x → ovansidans y vid given sittpunkts-höjd.
 * Sadelns FORM är fix; bara hela formen flyttas upp/ned med sittHeight.
 */
export function makeSaddleTopFn(G, sittHeight) {
  const s = G.saddle;
  const sitX = s.sit_x_cm;
  const bakOffset = s.back_offset_cm;
  const frontSlope = s.front_rise_slope;

  return function saddleTopAtX(x) {
    let relY;
    if (x >= sitX) {
      // Framför sittpunkten: linjär uppåtvinkling
      relY = (x - sitX) * frontSlope;
    } else if (x >= 0) {
      // Mellan x=0 och sittpunkten: kosinus-mjuk båge
      const t = x / sitX;
      const smoothT = (1 - Math.cos(t * Math.PI)) / 2;
      relY = bakOffset * (1 - smoothT);
    } else {
      // Bakom x=0: platt på bakhöjden
      relY = bakOffset;
    }
    return sittHeight + relY;
  };
}

/**
 * Bygg sadel-meshen för given sittpunkts-höjd.
 * Returnerar { mesh, topAt } där topAt(x) ger ovansidans y vid x.
 */
export function buildSaddle(G, sittHeight) {
  const s = G.saddle;
  const topAt = makeSaddleTopFn(G, sittHeight);
  const len_x = s.x_front - s.x_rear;
  const dipSigma = s.dip_sigma_cm;
  const sitX = s.sit_x_cm;

  function widthAt(u) {
    return s.width_rear + u * (s.width_front - s.width_rear);
  }

  const nu = 50;
  const nv = 24;
  const vertices = [];
  const indices = [];

  for (let i = 0; i <= nu; i++) {
    const u = i / nu;
    const x = s.x_rear + u * len_x;
    const halfW = widthAt(u) / 2;

    const top = topAt(x);
    const bottom = top - s.thickness;
    const centerY = (top + bottom) / 2;
    const halfH = (top - bottom) / 2;

    // Konkav fördjupning vid sittpunkten (gaussian).
    const dip = s.concavity *
      Math.exp(-((x - sitX) * (x - sitX)) / (2 * dipSigma * dipSigma));

    for (let j = 0; j < nv; j++) {
      const v = j / nv;
      const theta = v * 2 * Math.PI;
      const cosT = Math.cos(theta);
      const sinT = Math.sin(theta);

      let y;
      if (sinT > 0) {
        y = centerY + halfH * sinT - dip * sinT;
      } else {
        y = centerY + halfH * sinT * 0.85;
      }
      const z = halfW * cosT;
      vertices.push(x, y, z);
    }
  }

  // Triangulera mantel
  for (let i = 0; i < nu; i++) {
    for (let j = 0; j < nv; j++) {
      const jNext = (j + 1) % nv;
      const a = i * nv + j;
      const b = (i + 1) * nv + j;
      const c = (i + 1) * nv + jNext;
      const d = i * nv + jNext;
      indices.push(a, b, d);
      indices.push(b, c, d);
    }
  }

  // Stäng bakändan
  {
    const centerIdx = vertices.length / 3;
    const x = s.x_rear;
    const top = topAt(x);
    const bottom = top - s.thickness;
    const cy = (top + bottom) / 2;
    vertices.push(x, cy, 0);
    for (let j = 0; j < nv; j++) {
      const jNext = (j + 1) % nv;
      indices.push(centerIdx, j, jNext);
    }
  }

  // Stäng framändan
  {
    const centerIdx = vertices.length / 3;
    const x = s.x_front;
    const top = topAt(x);
    const bottom = top - s.thickness;
    const cy = (top + bottom) / 2;
    vertices.push(x, cy, 0);
    const ringStart = nu * nv;
    for (let j = 0; j < nv; j++) {
      const jNext = (j + 1) % nv;
      indices.push(centerIdx, ringStart + jNext, ringStart + j);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geom.setIndex(indices);
  geom.computeVertexNormals();

  const mat = new THREE.MeshStandardMaterial({
    color: SADDLE_COLOR,
    roughness: 0.55,
    metalness: 0.1,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;

  return { mesh, topAt };
}
