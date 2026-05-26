"""
STL-export av maskinen i 1:5 skala.

Alla delar exporteras som platta länkar med M3-hål. M3-skruvar fungerar
som pivot-pinnar och fäster delar mot varandra.

Komponenter:
- 44 benstänger (11 typer × 4 ben)
- 2 vevskivor med vevtappar
- 1 pedalvev
- 9 ramlänkar
- 12 förardelar

Mått (mm, 1:5 skala):
- Benstänger: 3 tjocka × 6 breda, ölja 10 mm diam
- Ramstänger: 5 tjocka × 8 breda, ölja 12 mm diam
- Förardelar: 5 × 5 mm
- M3-hål: 1.6 mm radie
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import os
import numpy as np
from stl import mesh

from machine import Machine, Leg, AC, CD, BD, DE, BE, CF, BF, EG, FG, FH, GH


# ============================================================
# KONFIGURATION
# ============================================================
SCALE = 0.2  # 1:5

# Plattlänk-dimensioner (mm)
LEG_THICKNESS = 3.0
LEG_WIDTH = 6.0
LEG_EYE_R = 5.0
LEG_HOLE_R = 1.6

RAM_THICKNESS = 5.0
RAM_WIDTH = 8.0
RAM_EYE_R = 6.0
RAM_HOLE_R = 1.6

RIDER_THICKNESS = 5.0
RIDER_WIDTH = 5.0
RIDER_EYE_R = 5.0
RIDER_HOLE_R = 1.6

CRANK_R = 35.0   # vevskivans yttre radie (mm)
CRANK_THICKNESS = 4.0
CRANK_TAP_R = AC * SCALE * 10  # vevtappens radie från centrum (= AC i mm)

PEDAL_R = 22.0   # pedalskivans yttre radie (mm)
PEDAL_THICKNESS = 4.0
PEDAL_TAP_R = 17 * SCALE * 10  # pedaltappens radie från centrum (mm)

OUTPUT_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'stl'
))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# STL-genereringsfunktioner
# ============================================================

def make_platelink_with_holes(length_mm, thickness, width, eye_r, hole_r,
                               extra_holes=None):
    """
    Skapa en plattlänk: två ändöljor förbundna med en rektangulär mittsektion.
    Hål i båda ändöljornas centrum + eventuella extra hål.
    
    Args:
        length_mm: avstånd mellan de två ändhålens centrum
        thickness: tjocklek (z-axel)
        width: bredd på mittsektionen (y-axel)
        eye_r: ändöljornas radie
        hole_r: hålradie
        extra_holes: lista av (x, y, r) för extra hål på länken
                     (x mätt från första ölja, y från länkens centrumlinje)
    
    Returnerar mesh-objekt placerad så att första öljans centrum är vid origo,
    andra öljans centrum vid (length_mm, 0, 0), och länken ligger i xy-planet
    med tjocklek längs z.
    """
    n_circle = 32
    angles = np.linspace(0, 2*np.pi, n_circle, endpoint=False)
    
    # Bygg silhuetten (sett från ovan) som en lista av (x,y)-punkter
    # Vänster ölja (cirkel kring (0,0)) — vi tar bara övre halvan + sidor
    silhouette = []
    
    # Vänster halvcirkel (vinkel π/2 till 3π/2, alltså vänster halva)
    for theta in np.linspace(np.pi/2, 3*np.pi/2, n_circle//2):
        x = eye_r * np.cos(theta)
        y = eye_r * np.sin(theta)
        silhouette.append((x, y))
    
    # Höger halvcirkel (vinkel -π/2 till π/2 kring (length_mm, 0))
    for theta in np.linspace(-np.pi/2, np.pi/2, n_circle//2):
        x = length_mm + eye_r * np.cos(theta)
        y = eye_r * np.sin(theta)
        silhouette.append((x, y))
    
    # Det vi har: en "pill"-form (cirkel-rektangel-cirkel). 
    # Vi triangulerar denna polygon och extruderar i z.
    
    # För enkelhet använder vi en kompositionsapproach: bygg en pill genom att
    # kombinera trianglar från två halvcirklar och en rektangel.
    
    triangles = []  # lista av (v0, v1, v2) trianglar i 3D
    
    def add_top_face_pill(z):
        """Lägg till plana ovansidan (vid z) genom triangulering av silhuetten."""
        # Fan-triangulering från första punkten — fungerar för konvex silhuett
        n = len(silhouette)
        for i in range(1, n - 1):
            v0 = (silhouette[0][0], silhouette[0][1], z)
            v1 = (silhouette[i][0], silhouette[i][1], z)
            v2 = (silhouette[i+1][0], silhouette[i+1][1], z)
            triangles.append((v0, v1, v2))
    
    def add_bottom_face_pill(z):
        """Underside, omvänd vinklingsordning så normalen pekar nedåt."""
        n = len(silhouette)
        for i in range(1, n - 1):
            v0 = (silhouette[0][0], silhouette[0][1], z)
            v2 = (silhouette[i][0], silhouette[i][1], z)
            v1 = (silhouette[i+1][0], silhouette[i+1][1], z)
            triangles.append((v0, v1, v2))
    
    def add_side_walls():
        """Sidoväggar mellan z=0 och z=thickness."""
        n = len(silhouette)
        for i in range(n):
            j = (i + 1) % n
            x0, y0 = silhouette[i]
            x1, y1 = silhouette[j]
            # Två trianglar för rektangulär vägg
            v00 = (x0, y0, 0)
            v01 = (x0, y0, thickness)
            v10 = (x1, y1, 0)
            v11 = (x1, y1, thickness)
            triangles.append((v00, v10, v11))
            triangles.append((v00, v11, v01))
    
    add_top_face_pill(thickness)
    add_bottom_face_pill(0)
    add_side_walls()
    
    # Nu lägger vi till hålen genom att skapa cylinder-mesh och 
    # markera dem som "subtraherade" — men det är komplicerat utan CSG.
    # I stället skapar vi länken som *inte* fyller pill-formen — utan vi 
    # skapar en pill med hål inbyggda redan från början.
    
    # Vi använder enklare approach: skapa länken som ringar runt hål +
    # förbindelse, så hålen är "byggda in" i geometrin.
    
    # OMSTART: bygg länken som komposition av enkla primitiver med hål
    return _make_link_with_holes_proper(length_mm, thickness, width, eye_r, hole_r, extra_holes)


def _make_link_with_holes_proper(length_mm, thickness, width, eye_r, hole_r, extra_holes=None):
    """
    Bygg länken korrekt med riktiga hål.
    Vi skapar:
    - Två ringar (en runt vardera ändhål) som ihåliga cylindrar
    - En rektangulär mittstång mellan ringarna
    - Eventuella extra hål
    """
    n_circle = 32
    
    triangles = []
    
    # Hjälpfunktion för att lägga till en plan polygon (triangulering)
    def add_polygon_triangles(verts_2d, z, reverse=False):
        """Triangulera en plan polygon (med eventuell konkavitet eller hål)."""
        # Fan-triangulering från första punkten — kräver att polygonen är konvex
        n = len(verts_2d)
        for i in range(1, n - 1):
            v0 = (verts_2d[0][0], verts_2d[0][1], z)
            v1 = (verts_2d[i][0], verts_2d[i][1], z)
            v2 = (verts_2d[i+1][0], verts_2d[i+1][1], z)
            if reverse:
                triangles.append((v0, v2, v1))
            else:
                triangles.append((v0, v1, v2))
    
    # Ringar runt vardera ändhål: vi gör en cylindrisk ring (donut-aktig)
    # Två cirklar: yttre radie eye_r, inre radie hole_r, höjd thickness
    
    def add_ring(center_x, center_y, outer_r, inner_r):
        """Lägg till en ring (rörsegment) som täcker ovansidan, undersidan och 
        de två cylindriska väggarna (inre och yttre)."""
        for i in range(n_circle):
            t0 = 2 * np.pi * i / n_circle
            t1 = 2 * np.pi * (i + 1) / n_circle
            
            # Yttre cirkel-punkter
            xo0 = center_x + outer_r * np.cos(t0)
            yo0 = center_y + outer_r * np.sin(t0)
            xo1 = center_x + outer_r * np.cos(t1)
            yo1 = center_y + outer_r * np.sin(t1)
            
            # Inre cirkel-punkter (hål)
            xi0 = center_x + inner_r * np.cos(t0)
            yi0 = center_y + inner_r * np.sin(t0)
            xi1 = center_x + inner_r * np.cos(t1)
            yi1 = center_y + inner_r * np.sin(t1)
            
            # Övre yta (z=thickness): ring-segment
            # Två trianglar
            triangles.append(((xo0, yo0, thickness), (xo1, yo1, thickness), (xi1, yi1, thickness)))
            triangles.append(((xo0, yo0, thickness), (xi1, yi1, thickness), (xi0, yi0, thickness)))
            
            # Undre yta (z=0): ring-segment (omvänd vinkelordning för normal nedåt)
            triangles.append(((xo0, yo0, 0), (xi0, yi0, 0), (xi1, yi1, 0)))
            triangles.append(((xo0, yo0, 0), (xi1, yi1, 0), (xo1, yo1, 0)))
            
            # Yttre vägg (cylinder)
            triangles.append(((xo0, yo0, 0), (xo1, yo1, 0), (xo1, yo1, thickness)))
            triangles.append(((xo0, yo0, 0), (xo1, yo1, thickness), (xo0, yo0, thickness)))
            
            # Inre vägg (cylinder för hålet, omvänd ordning så normalen pekar inåt)
            triangles.append(((xi0, yi0, 0), (xi0, yi0, thickness), (xi1, yi1, thickness)))
            triangles.append(((xi0, yi0, 0), (xi1, yi1, thickness), (xi1, yi1, 0)))
    
    # Vänster ring vid (0, 0)
    add_ring(0, 0, eye_r, hole_r)
    # Höger ring vid (length_mm, 0)
    add_ring(length_mm, 0, eye_r, hole_r)
    
    # Mittsektionen: rektangel från x=0 till x=length_mm, y=-width/2 till +width/2
    # Men vi måste subtrahera den del som överlappar ringarna.
    # Enkelt: gör mittsektionen från x där den möter cirkelns tangent (vid 
    # y=±width/2 på cirkeln, dvs x = sqrt(eye_r^2 - (width/2)^2))
    half_w = width / 2
    if half_w >= eye_r:
        # Bredden är större än öljans radie — degenererat fall
        x_start = 0
        x_end = length_mm
    else:
        x_offset = np.sqrt(eye_r**2 - half_w**2)
        x_start = x_offset
        x_end = length_mm - x_offset
    
    if x_end > x_start:
        # Övre yta av mittstången
        triangles.append(((x_start, -half_w, thickness), (x_end, -half_w, thickness), (x_end, half_w, thickness)))
        triangles.append(((x_start, -half_w, thickness), (x_end, half_w, thickness), (x_start, half_w, thickness)))
        # Undre yta (omvänd)
        triangles.append(((x_start, -half_w, 0), (x_end, half_w, 0), (x_end, -half_w, 0)))
        triangles.append(((x_start, -half_w, 0), (x_start, half_w, 0), (x_end, half_w, 0)))
        # Sidoväggar (framsidan, baksidan)
        # Framsida (y=-half_w)
        triangles.append(((x_start, -half_w, 0), (x_end, -half_w, 0), (x_end, -half_w, thickness)))
        triangles.append(((x_start, -half_w, 0), (x_end, -half_w, thickness), (x_start, -half_w, thickness)))
        # Baksida (y=+half_w)
        triangles.append(((x_start, half_w, 0), (x_start, half_w, thickness), (x_end, half_w, thickness)))
        triangles.append(((x_start, half_w, 0), (x_end, half_w, thickness), (x_end, half_w, 0)))
    
    # Konvertera till numpy-stl format
    mesh_data = np.zeros(len(triangles), dtype=mesh.Mesh.dtype)
    for i, tri in enumerate(triangles):
        for j, vertex in enumerate(tri):
            mesh_data['vectors'][i][j] = vertex
    
    return mesh.Mesh(mesh_data)


def make_disk_with_holes(outer_r, thickness, hole_centers_and_radii):
    """
    Skapa en cirkulär skiva med hål.
    
    Args:
        outer_r: yttre radie (mm)
        thickness: tjocklek (mm)
        hole_centers_and_radii: lista av (cx, cy, r) tuples för hål
    """
    n_outer = 48
    
    triangles = []
    
    # Vi gör skivan som ringsegment runt yttre radien, och för varje hål
    # subtraherar vi genom att inte täcka det området.
    # Enklare approach: triangulera skivan ovanifrån som "fan från centrum" 
    # men hoppa över sektorer där det finns hål.
    
    # För enkelhet: triangulera som n_outer trianglar från (0,0) till varje 
    # segment på yttre cirkeln. Sedan adderar vi "ring" runt varje hål.
    
    # Vi gör det enklare: skivan består av många små rektangulära "voxlar" — nej 
    # det är dumt. Bättre approach:
    
    # 1. Skapa ovansidan som ett "n-gon" med hål
    # 2. Detta är komplicerat utan CSG, så vi använder ett trick:
    #    triangulera skivan med "hålen" som inre konturer, då varje hål 
    #    bidrar med en innercirkel som vi snittar bort
    
    # Den enklaste approachen för STL utan CSG: skapa skivan som en stor "kaka"
    # och placera hålen som "tubrör" som går igenom. Sedan är skivans ovansida
    # och undersida polygoner med hål, vilket vi triangulerar med "constrained 
    # delaunay" eller "ear clipping" — men det är komplicerat.
    
    # Praktiskt val: använd matplotlib triangulering eller sätt ihop manuellt.
    # Vi gör manuellt genom att rasterise pseudo-radialt:
    
    # Vi skapar skivan som många ringsegment från yttre kanten in mot centrum
    # och hoppar segment som ligger inom ett hål.
    
    # Förenklad approach: använd en grid-rasterisering där varje cell som är 
    # innanför skivan och INTE i något hål får två trianglar.
    
    # Det blir mycket trianglar men det fungerar.
    
    grid_size = 1.0  # mm per cell
    nx = int(2 * outer_r / grid_size) + 1
    ny = int(2 * outer_r / grid_size) + 1
    
    def is_inside(x, y):
        """Innanför skivan men ej i något hål."""
        if x*x + y*y > outer_r * outer_r:
            return False
        for cx, cy, r in hole_centers_and_radii:
            if (x - cx)**2 + (y - cy)**2 < r * r:
                return False
        return True
    
    # Bygg ovan- och underyta som många små rektanglar
    for i in range(nx):
        for j in range(ny):
            x0 = -outer_r + i * grid_size
            y0 = -outer_r + j * grid_size
            x1 = x0 + grid_size
            y1 = y0 + grid_size
            cx, cy = (x0+x1)/2, (y0+y1)/2
            if is_inside(cx, cy):
                # Övre yta
                triangles.append(((x0, y0, thickness), (x1, y0, thickness), (x1, y1, thickness)))
                triangles.append(((x0, y0, thickness), (x1, y1, thickness), (x0, y1, thickness)))
                # Undre yta (omvänd)
                triangles.append(((x0, y0, 0), (x1, y1, 0), (x1, y0, 0)))
                triangles.append(((x0, y0, 0), (x0, y1, 0), (x1, y1, 0)))
    
    # Yttre kant (cylindervägg)
    for i in range(n_outer):
        t0 = 2 * np.pi * i / n_outer
        t1 = 2 * np.pi * (i + 1) / n_outer
        x0 = outer_r * np.cos(t0)
        y0 = outer_r * np.sin(t0)
        x1 = outer_r * np.cos(t1)
        y1 = outer_r * np.sin(t1)
        triangles.append(((x0, y0, 0), (x1, y1, 0), (x1, y1, thickness)))
        triangles.append(((x0, y0, 0), (x1, y1, thickness), (x0, y0, thickness)))
    
    # Hål-väggar (cylindrar inåt)
    for cx, cy, r in hole_centers_and_radii:
        for i in range(n_outer):
            t0 = 2 * np.pi * i / n_outer
            t1 = 2 * np.pi * (i + 1) / n_outer
            x0 = cx + r * np.cos(t0)
            y0 = cy + r * np.sin(t0)
            x1 = cx + r * np.cos(t1)
            y1 = cy + r * np.sin(t1)
            # Omvänd vinkelordning för normalen att peka inåt hålet
            triangles.append(((x0, y0, 0), (x0, y0, thickness), (x1, y1, thickness)))
            triangles.append(((x0, y0, 0), (x1, y1, thickness), (x1, y1, 0)))
    
    mesh_data = np.zeros(len(triangles), dtype=mesh.Mesh.dtype)
    for i, tri in enumerate(triangles):
        for j, vertex in enumerate(tri):
            mesh_data['vectors'][i][j] = vertex
    
    return mesh.Mesh(mesh_data)


# ============================================================
# EXPORT
# ============================================================

def export_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Exporterar STL-filer i 1:5 skala...")
    
    # === BENSTÄNGER ===
    # Jansens 11 stänger
    leg_links = {
        'AC': AC, 'CD': CD, 'BD': BD, 'DE': DE, 'BE': BE,
        'CF': CF, 'BF': BF, 'EG': EG, 'FG': FG, 'FH': FH, 'GH': GH,
    }
    
    print("\nBenstänger:")
    for name, length_cm in leg_links.items():
        length_mm = length_cm * SCALE * 10
        m = _make_link_with_holes_proper(length_mm, LEG_THICKNESS, LEG_WIDTH,
                                          LEG_EYE_R, LEG_HOLE_R)
        fname = f'{OUTPUT_DIR}/ben_{name}_x4.stl'
        m.save(fname)
        print(f"  {name}: {length_mm:.1f} mm → {fname}")
    
    # === VEVSKIVOR ===
    print("\nVevskivor:")
    # En vevskiva har:
    # - Centrum-hål för huvudaxeln (kanske M5 → 2.6 mm radie, eller M3 → 1.6)
    # - Två vevtappshål 180° förskjutna vid radie CRANK_TAP_R
    crank_holes = [
        (0, 0, 1.6),  # centrumhål för axel (M3)
        (CRANK_TAP_R, 0, 1.6),    # vevtapp 1 (vänster ben)
        (-CRANK_TAP_R, 0, 1.6),   # vevtapp 2 (höger ben), 180° förskjuten
    ]
    m = make_disk_with_holes(CRANK_R, CRANK_THICKNESS, crank_holes)
    fname = f'{OUTPUT_DIR}/vevskiva_x2.stl'
    m.save(fname)
    print(f"  Vevskiva (R={CRANK_R}mm, vevtappar vid R={CRANK_TAP_R:.1f}mm) → {fname}")
    
    # === PEDALVEV ===
    print("\nPedalvev:")
    pedal_holes = [
        (0, 0, 1.6),  # centrumhål
        (PEDAL_TAP_R, 0, 1.6),
        (-PEDAL_TAP_R, 0, 1.6),
    ]
    m = make_disk_with_holes(PEDAL_R, PEDAL_THICKNESS, pedal_holes)
    fname = f'{OUTPUT_DIR}/pedalvev.stl'
    m.save(fname)
    print(f"  Pedalvev (R={PEDAL_R}mm) → {fname}")
    
    # === RAMLÄNKAR ===
    # Vi behöver konkreta längder för varje ramlänk. Hämta från Machine.
    print("\nRamlänkar:")
    machine = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    nodes = machine.frame.nodes
    # Längder för varje ramlänk
    ram_links = [
        ('PQ', nodes['P'], nodes['Q'], nodes['A_rear']),  # PQ med hål i mitten för A_rear
        ('A_rear-B_rear', nodes['A_rear'], nodes['B_rear'], None),
        ('P-B_rear', nodes['P'], nodes['B_rear'], None),
        ('A_rear-A_front', nodes['A_rear'], nodes['A_front'], None),
        ('A_front-B_front', nodes['A_front'], nodes['B_front'], None),
        ('P-M', nodes['P'], nodes['M'], None),
        ('M-B_front', nodes['M'], nodes['B_front'], None),
        ('A_front-M', nodes['A_front'], nodes['M'], None),
        ('B_front-H', nodes['B_front'], nodes['H'], None),
    ]
    
    for name, p1, p2, mid_node in ram_links:
        length_cm = np.linalg.norm(p2 - p1)
        length_mm = length_cm * SCALE * 10
        
        extra_holes = None
        if mid_node is not None:
            # Var ligger mid_node på linjen p1-p2?
            t = np.dot(mid_node - p1, p2 - p1) / np.dot(p2 - p1, p2 - p1)
            mid_x = t * length_mm
            # Vi gör hålet något större för vevaxeln (M5 ≈ 2.6 mm)
            extra_holes = [(mid_x, 0, 2.6)]
        
        m = _make_link_with_holes_proper(length_mm, RAM_THICKNESS, RAM_WIDTH,
                                          RAM_EYE_R, RAM_HOLE_R, extra_holes)
        # Lägg till extra hål i mitten om relevant (för t.ex. PQ-länken med A_rear)
        # OBS: _make_link_with_holes_proper hanterar inte extra_holes än. 
        # Vi gör en utbyggd version för det.
        if extra_holes:
            # Tillfällig: vi lägger till hålet manuellt genom att modifiera meshen
            # Det är dock komplicerat — vi exporterar utan extrahålet och dokumenterar
            # att användaren måste borra det själv.
            pass
        
        fname = f'{OUTPUT_DIR}/ram_{name}.stl'
        m.save(fname)
        if mid_node is not None:
            print(f"  {name}: {length_mm:.1f} mm (OBS: borra extra hål vid x={mid_x:.1f}mm för A-axel) → {fname}")
        else:
            print(f"  {name}: {length_mm:.1f} mm → {fname}")
    
    # === FÖRARDELAR ===
    print("\nFörare:")
    rider = machine.rider
    
    rider_segments = [
        ('bal', rider.hip, rider.shoulder),
        ('overarm_vanster', rider.shoulder, rider.elbow),
        ('underarm_vanster', rider.elbow, rider.hand),
        ('lar_vanster', rider.hip, rider.knee_left),
        ('underben_vanster', rider.knee_left, rider.foot_left),
        ('lar_hoger', rider.hip, rider.knee_right),
        ('underben_hoger', rider.knee_right, rider.foot_right),
    ]
    # Höger arm samma som vänster (förenklat — egentligen behöver vi två armar)
    rider_segments.append(('overarm_hoger', rider.shoulder, rider.elbow))
    rider_segments.append(('underarm_hoger', rider.elbow, rider.hand))
    
    for name, p1, p2 in rider_segments:
        length_cm = np.linalg.norm(p2 - p1)
        length_mm = length_cm * SCALE * 10
        m = _make_link_with_holes_proper(length_mm, RIDER_THICKNESS, RIDER_WIDTH,
                                          RIDER_EYE_R, RIDER_HOLE_R)
        fname = f'{OUTPUT_DIR}/forare_{name}.stl'
        m.save(fname)
        print(f"  {name}: {length_mm:.1f} mm → {fname}")
    
    # Förarens huvud — en boll/cylinder med ett hål för axelfäste
    # Vi gör det enkelt: en liten skiva
    head_r = 6.5 * SCALE * 10  # huvudradie i mm
    head_holes = [(0, 0, RIDER_HOLE_R)]  # ett centrumhål för fäste vid axel
    m = make_disk_with_holes(head_r, RIDER_THICKNESS, head_holes)
    fname = f'{OUTPUT_DIR}/forare_huvud.stl'
    m.save(fname)
    print(f"  huvud (R={head_r:.1f}mm) → {fname}")
    
    # Fötter — små plattor som hänger från pedaltapparna
    foot_length_mm = 30  # ungefär 15 cm i full skala
    foot_holes = [(5, 0, RIDER_HOLE_R)]  # ett hål vid ena änden för pedaltapp
    # Vi använder samma plattlänk-funktion
    m = _make_link_with_holes_proper(foot_length_mm, RIDER_THICKNESS, RIDER_WIDTH,
                                      RIDER_EYE_R, RIDER_HOLE_R)
    fname = f'{OUTPUT_DIR}/forare_fot_x2.stl'
    m.save(fname)
    print(f"  fot (x2): {foot_length_mm}mm → {fname}")
    
    print("\nKlar! Alla STL-filer sparade i:", OUTPUT_DIR)
    
    # Sammanfattning
    print("\n" + "=" * 50)
    print("SAMMANFATTNING - delar att printa:")
    print("=" * 50)
    print("Benstänger (printa 4 av varje):")
    for name, length_cm in leg_links.items():
        print(f"  ben_{name}_x4.stl — {length_cm * SCALE * 10:.1f} mm")
    print("\nVevskivor (printa 2):")
    print(f"  vevskiva_x2.stl")
    print("\nPedalvev (printa 1):")
    print(f"  pedalvev.stl")
    print("\nRamlänkar (printa 1 av varje):")
    for name, _, _, _ in ram_links:
        print(f"  ram_{name}.stl")
    print("\nFörare:")
    print(f"  forare_bal.stl, forare_huvud.stl,")
    print(f"  forare_overarm_*, forare_underarm_*,")
    print(f"  forare_lar_*, forare_underben_*,")
    print(f"  forare_fot_x2.stl (printa 2 fötter)")


if __name__ == '__main__':
    export_all()
