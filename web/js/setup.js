// js/setup.js
// =============================================================================
// Scen-uppsättning: scen, kamera, renderer, ljus, mark, OrbitControls.
// Inga geometri-beroenden — bara Three.js + DOM.
// =============================================================================
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const BG_COLOR = 0xddddd0;

export function createScene() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(BG_COLOR);
  scene.fog = new THREE.Fog(BG_COLOR, 200, 600);

  // Kameran rymmer både maskin (0-130 cm) och förare (upp till ~190 cm).
  // Centrum y=100 ligger mitt i ekipaget.
  const camera = new THREE.PerspectiveCamera(
    40, window.innerWidth / window.innerHeight, 1, 1000
  );
  camera.position.set(230, 160, 320);
  camera.lookAt(20, 110, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(renderer.domElement);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(20, 110, 0);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  addLights(scene);
  const gridHelper = addGround(scene);

  return { scene, camera, renderer, controls, gridHelper };
}

function addLights(scene) {
  const ambient = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambient);

  const sun = new THREE.DirectionalLight(0xffffff, 0.9);
  sun.position.set(80, 200, 100);
  sun.castShadow = true;
  sun.shadow.mapSize.width = 2048;
  sun.shadow.mapSize.height = 2048;
  sun.shadow.camera.left = -150;
  sun.shadow.camera.right = 150;
  sun.shadow.camera.top = 150;
  sun.shadow.camera.bottom = -50;
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 500;
  scene.add(sun);

  const fill = new THREE.DirectionalLight(0xaaccff, 0.3);
  fill.position.set(-50, 50, -50);
  scene.add(fill);
}

function addGround(scene) {
  const groundGeom = new THREE.PlaneGeometry(400, 400);
  const groundMat = new THREE.MeshStandardMaterial({
    color: 0xcccccc, roughness: 0.9, metalness: 0.0
  });
  const ground = new THREE.Mesh(groundGeom, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = 0;
  ground.receiveShadow = true;
  scene.add(ground);

  // GridHelper med 40 divisions över 400 cm = 10 cm rutor.
  // Returneras så animationen kan skifta den för framdriftsillusion.
  const gridHelper = new THREE.GridHelper(400, 40, 0xaaaaaa, 0xbbbbbb);
  gridHelper.material.opacity = 0.5;
  gridHelper.material.transparent = true;
  scene.add(gridHelper);
  return gridHelper;
}
