// js/mannequin.js
// =============================================================================
// Mannequin — artikulerad förar-figur för springcykeln.
//
// En klassisk konstnärs-mannequin med:
//   - Tvådelad torso (bröstkorg + mage med midje-stuk)
//   - Pelvis som separat segment
//   - Ellipsoid-baserade lemmar med markerade leder
//   - Hierarkisk struktur (varje led som THREE.Group)
//   - IK-metoder för att placera fötter och händer på specifika punkter
//   - Pose-funktioner: standing(), sitting(), ridingMachine()
//
// Konvention:
//   - Höjder i cm
//   - Figuren är default 194 cm hög
//   - Lokala koordinater: y uppåt, figuren tittar längs +z
//     (vänds till körriktningen via root.rotation.y av rider.js)
//
// Användning:
//   import { Mannequin } from './mannequin.js';
//   const m = new Mannequin(194, 'male');
//   scene.add(m.root);
//   m.root.position.set(0, 113, 0);
//   m.root.rotation.y = -Math.PI / 2;  // titta längs +x
//   m.poseRidingMachine({...});
// =============================================================================
import * as THREE from 'three';

const SKIN = 0xFFCCBC;
const TORSO_COLOR = 0x6D4C41;
const LIMB_COLOR = 0x8D6E63;
const JOINT_COLOR = 0x5D4037;
const SHOE_COLOR = 0x3E2723;

function mat(color, roughness = 0.5) {
  return new THREE.MeshStandardMaterial({
    color, roughness, metalness: 0.05
  });
}

function ellipsoid(rx, ry, rz, color, segments = 20) {
  const geom = new THREE.SphereGeometry(1, segments, Math.floor(segments * 0.7));
  const mesh = new THREE.Mesh(geom, mat(color));
  mesh.scale.set(rx, ry, rz);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  return mesh;
}

function sphere(radius, color) {
  const geom = new THREE.SphereGeometry(radius, 20, 14);
  const mesh = new THREE.Mesh(geom, mat(color));
  mesh.castShadow = true;
  return mesh;
}

export class Mannequin {
  constructor(height = 194, gender = 'male') {
    this.height = height;
    this.gender = gender;
    
    const h = height;
    const isFemale = gender === 'female';
    
    // Proportioner baserade på antropometrisk data (vid samma totalhöjd):
    //   Manlig SHR (axel/höft) ≈ 1.18 — bredare axlar än höft
    //   Kvinnlig SHR ≈ 1.03 — nästan lika brett, men med markant smalare midja
    //   Höfter är ungefär lika breda mellan könen vid samma höjd
    //   Skillnaden ligger främst i bröstkorgens bredd och midjans smalhet
    this.dims = {
      headHeight: h * 0.13,
      neckLength: h * 0.04,
      chestHeight: h * 0.17,
      abdomenHeight: h * 0.13,
      pelvisHeight: h * 0.05,
      thighLength: h * 0.245,
      shinLength: h * 0.22,
      footHeight: h * 0.04,
      upperArmLength: h * 0.165,
      forearmLength: h * 0.135,
      handLength: h * 0.06,
      
      // Bredder — anatomiska könsskillnader
      shoulderWidth: h * (isFemale ? 0.205 : 0.235),   // 40 vs 46 cm
      chestWidth: h * (isFemale ? 0.155 : 0.180),      // 30 vs 35 cm
      chestDepth: h * (isFemale ? 0.105 : 0.115),      // 20 vs 22 cm
      waistWidth: h * (isFemale ? 0.095 : 0.125),      // 18 vs 24 cm (timglas)
      waistDepth: h * (isFemale ? 0.080 : 0.100),
      hipWidth: h * (isFemale ? 0.190 : 0.180),        // 37 vs 35 cm (snarlikt)
      hipDepth: h * (isFemale ? 0.130 : 0.115),
      headWidth: h * 0.075,
      headDepth: h * 0.085,
      neckWidth: h * (isFemale ? 0.035 : 0.040),
      upperArmRadius: h * (isFemale ? 0.022 : 0.025),
      forearmRadius: h * (isFemale ? 0.020 : 0.022),
      thighRadius: h * (isFemale ? 0.041 : 0.040),
      shinRadius: h * (isFemale ? 0.028 : 0.030),
      footWidth: h * 0.04,
      footLength: h * 0.09,
      
      // Könsspecifika tillägg
      breastSize: isFemale ? h * 0.045 : 0,           // ~9 cm bröst-radie
      gluteusBulge: isFemale ? h * 0.025 : h * 0.012, // mer rundad rumpa för kvinna
    };
    
    this.parts = {};
    this._build();
  }
  
