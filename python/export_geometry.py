"""
Exportera maskingeometrin till JSON för Three.js-visualisering.

Innehåller ALLA numeriska dimensioner som JS-lagret behöver, så att inga
mått dupliceras mellan Python och JS. Visuell stil (färger, materialvärden)
ligger kvar i JS-modulerna — den här filen producerar bara DATA.

Sektioner i den exporterade JSON-filen:
  - frame: ramnoder + länkar (3D-koordinater)
  - axles: vevaxlarnas centra och drev-positioner
  - drivelines_z: z-konventioner för axel-stack (lagerhus, drev, vevarm, ytter)
  - pedal: pedalvevens dimensioner (vevarm, pedalplatta)
  - leg: Jansens konstanter + B_local
  - legs: instanser (4 ben) med A_world, yaw, fas, z
  - saddle: sadelns 3D-form (alla formparametrar för buildSaddle)
  - handlebar: styrets dimensioner
  - rider: antropometri-data för Mannequin
  - mechanics: härledd mekanik (steglängd, utväxling) för speed-beräkning
  - ergonomy: parametrar för auto-sadelhöjd och förarplacering
  - ground_y, wheelbase, track_width: scen-skala
"""

import sys
import os
# Lägg till scriptets egen katalog så machine.py, machine3d.py, jansen.py
# hittas oavsett varifrån scriptet körs.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import numpy as np
from machine import Machine
from machine3d import Driveline, Saddle, Rider3D
from jansen import analyze as jansen_analyze


