// js/rider.js
// =============================================================================
// Föraren: skapar och placerar en Mannequin på maskinen.
//
// Beräknar:
//   - autoSaddleHeight(height)        → ideal sadelhöjd för given förarlängd
//   - riderXForLeg(height, sittH, ...) → bakersta x där benen når 95% utsträckta
//   - pedalPos(theta, side)            → fotens IK-mål (på pedalplattan)
//   - handlebarPos(side)               → handens IK-mål
//
// Alla antropometri-parametrar (benlängd, fothöjd osv) kommer från G.ergonomy
// så ingen magisk siffra ligger i den här filen.
// =============================================================================
import { Mannequin } from './mannequin.js';

/**
 * Skapa Rider-controller. Returnerar ett objekt med metoder för att
 * skapa/byta/uppdatera föraren.
 *
 * @param scene        THREE.Scene
 * @param G            geometri-data
 * @param getSaddleTop ()=>function(x)=>y  — sadelns topp-funktion (uppdateras
 *                     när sadelhöjden ändras). En getter eftersom sadelns
 *                     topAt-funktion byts ut när sadelhöjden ändras.
 */
export function createRiderController(scene, G, getSaddleTop, handlebar) {
  const E = G.ergonomy;
  let current = null;          // { man, updateRiderPose, riderX, saddleTopAtRider, pelvisHalf }
  let currentTheta = 0;        // senast använt theta (för att kunna re-posa)
  let currentVisible = true;

  function pedalPos(theta_global, side, height) {
    const gearRatio = G.mechanics.gear_ratio;
    const pedal_phase = theta_global / gearRatio;
    const pedal_angle = -pedal_phase + Math.PI / 2 + (side > 0 ? Math.PI : 0);
    const r = G.pedal.crank_radius_cm;
    const cx = G.axles.pedal.center[0];
    const cy = G.axles.pedal.center[1];
    const pedalTopOffset = E.pedal_top_offset_cm;
    const footHalfHeight = height * E.foot_half_height_ratio;
    return [
      cx + r * Math.cos(pedal_angle),
      cy + r * Math.sin(pedal_angle) + pedalTopOffset + footHalfHeight,
      side * G.pedal.plate_z_cm,   // foten centrerad på pedalplattan
    ];
  }

  function handlebarPos(side) {
    // Använd handlebar.gripWorld om tillgängligt (följer styrets rotation),
    // annars statiskt fallback.
    if (handlebar && handlebar.gripWorld) {
      const grip = handlebar.gripWorld(side);
      return [grip[0], grip[1] + E.hand_above_handlebar_cm, grip[2]];
    }
    return [
      G.handlebar.center[0],
      G.handlebar.center[1] + E.hand_above_handlebar_cm,
      side * G.handlebar.half_width,
    ];
  }

  function autoSaddleHeight(riderHeight) {
    const legLength = riderHeight * E.leg_length_ratio;
    const pedalLowY = G.axles.pedal.center[1] - G.pedal.crank_radius_cm;
    const footHalfHeight = riderHeight * E.foot_half_height_ratio;
    const footAnkleY = pedalLowY + E.pedal_top_offset_cm + footHalfHeight;
    const target = legLength * E.leg_stretch_target;
    const ideal = footAnkleY + target - G.saddle.back_offset_cm;
    const [lo, hi] = G.saddle.height_range_cm;
    return Math.max(lo, Math.min(hi, ideal));
  }

  /**
   * Hitta bakersta x där föraren kan sitta utan att översträcka benet.
   * Sadelns topAt-funktion ger höften-y vid given x; vi söker linjärt
   * från xMin framåt tills avståndet höft→fot ≤ targetDist.
   */
  function riderXForLeg(riderHeight, sittHeight, saddleTopAt) {
    const legLength = riderHeight * E.leg_length_ratio;
    const pedalX = G.axles.pedal.center[0];
    const pedalLowY = G.axles.pedal.center[1] - G.pedal.crank_radius_cm;
    const footHalfHeight = riderHeight * E.foot_half_height_ratio;
    const footAnkleY = pedalLowY + E.pedal_top_offset_cm + footHalfHeight;
    const targetDist = legLength * E.leg_stretch_target;

    function distAt(x) {
      const hipJointY = saddleTopAt(x);
      const dx = x - pedalX;
      const dy = hipJointY - footAnkleY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    const xMin = E.rider_x_min_cm, xMax = E.rider_x_max_cm;
    if (distAt(xMin) <= targetDist) return xMin;

    const steps = 200;
    let prevX = xMin, prevDist = distAt(xMin);
    for (let i = 1; i <= steps; i++) {
      const x = xMin + (xMax - xMin) * i / steps;
      const d = distAt(x);
      if (d <= targetDist) {
        const t = (prevDist - targetDist) / (prevDist - d);
        return prevX + t * (x - prevX);
      }
      prevX = x;
      prevDist = d;
    }
    return G.saddle.sit_x_cm;  // fallback: föraren för kort, sätt i sittpunkten
  }

  /**
   * Skapa eller byt ut den nuvarande föraren.
   */
  function createRider(gender, height, sittHeight) {
    if (current) {
      scene.remove(current.man.root);
    }
    try {
      const man = new Mannequin(height, gender);
      const saddleTopAt = getSaddleTop();
      const riderX = riderXForLeg(height, sittHeight, saddleTopAt);
      const saddleTopAtRider = saddleTopAt(riderX);
      const pelvisHalf = height * 0.025;

      man.root.position.set(riderX, saddleTopAtRider + pelvisHalf, 0);
      man.root.rotation.y = -Math.PI / 2;

      function updateRiderPose(theta_global) {
        currentTheta = theta_global;
        // Torsovridning följer styret. Hämta aktuell styrvinkel från
        // handlebar (om tillgängligt) och passera vidare. Mannequinen
        // applicerar fördelningen mellan abdomen, chest och head internt.
        const steerRad = (handlebar && handlebar.getSteerAngle)
          ? handlebar.getSteerAngle()
          : 0;
        man.poseRidingMachine({
          pedalLeft: pedalPos(theta_global, -1, height),
          pedalRight: pedalPos(theta_global, +1, height),
          handlebarLeft: handlebarPos(-1),
          handlebarRight: handlebarPos(+1),
          hipWorld: [riderX, saddleTopAtRider + pelvisHalf, 0],
          torsoLean: E.torso_lean_deg,
          torsoYaw: steerRad,
        });
      }

      updateRiderPose(currentTheta);
      scene.add(man.root);
      man.root.visible = currentVisible;

      current = { man, updateRiderPose, riderX, saddleTopAtRider, pelvisHalf };
    } catch (e) {
      console.error('Mannequin fel:', e);
      console.error('Stack:', e.stack);
    }
  }

  function setVisible(visible) {
    currentVisible = visible;
    if (current) current.man.root.visible = visible;
  }

  function updatePose(theta_global) {
    if (current) current.updateRiderPose(theta_global);
  }

  return {
    autoSaddleHeight,
    createRider,
    setVisible,
    updatePose,
    get current() { return current; },
  };
}