  _build() {
    const D = this.dims;
    
    // === ROOT (figurens "förflyttningspunkt") ===
    // Root är vid pelvis-centrum (förarens höft).
    this.root = new THREE.Group();
    this.root.name = 'mannequin_root';
    
    // === PELVIS ===
    const pelvis = ellipsoid(
      D.hipWidth / 2, D.pelvisHeight / 2, D.hipDepth / 2,
      TORSO_COLOR
    );
    this.root.add(pelvis);
    this.parts.pelvis = pelvis;
    
    // Glutealregion — rundad utbuktning bakåt-nedåt
    if (D.gluteusBulge > 0) {
      const gluteus = ellipsoid(
        D.hipWidth / 2 * 0.85,
        D.gluteusBulge,
        D.gluteusBulge * 1.3,
        TORSO_COLOR
      );
      gluteus.position.set(0, -D.pelvisHeight / 3, +D.hipDepth / 2 * 0.5);
      this.root.add(gluteus);
    }
    
    // === ABDOMEN (nedre bål, magpartiet) ===
    // Bygger uppåt från pelvis. Group vid övre kant av pelvis.
    const abdomenGroup = new THREE.Group();
    abdomenGroup.name = 'abdomen';
    abdomenGroup.position.y = D.pelvisHeight / 2;
    this.root.add(abdomenGroup);
    this.parts.abdomen = abdomenGroup;
    
    // Mage som taperar uppåt mot midjan
    const abdomen = ellipsoid(
      D.waistWidth / 2 * 1.1,    // lite bredare nedtill
      D.abdomenHeight / 2,
      D.waistDepth / 2 * 1.1,
      TORSO_COLOR
    );
    abdomen.position.y = D.abdomenHeight / 2;
    abdomenGroup.add(abdomen);
    
    // Midje-led: liten sfär som markerar midjan
    const waist = sphere(D.waistWidth / 2 * 0.7, JOINT_COLOR);
    waist.position.y = D.abdomenHeight;
    waist.scale.set(1, 0.4, 0.7);  // platt skiva
    abdomenGroup.add(waist);
    
    // === CHEST (övre bål, bröstkorg) ===
    // Group vid midjan, kan rotera relativt magpartiet
    const chestGroup = new THREE.Group();
    chestGroup.name = 'chest';
    chestGroup.position.y = D.abdomenHeight;
    abdomenGroup.add(chestGroup);
    this.parts.chest = chestGroup;
    
    // Bröstkorg som taperar uppåt mot axlarna
    const chest = ellipsoid(
      D.chestWidth / 2,
      D.chestHeight / 2,
      D.chestDepth / 2,
      TORSO_COLOR
    );
    chest.position.y = D.chestHeight / 2;
    chestGroup.add(chest);
    
    // Axelparti — bredare ellipsoid ovanpå bröstet
    const shoulderRidge = ellipsoid(
      D.shoulderWidth / 2,
      D.chestHeight * 0.15,
      D.chestDepth / 2 * 0.9,
      TORSO_COLOR
    );
    shoulderRidge.position.y = D.chestHeight * 0.9;
    chestGroup.add(shoulderRidge);
    
    // Bröst (för kvinnlig figur)
    if (D.breastSize > 0) {
      const breastR = D.breastSize * 0.75;  // 75% av tidigare storlek
      const breastY = D.chestHeight * 0.55;
      const breastZ = -D.chestDepth / 2 * 0.85;  // NEGATIV z = framåt i denna 
                                                  // riktning eftersom föraren är 
                                                  // roterad så att lokal -z = framåt
      const breastX = D.chestWidth / 4;
      
      const breastLeft = ellipsoid(breastR * 0.9, breastR, breastR * 0.95, TORSO_COLOR);
      breastLeft.position.set(-breastX, breastY, breastZ);
      chestGroup.add(breastLeft);
      
      const breastRight = ellipsoid(breastR * 0.9, breastR, breastR * 0.95, TORSO_COLOR);
      breastRight.position.set(+breastX, breastY, breastZ);
      chestGroup.add(breastRight);
    }
    
    // === NACKE + HUVUD ===
    const neckGroup = new THREE.Group();
    neckGroup.name = 'neck';
    neckGroup.position.y = D.chestHeight;
    chestGroup.add(neckGroup);
    this.parts.neck = neckGroup;
    
    const neck = ellipsoid(
      D.neckWidth / 2, D.neckLength / 2, D.neckWidth / 2,
      SKIN
    );
    neck.position.y = D.neckLength / 2;
    neckGroup.add(neck);
    
    const headGroup = new THREE.Group();
    headGroup.name = 'head';
    headGroup.position.y = D.neckLength;
    neckGroup.add(headGroup);
    this.parts.head = headGroup;
    
    // Huvud: ellipsoid, lite avlångt vertikalt
    const head = ellipsoid(
      D.headWidth / 2, D.headHeight / 2, D.headDepth / 2,
      SKIN
    );
    head.position.y = D.headHeight / 2;
    headGroup.add(head);
    
    // === ARMAR ===
    this._buildArm(+1, chestGroup);
    this._buildArm(-1, chestGroup);
    
    // === BEN ===
    this._buildLeg(+1);
    this._buildLeg(-1);
  }
  