def export_geometry():
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=50.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=50, handlebar_y=124,
        gait='trot', steer=0.0,
    )

    track_width = 30
    z_left = -track_width / 2
    z_right = +track_width / 2

    data = {}

    # ============================================================
    # Ramen — 3D-konstruktion med raka sidoramar vid z=±RAM_Z
    # ============================================================
    # Sidoramarna är raka, båda vid z=±10. Det är *mitt på* B-axeln som går
    # från B1 (vid z=±15, benets z1-plan) till B2 (vid z=±5, benets z2-plan).
    # Triangelstöd och teleskop ankrar mitt på B-axeln — eliminerar
    # vridmoment vid B-leden.
    #
    # Ramtopologi: centrala A_front och A_rear-noder (vid z=0) tar upp de
    # diagonala stagen från P respektive M på båda sidor — "Y-formad" struktur
    # sett från sidan. Tvärbalkarna A_front_left↔A_front_right och
    # A_rear_left↔A_rear_right passerar genom respektive central nod.
    #
    # Föraren har 20 cm benbredd mellan sidoramarna — gott om plats.
    RAM_Z = 10.0   # sidoramarnas z-position (cm)

    nodes2d = machine2d.frame.nodes
    nodes3d = {}

    # ── Sidorams-noder vid z=±RAM_Z (A_front, A_rear, P, M) ──
    sidoram_node_names = ['A_front', 'A_rear', 'P', 'M']
    for name in sidoram_node_names:
        p = nodes2d[name]
        nodes3d[f'{name}_left']  = [float(p[0]), float(p[1]), -RAM_Z]
        nodes3d[f'{name}_right'] = [float(p[0]), float(p[1]), +RAM_Z]

    # ── Centrala A-noder vid z=0 — bryts ut för att förenkla ramen ──
    # A_front och A_rear sitter där tvärbalkarna mellan vänster och höger
    # passerar mittlinjen. Diagonala stag från P/M på sidoramarna går till
    # respektive central A-nod istället för till A_front_left/right.
    nodes3d['A_front'] = [float(nodes2d['A_front'][0]),
                          float(nodes2d['A_front'][1]), 0.0]
    nodes3d['A_rear']  = [float(nodes2d['A_rear'][0]),
                          float(nodes2d['A_rear'][1]),  0.0]

    # ── Centrala noder: Q (sadelstolpens topp), N (styraxel), H (styre) ──
    for name in ['Q', 'N', 'H']:
        p = nodes2d[name]
        nodes3d[name] = [float(p[0]), float(p[1]), 0.0]

    links3d = []

    # ── Sidoramslänkar (per-sida) ──
    # Bevarade per-sida-stag: A_rear↔P (vertikalt), M↔A_front (snett framåt).
    per_side_link_pairs = [
        ('A_rear', 'P'),
        ('M', 'A_front'),
    ]
    for n1, n2 in per_side_link_pairs:
        links3d.append([f'{n1}_left',  f'{n2}_left'])
        links3d.append([f'{n1}_right', f'{n2}_right'])

    # ── Diagonala stag till central nod ──
    # P (på sidan) → A_front (central): båda sidor möts vid central nod.
    # M (på sidan) → A_rear (central): båda sidor möts.
    # Central balk A_rear ↔ A_front förbinder de två centrala noderna.
    links3d.append(['A_rear', 'A_front'])
    links3d.append(['A_rear', 'M_left'])
    links3d.append(['A_rear', 'M_right'])
    links3d.append(['P_left',  'A_front'])
    links3d.append(['P_right', 'A_front'])

    # ── Tvärbalkar mellan sidorna: en per sidorams-nod ──
    for name in sidoram_node_names:
        links3d.append([f'{name}_left', f'{name}_right'])

    # ── Centrala stöd: N (styraxel) ankras från båda A_front-noderna ──
    links3d.append(['A_front_left',  'N'])
    links3d.append(['A_front_right', 'N'])
    links3d.append(['N', 'H'])
    # Q stöttas dynamiskt av sadelstolpen (hanteras i frame.js)

    data['frame'] = {
        'nodes': nodes3d,
        'links': links3d,
        'tube_radius_cm': 1.2,
        'side_z_cm': RAM_Z,    # sidoramarnas z-position
    }

    # ============================================================
    # Vevaxlar
    # ============================================================
    data['axles'] = {
        'pedal': {
            'center': [float(machine2d.frame.P[0]), float(machine2d.frame.P[1])],
            'drev_left_z': -Driveline.DREV_Z,
            'drev_right_z': +Driveline.DREV_Z,
            'drev_r': Driveline.PEDAL_DREV_R,
        },
        'rear': {
            'center': [float(machine2d.frame.A_rear[0]), float(machine2d.frame.A_rear[1])],
            'drev_left_z': -Driveline.DREV_Z,
            'drev_right_z': None,
            'drev_r': Driveline.VEV_DREV_R,
        },
        'front': {
            'center': [float(machine2d.frame.A_front[0]), float(machine2d.frame.A_front[1])],
            'drev_left_z': None,
            'drev_right_z': +Driveline.DREV_Z,
            'drev_r': Driveline.VEV_DREV_R,
        },
    }

    # Z-konvention för axelstacken
    # Pedalvevaxeln slutar nu vid z=±12 (utsidan av sidoramen vid z=±10
    # + 2 cm för att vevarmen ska sitta UTANPÅ ramen). Pedaltappen sticker
    # ut 10 cm därifrån, från z=±12 till z=±22. Lagringen sitter i
    # sidoramen vid z=±10.
    #
    # Fram/bak-vevaxlarna sticker fortfarande ut till z=±15 där C-punkten
    # ankrar på benets z1-plan. Lagringen sitter i sidoramen vid z=±10.
    PEDAL_VEVARM_Z = 12.0      # pedalvevarmens innerkant = utsida av sidoramen + marginal
    PEDAL_TAPP_OUTER_Z = 22.0  # pedaltappens yttre ände (= VEVARM_Z + 10 cm)
    BEN_VEVARM_Z = Driveline.OUTER_Z  # = 15.0, för fram/bak-vevaxlarna

    data['drivelines_z'] = {
        'ram_z': RAM_Z,                                  # = 10.0; lagring sker här
        'drev_z': Driveline.DREV_Z,                      # = 3.0; dreven nära mitten
        'pedal_vevarm_z': PEDAL_VEVARM_Z,                # = 12.0
        'pedal_tapp_outer_z': PEDAL_TAPP_OUTER_Z,        # = 22.0
        'ben_vevarm_z': BEN_VEVARM_Z,                    # = 15.0
        # Bakåtkompatibla namn (används än så länge i JS — avveckla senare)
        'lagerhus_half': Driveline.LAGERHUS_HALF,
        'vevarm_anchor_z': Driveline.VEVARM_ANCHOR_Z,
        'outer_z': Driveline.OUTER_Z,
        'pedal_axle_outer_z': PEDAL_VEVARM_Z,
    }

    # ============================================================
    # Pedalvev (vevarm + pedalplatta)
    # ============================================================
    data['pedal'] = {
        'crank_radius_cm': 17.0,         # vevarmens längd = pedalradien
        'arm_width_cm': 2.0,             # vevarmens bredd (radiellt tvärsnitt)
        'arm_thickness_z_cm': 2.0,       # vevarmens tjocklek i z-led
        # Pedaltappen sticker ut från vevarmens utsida 10 cm i z-led
        'plate_size_cm': [6.0, 2.0, 10.0],
        # Pedalplattans z-centrum (mitten av tappens utstickande del)
        'plate_z_cm': (PEDAL_VEVARM_Z + PEDAL_TAPP_OUTER_Z) / 2,  # = 17.0
        # z-position där vevarmen ankrar på pedalvevaxeln (insida vevarm)
        'vevarm_anchor_z': PEDAL_VEVARM_Z,  # = 12.0
    }

    # ============================================================
    # Ben (Jansen)
    # ============================================================
    from machine import AC, CD, BD, DE, BE, CF, BF, EG, FG, FH, GH
    data['leg'] = {
        'constants': {
            'AC': AC, 'CD': CD, 'BD': BD, 'DE': DE, 'BE': BE,
            'CF': CF, 'BF': BF, 'EG': EG, 'FG': FG, 'FH': FH, 'GH': GH,
        },
        'B_local': [38.0, 7.8],
        'tube_radius_cm': 0.8,  # benstängernas radie i 3D
        # 3D-fackverk: B, E, F, G dupliceras till z2-planet (10 cm inåt mot
        # ramen) som B2, E2, F2, G2. D och H är "spetsar" som binder samman
        # de två planen via trianglarna D-B2-E2 och H-G2-F2. Strukturen är
        # rent visuell — Jansens kinematik är oförändrad.
        'z_offset_cm': 10.0,
        # Stänger i ursprungsplanet (z1). Behåller "A", "B", "C"... som
        # nodnamn — det är samma 11 stänger som tidigare.
        'links_z1': [
            ['A', 'C'], ['C', 'D'], ['B', 'D'], ['D', 'E'], ['B', 'E'],
            ['C', 'F'], ['B', 'F'], ['E', 'G'], ['F', 'G'], ['F', 'H'],
            ['G', 'H'],
        ],
        # Stänger i z2-planet (samma BEFG-topologi)
        'links_z2': [
            ['B2', 'E2'], ['B2', 'F2'], ['E2', 'G2'], ['F2', 'G2'],
        ],
        # Tvärbalkar mellan planen (z-led)
        'links_cross': [
            ['B', 'B2'], ['E', 'E2'], ['F', 'F2'], ['G', 'G2'],
        ],
        # Triangelstänger D→z2 och H→z2 (basen B2E2/F2G2 finns redan ovan)
        'links_apex': [
            ['D', 'B2'], ['D', 'E2'], ['H', 'F2'], ['H', 'G2'],
        ],
    }

    # Bens-instanser
    data['legs'] = []
    for inst, z_off, label in [
        (machine2d.front.left, z_left, 'front_left'),
        (machine2d.front.right, z_right, 'front_right'),
        (machine2d.rear.left, z_left, 'rear_left'),
        (machine2d.rear.right, z_right, 'rear_right'),
    ]:
        data['legs'].append({
            'label': label,
            'A_world': [float(inst.A_world[0]), float(inst.A_world[1])],
            'B_world': [float(inst.leg.B[0]), float(inst.leg.B[1])],
            'phase_offset_deg': float(np.degrees(inst.phase_rad)),
            'yaw_deg': float(np.degrees(inst.yaw_rad)),
            'reverse': inst.reverse,
            'z': z_off,
        })

    # ============================================================
    # Styrmekanism
    # ============================================================
    # Per-ben B-noder med separata triangelstöd. Varje ben har:
    #   - en pivotnod (P för bakben, M för framben) på sin sidoram
    #   - en B-nod som rör sig i en båge kring pivoten när AB förlängs
    #   - en teleskopisk AB-länk från A_world till B
    #   - en fast pivot→B-stång (PB resp MB) med gångjärn vid pivoten
    #
    # AB-baseline är 38.79 cm (Jansens grundkonfiguration). Max förlängning
    # är +4.0 cm. Vid styrutslag åt vänster förlängs vänster sidas AB; vid
    # höger sväng förlängs höger.
    AB_BASELINE = float(np.sqrt(38.0**2 + 7.8**2))  # 38.79 cm
    PB_REAR = 51.01    # fast längd för bakbenets P→B-stöd (cm)
    MB_FRONT = 49.20   # fast längd för frambenets M→B-stöd (cm)
    AB_MAX_OFFSET = 4.0

    # Pivotpositioner per sida. Med raka sidoramar vid z=±10 ligger både
    # P-noden, M-noden, A-noden och B-noden i samma z-plan (±10). Det är
    # *mitt på* B-axeln (som sträcker sig från B1 vid z=±15 till B2 vid z=±5)
    # och ger momentfri infästning av styrmekanismen vid B-leden.
    P_xy = [float(nodes2d['P'][0]), float(nodes2d['P'][1])]
    M_xy = [float(nodes2d['M'][0]), float(nodes2d['M'][1])]
    A_front_xy = [float(nodes2d['A_front'][0]), float(nodes2d['A_front'][1])]
    A_rear_xy = [float(nodes2d['A_rear'][0]), float(nodes2d['A_rear'][1])]
    B_front_xy = [float(nodes2d['B_front'][0]), float(nodes2d['B_front'][1])]
    B_rear_xy = [float(nodes2d['B_rear'][0]), float(nodes2d['B_rear'][1])]

    data['steering'] = {
        'AB_baseline_cm': AB_BASELINE,
        'AB_max_offset_cm': AB_MAX_OFFSET,
        'PB_rear_cm': PB_REAR,
        'MB_front_cm': MB_FRONT,
        'side_z_cm': RAM_Z,
        # Triangelstöden — fyra per maskin (bak-vänster, bak-höger,
        # fram-vänster, fram-höger). Varje stöd har en pivot, en B-baseline-
        # position (där B vilar vid offset 0), och en konstant längd.
        # JS-modulen 'steering.js' beräknar B-positionen för givet offset
        # via cirkelskärning. Allt ligger i z=±RAM_Z-planet.
        'supports': [
            {
                'label': 'rear_left',
                'pivot_name': 'P_left',
                'pivot_xy': P_xy,
                'pivot_z': -RAM_Z,
                'A_xy': A_rear_xy,
                'B_baseline_xy': B_rear_xy,
                'support_length_cm': PB_REAR,
                'side': 'left',
                'position': 'rear',
                'z': -RAM_Z,
            },
            {
                'label': 'rear_right',
                'pivot_name': 'P_right',
                'pivot_xy': P_xy,
                'pivot_z': +RAM_Z,
                'A_xy': A_rear_xy,
                'B_baseline_xy': B_rear_xy,
                'support_length_cm': PB_REAR,
                'side': 'right',
                'position': 'rear',
                'z': +RAM_Z,
            },
            {
                'label': 'front_left',
                'pivot_name': 'M_left',
                'pivot_xy': M_xy,
                'pivot_z': -RAM_Z,
                'A_xy': A_front_xy,
                'B_baseline_xy': B_front_xy,
                'support_length_cm': MB_FRONT,
                'side': 'left',
                'position': 'front',
                'z': -RAM_Z,
            },
            {
                'label': 'front_right',
                'pivot_name': 'M_right',
                'pivot_xy': M_xy,
                'pivot_z': +RAM_Z,
                'A_xy': A_front_xy,
                'B_baseline_xy': B_front_xy,
                'support_length_cm': MB_FRONT,
                'side': 'right',
                'position': 'front',
                'z': +RAM_Z,
            },
        ],
        # UI-slider för styrutslag: -1 (full högersväng) till +1 (full
        # vänstersväng). 0 = rakt. Slidervärdet skalas linjärt till
        # AB-offset 0..AB_MAX_OFFSET för den aktiva sidan.
        'steer_range': [-1.0, +1.0],
        'steer_default': 0.0,
    }

    # ============================================================
    # Sadel — komplett 3D-form
    # ============================================================
    # OBS: dessa parametrar driver buildSaddle i JS. Allt som styr formen
    # SKA komma härifrån, så Python är ensam källa.
    data['saddle'] = {
        'x_rear': -15.0,
        'x_front': 30.0,
        'top_y': 113.0,
        'thickness': 7.0,
        'width_rear': 12.0,
        'width_front': 8.0,
        'concavity': 1.5,
        # Form-parametrar (tidigare hårdkodade i HTML)
        'sit_x_cm': 25.0,            # sittpunktens x (ovansidans referenspunkt)
        'back_offset_cm': 11.0,      # bakdelens höjd över sittpunkten
        'dip_sigma_cm': 8.0,         # konkavitetens utbredning kring sittpunkten
        'front_rise_slope': 0.1,     # uppåtvinkling framför sittpunkten
        # Vevpartiets svängcirkel (för fri rörlighet — informationsfält)
        'crank_clearance': {
            'center_xy': [float(machine2d.frame.A_rear[0]),
                          float(machine2d.frame.A_rear[1])],
            'radius_cm': 15.0,
            'margin_cm': 3.0,
        },
        # UI-gränser (slider för sadelhöjd)
        'height_range_cm': [106.0, 140.0],
    }

    # ============================================================
    # Styre
    # ============================================================
    data['handlebar'] = {
        'center': [float(machine2d.frame.H[0]), float(machine2d.frame.H[1])],
        'half_width': 20.0,
        'tube_radius_cm': 1.0,
        'grip_radius_cm': 1.8,
    }

    # ============================================================
    # Förare (antropometri)
    # ============================================================
    data['rider'] = {
        'height': 194,
        'saddle_xy': [0.0, 113.0],
        'handlebar_xy': [35.0, 110.0],
        'pedal_center_xy': [0.0, 45.0],
        'pedal_radius': 17.0,
        'foot_track_z': 10.0,
        'hand_track_z': 20.0,
        'hip_width': Rider3D.HIP_WIDTH,
        'shoulder_width': Rider3D.SHOULDER_WIDTH,
        'torso_angle_deg': 10.0,
        'proportions': Rider3D.PROPORTIONS,
        # UI-gränser
        'height_range_cm': [140, 210],
        'default_height_cm': 194,
        'default_gender': 'male',
    }

    # ============================================================
    # Mekanik (härlett: drev-utväxling × Jansens steglängd → hastighet)
    # ============================================================
    stats = jansen_analyze()
    data['mechanics'] = {
        'step_length_cm': stats['step_length_cm'],   # ≈ 67.91
        'gear_ratio': Driveline.VEV_DREV_R / Driveline.PEDAL_DREV_R,  # 2.5
        # UI: rpm-slider
        'rpm_range': [10, 120],
        'default_rpm': 10,
    }

    # ============================================================
    # Ergonomi — auto-placering av förare
    # ============================================================
    data['ergonomy'] = {
        # Benlängd som andel av kroppslängd (antropometri).
        # Används både för auto-sadelhöjd och förarens x-placering.
        'leg_length_ratio': 0.465,
        # Mål-utsträckning vid pedalens lägsta läge (95% av maxbenlängd).
        'leg_stretch_target': 0.95,
        # Foten vilar 1 cm över pedalplattans översida + halv fothöjd.
        'pedal_top_offset_cm': 1.0,
        'foot_half_height_ratio': 0.02,  # halv fothöjd som andel av kroppslängd
        # Skanningsfönster för riderXForLeg
        'rider_x_min_cm': -15.0,
        'rider_x_max_cm': 35.0,
        # Styre: handens y ligger n cm ovanför styrets centrum
        'hand_above_handlebar_cm': 3.0,
        # Mannequinets bål-lutning vid körställning (grader)
        'torso_lean_deg': 25.0,
    }

    # ============================================================
    # Scen
    # ============================================================
    data['ground_y'] = 0.0
    data['wheelbase'] = 50.0
    data['track_width'] = track_width

    # Skriv till web/-katalogen relativt detta script (python/ → ../web/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, '..', 'web', 'machine_geometry.json')
    out_path = os.path.normpath(out_path)
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Exporterat: {out_path}")

    return data


if __name__ == '__main__':
    data = export_geometry()
    print(f"Ramnoder: {len(data['frame']['nodes'])}")
    print(f"Ramlänkar: {len(data['frame']['links'])}")
    print(f"Ben: {len(data['legs'])}")
    print(f"Steglängd: {data['mechanics']['step_length_cm']:.2f} cm")
    print(f"Utväxling: 1:{data['mechanics']['gear_ratio']}")