  _buildArm(side, parent) {
    const D = this.dims;
    const sideName = side > 0 ? 'r' : 'l';
    
    const armGroup = new THREE.Group();
    armGroup.name = sideName + '_arm';
    armGroup.position.set(
      side * D.shoulderWidth / 2,
      D.chestHeight * 0.85,
      0
    );
    parent.add(armGroup);
    this.parts[sideName + '_arm'] = armGroup;
    
    // Axel-led
    const shoulder = sphere(D.upperArmRadius * 1.1, JOINT_COLOR);
    armGroup.add(shoulder);
    
    // Överarm — ellipsoid hängande nedåt
    const upperArm = ellipsoid(
      D.upperArmRadius, D.upperArmLength / 2, D.upperArmRadius,
      LIMB_COLOR
    );
    upperArm.position.y = -D.upperArmLength / 2;
    armGroup.add(upperArm);
    
    // Armbåge
    const elbowGroup = new THREE.Group();
    elbowGroup.name = sideName + '_elbow';
    elbowGroup.position.y = -D.upperArmLength;
    armGroup.add(elbowGroup);
    this.parts[sideName + '_elbow'] = elbowGroup;
    
    const elbow = sphere(D.forearmRadius * 1.1, JOINT_COLOR);
    elbowGroup.add(elbow);
    
    // Underarm
    const forearm = ellipsoid(
      D.forearmRadius, D.forearmLength / 2, D.forearmRadius,
      LIMB_COLOR
    );
    forearm.position.y = -D.forearmLength / 2;
    elbowGroup.add(forearm);
    
    // Handled
    const wristGroup = new THREE.Group();
    wristGroup.name = sideName + '_wrist';
    wristGroup.position.y = -D.forearmLength;
    elbowGroup.add(wristGroup);
    this.parts[sideName + '_wrist'] = wristGroup;
    
    const wrist = sphere(D.forearmRadius * 0.9, JOINT_COLOR);
    wristGroup.add(wrist);
    
    // Hand
    const hand = ellipsoid(
      D.forearmRadius * 0.9, D.handLength / 2, D.forearmRadius * 0.5,
      SKIN
    );
    hand.position.y = -D.handLength / 2;
    wristGroup.add(hand);
  }
  
  _buildLeg(side) {
    const D = this.dims;
    const sideName = side > 0 ? 'r' : 'l';
    
    const legGroup = new THREE.Group();
    legGroup.name = sideName + '_leg';
    legGroup.position.set(
      side * D.hipWidth / 4,
      -D.pelvisHeight / 2,
      0
    );
    this.root.add(legGroup);
    this.parts[sideName + '_leg'] = legGroup;
    
    // Höft-led
    const hipJoint = sphere(D.thighRadius * 1.2, JOINT_COLOR);
    legGroup.add(hipJoint);
    
    // Lår
    const thigh = ellipsoid(
      D.thighRadius, D.thighLength / 2, D.thighRadius,
      LIMB_COLOR
    );
    thigh.position.y = -D.thighLength / 2;
    legGroup.add(thigh);
    
    // Knä
    const kneeGroup = new THREE.Group();
    kneeGroup.name = sideName + '_knee';
    kneeGroup.position.y = -D.thighLength;
    legGroup.add(kneeGroup);
    this.parts[sideName + '_knee'] = kneeGroup;
    
    const knee = sphere(D.shinRadius * 1.2, JOINT_COLOR);
    kneeGroup.add(knee);
    
    // Underben
    const shin = ellipsoid(
      D.shinRadius, D.shinLength / 2, D.shinRadius,
      LIMB_COLOR
    );
    shin.position.y = -D.shinLength / 2;
    kneeGroup.add(shin);
    
    // Fotled
    const ankleGroup = new THREE.Group();
    ankleGroup.name = sideName + '_ankle';
    ankleGroup.position.y = -D.shinLength;
    kneeGroup.add(ankleGroup);
    this.parts[sideName + '_ankle'] = ankleGroup;
    
    const ankle = sphere(D.shinRadius * 0.9, JOINT_COLOR);
    ankleGroup.add(ankle);
    
    // Fot (skor) — platt ellipsoid framåtsträckt
    const foot = ellipsoid(
      D.footWidth / 2, D.footHeight / 2, D.footLength / 2,
      SHOE_COLOR
    );
    foot.position.set(0, -D.footHeight / 2, -D.footLength / 3);
    ankleGroup.add(foot);
  }
  
  // ============================================================
  // POSE-METODER
  // ============================================================
  
  /**
   * Nollställ alla rotationer.
   */
  resetPose() {
    const partsToReset = [
      'abdomen', 'chest', 'neck', 'head',
      'r_arm', 'l_arm', 'r_elbow', 'l_elbow', 'r_wrist', 'l_wrist',
      'r_leg', 'l_leg', 'r_knee', 'l_knee', 'r_ankle', 'l_ankle',
    ];
    for (const name of partsToReset) {
      if (this.parts[name]) {
        this.parts[name].rotation.set(0, 0, 0);
      }
    }
  }
  
  /**
   * Standpose (default — figuren står upp med armarna lite ut).
   */
  poseStanding() {
    this.resetPose();
    this.parts.r_arm.rotation.z = THREE.MathUtils.degToRad(8);
    this.parts.l_arm.rotation.z = THREE.MathUtils.degToRad(-8);
  }
  
  /**
   * Sittpose (sittande på sadel med ben pekande framåt och uppåt).
   */
  poseSitting() {
    this.resetPose();
    this.parts.r_leg.rotation.x = THREE.MathUtils.degToRad(85);
    this.parts.l_leg.rotation.x = THREE.MathUtils.degToRad(85);
    this.parts.r_knee.rotation.x = THREE.MathUtils.degToRad(-85);
    this.parts.l_knee.rotation.x = THREE.MathUtils.degToRad(-85);
  }
  
  /**
   * Pose att rida maskinen, med IK för fötter på pedaler och händer på styre.
   * 
   * Argument:
   *   config = {
   *     pedalLeft: [x, y, z],      // vänster pedalcentrum i world
   *     pedalRight: [x, y, z],     // höger pedalcentrum
   *     handlebarLeft: [x, y, z],  // vänster handtag
   *     handlebarRight: [x, y, z], // höger handtag
   *     hipWorld: [x, y, z],       // där höften ska sitta
   *     torsoLean: 15,             // bålens framåtlutning i grader
   *   }
   * 
   * Föraren-figurens root.position och root.rotation.y antas vara satta 
   * redan så att lokal +z = framåt i världen.
   */
  /**
   * Färgmarkera en lem som "out of reach" (röd) eller "normal".
   * Sub-tree från legGroup eller armGroup färgas om.
   */
  _markLimbReach(group, exceeded) {
    const color = exceeded ? 0xC62828 : 0x8D6E63;  // röd eller normal LIMB_COLOR
    group.traverse((child) => {
      if (child.isMesh && child.material && child.userData.reachIndicator !== false) {
        // Sätt om materialet - använd unika material per lem för att inte 
        // påverka andra mesh som delar material
        if (!child.userData.originalColor) {
          child.userData.originalColor = child.material.color.getHex();
        }
        // Bara färgom de bruna LIMB-färgade delarna, inte hudfärgade händer/fötter
        const orig = child.userData.originalColor;
        if (orig === 0x8D6E63 || orig === 0xC62828) {
          child.material = child.material.clone();
          child.material.color.setHex(color);
        }
      }
    });
  }
  
  poseRidingMachine(config) {
    this.resetPose();
    const D = this.dims;
    
    // === BEN-IK (oberoende av bål-lutning eftersom benen utgår från höften) ===
    const rLegExceeded = this._ikLeg('r', config.pedalRight, config.hipWorld);
    const lLegExceeded = this._ikLeg('l', config.pedalLeft, config.hipWorld);
    this._markLimbReach(this.parts.r_leg, rLegExceeded);
    this._markLimbReach(this.parts.l_leg, lLegExceeded);
    
    // === BÅL-LUTNING med automatisk justering ===
    // Börja med given lutning, öka tills armarna når styret (eller max 70°)
    const minLean = config.torsoLean || 15;
    const maxLean = 70;
    let leanDeg = minLean;
    let rArmExceeded = true, lArmExceeded = true;
    
    while (leanDeg <= maxLean) {
      this._applyTorsoLean(leanDeg);
      // Vi måste uppdatera världs-matriserna innan IK eftersom 
      // axelpositionen ändras med bål-lutningen
      this.root.updateMatrixWorld(true);
      
      rArmExceeded = this._ikArm('r', config.handlebarRight);
      lArmExceeded = this._ikArm('l', config.handlebarLeft);
      
      if (!rArmExceeded && !lArmExceeded) break;
      leanDeg += 2;
    }
    
    this._markLimbReach(this.parts.r_arm, rArmExceeded);
    this._markLimbReach(this.parts.l_arm, lArmExceeded);
  }
  
  _applyTorsoLean(leanDeg) {
    const lean = THREE.MathUtils.degToRad(leanDeg);
    this.parts.abdomen.rotation.x = -lean * 0.3;
    this.parts.chest.rotation.x = -lean * 0.7;
    this.parts.head.rotation.x = lean * 0.5;
  }
  
  /**
   * IK för ett ben. Beräkna höft- och knävinklar så att foten hamnar 
   * vid målpunkten.
   * 
   * sideName: 'l' eller 'r'
   * footTarget: [x, y, z] i world coords
   * hipWorld: höftens världs-position (där root är)
   */
  _ikLeg(sideName, footTarget, hipWorld) {
    const D = this.dims;
    const legGroup = this.parts[sideName + '_leg'];
    const kneeGroup = this.parts[sideName + '_knee'];
    
    // Hitta höftens position i world via legGroup
    legGroup.updateMatrixWorld(true);
    const hipPos = new THREE.Vector3();
    legGroup.getWorldPosition(hipPos);
    
    // Vektorn från höften till foten i world
    const target = new THREE.Vector3(...footTarget);
    const delta = new THREE.Vector3().subVectors(target, hipPos);
    
    // Transformera delta till förarens lokala koord (eftersom benets rotationer 
    // är i lokal frame). Vi tar bort root.rotation.y från delta.
    const rootRot = this.root.rotation.y;
    const cosR = Math.cos(-rootRot), sinR = Math.sin(-rootRot);
    const dx_local = cosR * delta.x - sinR * delta.z;
    const dy_local = delta.y;
    const dz_local = sinR * delta.x + cosR * delta.z;
    
    // Nu har vi delta i förarens lokala frame.
    // Bestäm vinklar: 
    //   - "raise" = rotation.x på legGroup: positiv = lyft framåt (+z)
    //   - "knee bend" = rotation.x på kneeGroup: positiv eller negativ?
    // Då lokal frame har +y nedåt från legGroup (benet hänger), 
    // och knee är vid (0, -thighLen, 0) lokalt, måste vi tänka på det.
    
    // Använd 2D-IK i x-y planet av lokala frame (där x här = lateral, 
    // ignoreras; vi tar y och z för planet "framåt-uppåt").
    // I lokal koord för benet (efter root.rotation.y kompenserats):
    //   x_local = lateral
    //   y_local = upp/ned
    //   z_local = framåt/bakåt
    // Benet vid raise=0 pekar rakt ner (negativ y från legGroup).
    
    // Vi gör IK i det vertikala plan som innehåller höft → fot.
    // I detta plan är "framåt-avstånd" = dz_local och "ner-avstånd" = -dy_local
    const horiz = dz_local;          // framåt (positiv) eller bakåt
    const vert = -dy_local;          // nedåt (positiv) eller uppåt
    const dist = Math.sqrt(horiz * horiz + vert * vert);
    
    const L1 = D.thighLength;
    const L2 = D.shinLength;
    const maxReach = L1 + L2;
    
    let totalReach = Math.min(dist, maxReach * 0.99);
    
    // Vinkel höft-fot från lodlinjen (positiv = framåt)
    const angleHipFoot = Math.atan2(horiz, vert);
    
    // Vinkel knäets böjning (lagen om cosinus)
    // cosKnee = (L1² + L2² - dist²) / (2 L1 L2)
    const cosKnee = (L1 * L1 + L2 * L2 - totalReach * totalReach) / (2 * L1 * L2);
    const kneeAngle = Math.PI - Math.acos(Math.max(-1, Math.min(1, cosKnee)));
    
    // Vinkel höft från sin "rätt-ner"-riktning
    // Vinkeln mellan höft-fot-linjen och låret:
    const cosHip = (L1 * L1 + totalReach * totalReach - L2 * L2) / 
                   (2 * L1 * totalReach);
    const hipFromLine = Math.acos(Math.max(-1, Math.min(1, cosHip)));
    
    // Höftens rotation: angleHipFoot är hela höft-fot-vinkeln från ner,
    // höften ska vrida sig så att låret ligger längs höft-fot men 
    // sedan minus hipFromLine för att knäet ska peka rätt håll
    // (knäna pekar framåt i sittande, så låret behöver luta MER framåt 
    // än rät linje till foten)
    const hipAngle = angleHipFoot + hipFromLine;
    
    // Applicera
    legGroup.rotation.x = hipAngle;
    legGroup.rotation.y = 0;
    legGroup.rotation.z = 0;
    
    kneeGroup.rotation.x = -kneeAngle;
    kneeGroup.rotation.y = 0;
    kneeGroup.rotation.z = 0;
    
    // Returnera om räckvidden överskreds (verkligen, inte bara över säkerhetsmarginal)
    return dist > (L1 + L2);
  }
  
  /**
   * IK för en arm. Liknande som benet men för axel-armbåge-hand.
   * Armbågen pekar bakåt (när man håller styret är armbågarna ute-bakåt).
   */
  _ikArm(sideName, handTarget) {
    const D = this.dims;
    const armGroup = this.parts[sideName + '_arm'];
    const elbowGroup = this.parts[sideName + '_elbow'];
    
    // Använd lookAt-baserad IK i världskoordinater.
    // Steg 1: peka armgruppen så att dess "nedåt" (y=-1) riktning pekar 
    // mot målet. Detta ger en helt utsträckt arm mot handen.
    
    armGroup.updateMatrixWorld(true);
    const shoulderPos = new THREE.Vector3();
    armGroup.getWorldPosition(shoulderPos);
    
    const target = new THREE.Vector3(...handTarget);
    const toTarget = new THREE.Vector3().subVectors(target, shoulderPos);
    const distance = toTarget.length();
    
    const L1 = D.upperArmLength;
    // L2_eff inkluderar halva handens längd, eftersom IK ska placera handens 
    // CENTRUM på målet, inte handleden
    const L2 = D.forearmLength + D.handLength / 2;
    const maxReach = (L1 + L2) * 0.99;
    // Markera bara som "exceeded" när det verkligen är out of reach (inte 
    // bara över IK:s säkerhetsmarginal)
    const armExceeded = distance > (L1 + L2);
    
    // Trick: vi använder en hjälp-objekt som är riktat mot målet, 
    // och avläser dess quaternion.
    // Armens default-riktning (overarm pekar nedåt) är (0, -1, 0) lokalt.
    
    // Vi vill att överarmen pekar längs en vektor mellan axel och en punkt 
    // som ger korrekt böjning av armbågen.
    //
    // Med lagen om cosinus:
    //   Om hela avståndet är dist, och vi vill att armbågen är på axel-mål-linjen
    //   förflyttad sidvägs (mot en "böj-riktning"), beräknar vi var armbågen 
    //   sitter och sedan riktar överarmen från axel till armbåge.
    
    const totalReach = Math.min(distance, maxReach);
    
    // Position längs axel-mål-linjen där armbågen "projicerar" 
    // (=lägsta avstånd till axeln för en given totalReach)
    const a_proj = (L1 * L1 - L2 * L2 + totalReach * totalReach) / (2 * totalReach);
    // Vinkelrät avstånd från denna linje till armbågen
    const h = Math.sqrt(Math.max(0, L1 * L1 - a_proj * a_proj));
    
    // Riktning från axel mot mål (enhetsvektor i världen)
    const dir = toTarget.clone().normalize();
    
    // För att hitta armbågens position, behöver vi en riktning vinkelrät mot 
    // dir. Eftersom armbågar naturligt pekar nedåt-utåt-bakåt, väljer vi 
    // "böj-riktningen" som projektionen av världs (0,-1,0) ortogonalt mot dir.
    const downHint = new THREE.Vector3(0, -1, 0);
    const perp = downHint.clone().sub(dir.clone().multiplyScalar(downHint.dot(dir)));
    if (perp.lengthSq() < 1e-6) {
      // dir är nästan parallellt med upp/ner — använd en annan hint
      perp.set(0, 0, -1);
    }
    perp.normalize();
    
    // Armbågens position i världen
    const elbowWorld = shoulderPos.clone()
      .add(dir.clone().multiplyScalar(a_proj))
      .add(perp.clone().multiplyScalar(h));
    
    // Steg 2: rikta armgruppen så att lokal (0,-1,0) pekar från axel mot armbåge.
    // Använd Three.js Quaternion.setFromUnitVectors
    
    // Parent's världs-rotation behövs för att gå tillbaka till lokala rotationer
    armGroup.parent.updateMatrixWorld(true);
    const parentInverseMatrix = new THREE.Matrix4().copy(armGroup.parent.matrixWorld).invert();
    
    // Lokala riktningen från axel till armbåge
    const elbowLocal = elbowWorld.clone().applyMatrix4(parentInverseMatrix);
    const shoulderLocal = shoulderPos.clone().applyMatrix4(parentInverseMatrix);
    const upperArmDirLocal = new THREE.Vector3().subVectors(elbowLocal, shoulderLocal).normalize();
    
    const defaultDown = new THREE.Vector3(0, -1, 0);
    const quat = new THREE.Quaternion().setFromUnitVectors(defaultDown, upperArmDirLocal);
    armGroup.quaternion.copy(quat);
    
    // Steg 3: rikta armbågen så att underarmen pekar mot målet.
    armGroup.updateMatrixWorld(true);
    elbowGroup.updateMatrixWorld(true);
    const elbowPosNow = new THREE.Vector3();
    elbowGroup.getWorldPosition(elbowPosNow);
    
    // Lokala riktningen från armbåge till hand i elbowGroup's lokala frame
    const elbowParentInverse = new THREE.Matrix4().copy(elbowGroup.parent.matrixWorld).invert();
    const targetInElbowFrame = target.clone().applyMatrix4(elbowParentInverse);
    const elbowInElbowFrame = elbowPosNow.clone().applyMatrix4(elbowParentInverse);
    const forearmDir = new THREE.Vector3().subVectors(targetInElbowFrame, elbowInElbowFrame).normalize();
    
    const elbowQuat = new THREE.Quaternion().setFromUnitVectors(defaultDown, forearmDir);
    elbowGroup.quaternion.copy(elbowQuat);
    
    return armExceeded;
  }
}

