"""
machine3d.py — 3D-utbyggnad av maskinmodellen.

Etapp 1: Grundläggande 3D-koordinater och projektion.
Importerar och bygger på 2D-kärnan i machine.py.

Punkter i 3D är np.array([x, y, z]) där:
  x = framåt (färdriktning)
  y = uppåt (mot taket)
  z = sidled (positiv = höger sida från färdrikntningen sett)

Kameror:
  side  — tittar från +z (höger sida) mot vänster
  front — tittar från +x (framifrån) mot maskinen
  top   — tittar från +y (ovanifrån) ner mot marken
  iso   — isometrisk vy snett uppifrån
"""

import sys
sys.path.insert(0, '/mnt/user-data/outputs')

import numpy as np
from machine import (
    Leg, LegInstance, LegPair, Machine, Frame,
    Canvas, AC, CD, BD, DE, BE, CF, BF, EG, FG, FH, GH
)


# ============================================================
# Camera & projection
# ============================================================
class Camera:
    """
    Definierar en vy: var kameran tittar från och vilken riktning.
    
    Använder ortografisk projektion (parallella linjer behåller längd).
    """
    
    def __init__(self, view='side'):
        """
        view kan vara: 'side', 'front', 'rear', 'top', 'iso'
        """
        self.view = view
    
    def project(self, point3d):
        """
        Projektera en 3D-punkt till 2D-skärmkoord.
        
        Returnerar (sx, sy, depth) där:
          sx, sy = 2D-koord på skärmen (samma enhet som världen)
          depth = djup från kameran (för z-sortering, större=närmare)
        """
        x, y, z = point3d[0], point3d[1], point3d[2]
        
        if self.view == 'side':
            # Tittar från +z mot origo. x→höger på skärm, y→upp på skärm.
            # Närmare objekt har större z.
            return (x, y, z)
        
        elif self.view == 'front':
            # Tittar från +x mot origo. -z→höger på skärm, y→upp.
            # Närmare = större x.
            return (-z, y, x)
        
        elif self.view == 'rear':
            # Tittar från -x mot origo. +z→höger, y→upp.
            return (z, y, -x)
        
        elif self.view == 'top':
            # Tittar från +y nedåt. x→höger, -z→upp på skärm.
            # Närmare = större y.
            return (x, -z, y)
        
        elif self.view == 'iso':
            # Isometrisk: snett uppifrån från +x, +y, +z
            # Klassisk 30°-vy: x och z ger horisontella komponenter
            # som lutar 30° från horisontell, y ger vertikal komponent
            cos30 = np.cos(np.radians(30))
            sin30 = np.sin(np.radians(30))
            sx = (x - z) * cos30
            sy = y - (x + z) * sin30
            # Depth: större = närmare kameran (kombination av x, y och -z)
            depth = x + y - z
            return (sx, sy, depth)
        
        else:
            raise ValueError(f"Okänd vy: {self.view}")
    
    def project_many(self, points3d):
        """Projektera flera punkter samtidigt."""
        return [self.project(p) for p in points3d]


# ============================================================
# Canvas3D — ritsystem med projektion och z-sortering
# ============================================================
class Canvas3D:
    """
    Canvas som tar emot 3D-objekt, projicerar dem via en kamera, 
    och z-sorterar så att närmare objekt ritas över längre.
    """
    
    def __init__(self, camera, x_min, x_max, y_min, y_max, pad=15):
        self.camera = camera
        # 2D-canvas under huven
        self.canvas2d = Canvas(x_min, x_max, y_min, y_max, pad=pad)
        # Buffer av ritkommandon med depth för z-sortering
        self.drawables = []
    
    @property
    def width(self):
        return self.canvas2d.width
    
    @property
    def height(self):
        return self.canvas2d.height
    
    @property
    def x_min(self):
        return self.canvas2d.x_min
    
    @property
    def y_max(self):
        return self.canvas2d.y_max
    
    def w(self, p2d):
        """Vidarebefordra världs-till-skärm-koord till underliggande canvas."""
        return self.canvas2d.w(p2d)
    
    def add_raw(self, svg_string):
        """Lägg till SVG-element utan z-sortering (t.ex. grid, mark)."""
        self.canvas2d.add(svg_string)
    
    def add(self, svg_string):
        """Backward-kompatibilitet."""
        self.canvas2d.add(svg_string)
    
    def polygon3d(self, points3d, fill='#888', stroke=None, stroke_width=0.5,
                   opacity=1.0):
        """
        Rita en fylld polygon från en lista av 3D-punkter.
        Punkterna projiceras och en SVG-polygon ritas med djupet=medel-z.
        """
        projected = [self.camera.project(p) for p in points3d]
        depth = sum(s[2] for s in projected) / len(projected)
        
        # Bygg points-attribut
        pts_2d = []
        for s in projected:
            sx_screen, sy_screen = self.canvas2d.w([s[0], s[1]])
            pts_2d.append(f"{sx_screen:.2f},{sy_screen:.2f}")
        points_str = " ".join(pts_2d)
        
        attrs = f'points="{points_str}" fill="{fill}"'
        if stroke:
            attrs += f' stroke="{stroke}" stroke-width="{stroke_width}"'
        else:
            attrs += ' stroke="none"'
        if opacity != 1.0:
            attrs += f' opacity="{opacity}"'
        
        svg = f'<polygon {attrs}/>'
        
        def draw():
            self.canvas2d.add(svg)
        self.drawables.append((depth, draw))
    
    def line3d(self, p1, p2, color='#222', width=1.0, opacity=1.0,
                dasharray=None):
        """Rita en linje mellan två 3D-punkter."""
        s1 = self.camera.project(p1)
        s2 = self.camera.project(p2)
        depth = (s1[2] + s2[2]) / 2  # genomsnittligt djup
        # Skapa 2D-koord
        p1_2d = [s1[0], s1[1]]
        p2_2d = [s2[0], s2[1]]
        # Sparas som ritkommando med depth
        def draw():
            self.canvas2d.line(p1_2d, p2_2d, color=color, width=width,
                                opacity=opacity, dasharray=dasharray)
        self.drawables.append((depth, draw))
    
    def circle3d(self, center, radius, fill='#fff', stroke='#222',
                  stroke_width=0.5, opacity=1.0, dasharray=None):
        """Rita en cirkel vid 3D-position (radie i 2D-skärmkoord)."""
        s = self.camera.project(center)
        center_2d = [s[0], s[1]]
        depth = s[2]
        def draw():
            self.canvas2d.circle(center_2d, radius, fill=fill, stroke=stroke,
                                  stroke_width=stroke_width, opacity=opacity,
                                  dasharray=dasharray)
        self.drawables.append((depth, draw))
    
    def text3d(self, position, text, size=4, color='#222', anchor='start',
                weight='normal', dx=0, dy=0):
        """Rita text vid 3D-position."""
        s = self.camera.project(position)
        position_2d = [s[0], s[1]]
        depth = s[2]
        def draw():
            self.canvas2d.text(position_2d, text, size=size, color=color,
                                anchor=anchor, weight=weight, dx=dx, dy=dy)
        self.drawables.append((depth, draw))
    
    def flush(self):
        """Sortera och rita alla 3D-element. Anropas innan save."""
        # Sortera med stigande depth (längst bort först, närmast sist)
        self.drawables.sort(key=lambda d: d[0])
        for depth, draw_fn in self.drawables:
            draw_fn()
        self.drawables = []
    
    def grid(self, spacing=10, color='#eee'):
        self.canvas2d.grid(spacing=spacing, color=color)
    
    def save(self, filename, width_px=1100):
        self.flush()
        return self.canvas2d.save(filename, width_px=width_px)


# ============================================================
# Hjälpfunktioner: utöka 2D-punkter till 3D
# ============================================================
def to_3d(point2d, z=0.0):
    """Konvertera 2D-punkt till 3D genom att lägga till z-koordinat."""
    return np.array([point2d[0], point2d[1], z])


def points_3d(points2d, z=0.0):
    """Konvertera lista/array av 2D-punkter till 3D."""
    return [to_3d(p, z) for p in points2d]


# ============================================================
# Demo: rita en placeholder-maskin från flera vyer
# ============================================================
def demo_etapp1():
    """
    Etapp 1: Bygg en enkel 3D-modell av maskinen som platta i z=0,
    och visa den från olika vyer för att verifiera projektionen.
    """
    # Använd den befintliga 2D-maskinen som bas
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    # För varje vy: skapa en Canvas3D, rita ramen och en placeholder för ben
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar vy: {view_name}")
        camera = Camera(view=view_name)
        
        # Beräkna extents för canvas: projicera alla intressanta punkter
        # och hitta omfång i projicerade x och y
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        # Lägg till markpunkter
        all_points.append(np.array([machine2d.frame.A_front[0] + 50, 0, 0]))
        all_points.append(np.array([machine2d.frame.A_rear[0] - 50, 0, 0]))
        all_points.append(np.array([0, 0, 20]))
        all_points.append(np.array([0, 0, -20]))
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        # Pad
        x_min -= 20
        x_max += 20
        y_min -= 20
        y_max += 20
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark (y=0) — rita som horisontell linje i sida/front, eller som plan i top
        if view_name in ('side', 'front', 'rear', 'iso'):
            # Mark är vid y=0 (i världen). Rita en linje från z=-50 till z=+50 vid 
            # x-spannet vi visar
            ground_left = np.array([x_min, 0, 0])
            ground_right = np.array([x_max, 0, 0])
            # I 3D är marken ett plan, men vi visar bara en linje vid z=0
            # för sidvyer
            if view_name == 'front':
                # Mark sträcker sig från z=-50 till z=+50
                canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                              color='#555', width=0.5)
            elif view_name == 'iso':
                # I iso-vyn ritar vi en mark-fyrkant
                corners = [
                    np.array([-50, 0, -30]), np.array([150, 0, -30]),
                    np.array([150, 0, 30]),  np.array([-50, 0, 30]),
                ]
                for i in range(4):
                    canvas.line3d(corners[i], corners[(i+1) % 4],
                                  color='#999', width=0.3, opacity=0.5)
            else:  # side
                canvas.line3d(ground_left, ground_right,
                              color='#555', width=0.5)
        
        # Ramnoder och länkar (alla vid z=0 just nu)
        nodes_2d = machine2d.frame.nodes
        nodes_3d = {name: to_3d(p, z=0) for name, p in nodes_2d.items()}
        
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#1976D2', width=1.4, opacity=0.85)
        
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.5, fill='#0D47A1', stroke='white',
                            stroke_width=0.4)
            canvas.text3d(p, name, size=3.5, color='black',
                          weight='bold', dx=3, dy=-1.5)
        
        # Placeholder för ben — bara visa benens fotbanor som z=±15 (spårvidd 30)
        track_width = 30  # cm
        z_left = -track_width / 2
        z_right = +track_width / 2
        
        for inst, z_off, color in [
            (machine2d.front.left,  z_left,  '#E65100'),
            (machine2d.front.right, z_right, '#E65100'),
            (machine2d.rear.left,   z_left,  '#1976D2'),
            (machine2d.rear.right,  z_right, '#1976D2'),
        ]:
            path = inst.foot_path(60)
            # Rita banan som en serie linjer
            for i in range(len(path)):
                p1 = to_3d(path[i], z=z_off)
                p2 = to_3d(path[(i+1) % len(path)], z=z_off)
                canvas.line3d(p1, p2, color=color, width=0.5, opacity=0.5)
        
        # Titel
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 1: vy = {view_name}</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e1_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


def render_leg_3d(canvas, leg_inst, theta_global, z_offset,
                   color_scheme=None, opacity=1.0):
    """
    Rita ett helt ben i 3D vid given z-position.
    
    Benets kinematik beräknas i 2D (i benets eget vertikala plan), och 
    sedan placeras varje punkt vid z=z_offset.
    
    Args:
        canvas: Canvas3D
        leg_inst: LegInstance (från machine.py)
        theta_global: vevvinkel
        z_offset: z-position för benets plan
        color_scheme: dict med färger per länk (default = standardfärger)
        opacity: opacitet för alla länkar
    """
    pose = leg_inst.pose(theta_global)
    if pose is None:
        return
    
    # Standardfärger för länkar
    if color_scheme is None:
        color_scheme = {
            ('A', 'C'): '#1565C0',  # vevarm
            ('C', 'D'): '#2E7D32',
            ('B', 'D'): '#C62828',
            ('D', 'E'): '#E57373',
            ('B', 'E'): '#C62828',
            ('C', 'F'): '#EF6C00',
            ('B', 'F'): '#9E9D24',
            ('E', 'G'): '#7B1FA2',
            ('F', 'G'): '#0288D1',
            ('F', 'H'): '#1565C0',
            ('G', 'H'): '#1565C0',
        }
    
    leg_links = [
        ('A', 'C'), ('C', 'D'), ('B', 'D'), ('D', 'E'), ('B', 'E'),
        ('C', 'F'), ('B', 'F'), ('E', 'G'), ('F', 'G'),
        ('F', 'H'), ('G', 'H'),
    ]
    
    for p1_name, p2_name in leg_links:
        p1_3d = to_3d(pose[p1_name], z=z_offset)
        p2_3d = to_3d(pose[p2_name], z=z_offset)
        color = color_scheme.get((p1_name, p2_name), '#666')
        width = 1.3 if (p1_name, p2_name) == ('A', 'C') else 1.0
        canvas.line3d(p1_3d, p2_3d, color=color, width=width, opacity=opacity)
    
    # Leder som små punkter
    for joint_name in ['B', 'C', 'D', 'E', 'F', 'G', 'H']:
        p = to_3d(pose[joint_name], z=z_offset)
        radius = 1.0 if joint_name == 'H' else 0.7
        fill = '#1B5E20' if joint_name == 'H' else '#222'
        canvas.circle3d(p, radius, fill=fill, stroke='white',
                        stroke_width=0.3, opacity=opacity)


def render_foot_path_3d(canvas, leg_inst, z_offset, color='#1976D2',
                         width=0.4, opacity=0.4):
    """Rita fotbanans hela kurva i 3D vid z_offset."""
    path = leg_inst.foot_path(120)
    for i in range(len(path)):
        p1 = to_3d(path[i], z=z_offset)
        p2 = to_3d(path[(i+1) % len(path)], z=z_offset)
        canvas.line3d(p1, p2, color=color, width=width, opacity=opacity)


# ============================================================
# Demo: rita hela maskinen från flera vyer
# ============================================================
def demo_etapp2():
    """
    Etapp 2: Hela maskinen ritad i 3D — alla fyra benen, ramen, från alla vyer.
    """
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    track_width = 30  # cm
    z_left = -track_width / 2
    z_right = +track_width / 2
    
    theta_global = np.radians(60)  # samma som tidigare demo
    
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar etapp 2 vy: {view_name}")
        camera = Camera(view=view_name)
        
        # Hitta extents genom att projicera nyckelpunkter
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        # Benens fotbanor
        for inst, z_off in [
            (machine2d.front.left, z_left), (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left), (machine2d.rear.right, z_right),
        ]:
            path = inst.foot_path(30)
            for p in path:
                all_points.append(to_3d(p, z=z_off))
        all_points.append(np.array([-50, -5, 0]))
        all_points.append(np.array([150, -5, 0]))
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        
        x_min, x_max = min(xs) - 10, max(xs) + 10
        y_min, y_max = min(ys) - 10, max(ys) + 10
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark
        if view_name == 'side':
            ground_left = np.array([x_min, 0, 0])
            ground_right = np.array([x_max, 0, 0])
            canvas.line3d(ground_left, ground_right, color='#555', width=0.5)
        elif view_name == 'front':
            canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                          color='#555', width=0.5)
        elif view_name == 'top':
            # I top-vyn syns marken som hela bilden
            pass
        elif view_name == 'iso':
            # Mark-fyrkant
            corners = [
                np.array([-80, 0, -30]), np.array([150, 0, -30]),
                np.array([150, 0, 30]),  np.array([-80, 0, 30]),
            ]
            for i in range(4):
                canvas.line3d(corners[i], corners[(i+1) % 4],
                              color='#999', width=0.3, opacity=0.5)
        
        # Färdriktning
        if view_name == 'side':
            canvas.line3d(np.array([20, -5, 0]), np.array([60, -5, 0]),
                          color='#2E7D32', width=0.9)
        elif view_name == 'top':
            canvas.line3d(np.array([20, 0, -25]), np.array([60, 0, -25]),
                          color='#2E7D32', width=0.9)
        
        # Ramen (z=0)
        nodes_3d = {name: to_3d(p, z=0) for name, p in machine2d.frame.nodes.items()}
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#5D4037', width=1.6, opacity=0.9)
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.3, fill='#3E2723', stroke='white',
                            stroke_width=0.4)
        
        # VEVAXLAR — genomgående axlar från z=-track_width/2 till +track_width/2
        for ax_pos, ax_label in [(machine2d.frame.A_rear, 'A_rear'),
                                   (machine2d.frame.A_front, 'A_front')]:
            p1 = np.array([ax_pos[0], ax_pos[1], z_left])
            p2 = np.array([ax_pos[0], ax_pos[1], z_right])
            canvas.line3d(p1, p2, color='#222', width=2.0, opacity=0.9)
        
        # Benen — alla fyra
        # Färgschema: lite olika opacity för att se vänster/höger
        for inst, z_off, label in [
            (machine2d.front.left, z_left, 'FV'),
            (machine2d.front.right, z_right, 'FH'),
            (machine2d.rear.left, z_left, 'BV'),
            (machine2d.rear.right, z_right, 'BH'),
        ]:
            render_leg_3d(canvas, inst, theta_global, z_off, opacity=0.9)
            render_foot_path_3d(canvas, inst, z_off,
                                 color='#1976D2' if 'V' in label else '#E65100',
                                 width=0.35, opacity=0.35)
        
        # Titel
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 2: maskinen i 3D · vy = {view_name}</text>')
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="11" '
                        f'font-size="2.8" fill="#666" text-anchor="middle">'
                        f'spårvidd {track_width} cm · ramen vid z=0 · ben vid z=±{track_width/2:.0f}</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e2_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


# ============================================================
# Rider3D — förare med utbredning i z-led
# ============================================================
class Rider3D:
    """
    3D-förare med utbredning i höft, axlar och händer/fötter.
    
    Beräknar 3D-positioner för alla leder baserat på:
    - Central höft- och axelposition i sagittalplanet (från 2D-modellen)
    - Utbredning i z-led för höft, axlar, knän, händer, fötter
    """
    
    PROPORTIONS = {
        'sitting_height': 0.52,
        'torso': 0.30,
        'head': 0.13,
        'thigh': 0.25,
        'shin': 0.25,
        'upper_arm': 0.19,
        'forearm': 0.15,
    }
    
    # Utbredning i z-led (cm)
    HIP_WIDTH = 35       # höftbredd
    SHOULDER_WIDTH = 45  # axelbredd
    HEAD_WIDTH = 16      # huvudbredd (för cirkulär visning)
    
    def __init__(self, height=194, saddle_xy=(0, 113), handlebar_xy=(35, 110),
                 pedal_center_xy=(0, 45), pedal_radius=17,
                 theta_global=0.0, torso_angle_deg=10,
                 foot_track_z=10, hand_track_z=20):
        """
        Args:
            theta_global: vevvinkel (för att placera fötter på rätt pedalposition)
            foot_track_z: |z| för förarens fötter (default 10, mitten av pedalen)
            hand_track_z: |z| för förarens händer
        """
        self.height = height
        self.saddle_xy = np.asarray(saddle_xy, dtype=float)
        self.handlebar_xy = np.asarray(handlebar_xy, dtype=float)
        self.pedal_center_xy = np.asarray(pedal_center_xy, dtype=float)
        self.pedal_radius = pedal_radius
        # Pedalvinkel synkroniserad med theta_global, som driveline
        self.pedal_angle_left = -theta_global + np.pi / 2
        self.torso_angle = np.radians(torso_angle_deg)
        self.foot_z = foot_track_z
        self.hand_z = hand_track_z
        
        self._compute_joints()
    
    def _segment(self, name):
        return self.height * self.PROPORTIONS[name]
    
    def _compute_joints(self):
        """Beräkna alla led-positioner i 3D."""
        # Höftens mitt = sadel-position. Höften är utbredd i z-led.
        hip_mid = np.array([self.saddle_xy[0], self.saddle_xy[1], 0])
        self.hip_left = hip_mid + np.array([0, 0, -self.HIP_WIDTH/2])
        self.hip_right = hip_mid + np.array([0, 0, +self.HIP_WIDTH/2])
        self.hip_mid = hip_mid
        
        # Bålen lutar framåt. Axelmitten:
        torso_len = self._segment('torso')
        shoulder_mid_xy = self.saddle_xy + torso_len * np.array([
            np.sin(self.torso_angle), np.cos(self.torso_angle)
        ])
        self.shoulder_mid = np.array([shoulder_mid_xy[0], shoulder_mid_xy[1], 0])
        self.shoulder_left = self.shoulder_mid + np.array([0, 0, -self.SHOULDER_WIDTH/2])
        self.shoulder_right = self.shoulder_mid + np.array([0, 0, +self.SHOULDER_WIDTH/2])
        
        # Huvud
        head_len = self._segment('head')
        head_center_xy = shoulder_mid_xy + (head_len * 0.6) * np.array([
            np.sin(self.torso_angle), np.cos(self.torso_angle)
        ])
        self.head_center = np.array([head_center_xy[0], head_center_xy[1], 0])
        self.head_top = self.head_center + np.array([
            head_len * 0.4 * np.sin(self.torso_angle),
            head_len * 0.4 * np.cos(self.torso_angle),
            0,
        ])
        
        # Händer på styret — utbredda i z-led
        self.hand_left = np.array([self.handlebar_xy[0], self.handlebar_xy[1],
                                    -self.hand_z])
        self.hand_right = np.array([self.handlebar_xy[0], self.handlebar_xy[1],
                                     +self.hand_z])
        
        # Armbågar via inverse kinematik i ZY-planet för varje arm
        upper_arm_len = self._segment('upper_arm')
        forearm_len = self._segment('forearm')
        self.elbow_left = self._ik_3d(self.shoulder_left, self.hand_left,
                                       upper_arm_len, forearm_len,
                                       bend_dir='down_back')
        self.elbow_right = self._ik_3d(self.shoulder_right, self.hand_right,
                                        upper_arm_len, forearm_len,
                                        bend_dir='down_back')
        
        # Fötter på pedaler — utbredda i z-led, synkade med pedalvinkeln
        # Vänster pedal i sin fas, höger 180° förskjuten
        foot_left_xy = self.pedal_center_xy + self.pedal_radius * np.array([
            np.cos(self.pedal_angle_left), np.sin(self.pedal_angle_left)
        ])
        foot_right_xy = self.pedal_center_xy + self.pedal_radius * np.array([
            np.cos(self.pedal_angle_left + np.pi), np.sin(self.pedal_angle_left + np.pi)
        ])
        self.foot_left = np.array([foot_left_xy[0], foot_left_xy[1], -self.foot_z])
        self.foot_right = np.array([foot_right_xy[0], foot_right_xy[1], +self.foot_z])
        
        # Knän via IK
        thigh_len = self._segment('thigh')
        shin_len = self._segment('shin')
        self.knee_left = self._ik_3d(self.hip_left, self.foot_left,
                                      thigh_len, shin_len,
                                      bend_dir='forward')
        self.knee_right = self._ik_3d(self.hip_right, self.foot_right,
                                       thigh_len, shin_len,
                                       bend_dir='forward')
    
    @staticmethod
    def _ik_3d(p1, p2, len1, len2, bend_dir='forward'):
        """
        Inverse kinematik i 3D: hitta mellanpunkten (knä/armbåge) mellan
        p1 (höft/axel) och p2 (fot/hand) givet längder len1 och len2.
        
        Vi gör IK i det plan som innehåller p1, p2 och en vertikal riktning,
        med bend_dir som väljer böjningsriktning i det planet.
        """
        p1 = np.asarray(p1, dtype=float)
        p2 = np.asarray(p2, dtype=float)
        d_vec = p2 - p1
        d = np.linalg.norm(d_vec)
        
        if d > len1 + len2:
            t = len1 / (len1 + len2)
            return p1 + t * d_vec
        if d < abs(len1 - len2) or d < 1e-6:
            return p1 + len1 * d_vec / max(d, 1e-6)
        
        # Mittpunkt på "kordan" och vinkelrät avstånd
        a = (len1**2 - len2**2 + d**2) / (2 * d)
        h_sq = max(0, len1**2 - a**2)
        h = np.sqrt(h_sq)
        d_hat = d_vec / d
        mid = p1 + a * d_hat
        
        # Vinkelrät riktning i ett plan som innehåller p1-p2 och 
        # en bend-riktning. Vi använder "vertikal upp" eller "framåt" som hint.
        if bend_dir == 'forward':
            hint = np.array([1, 0, 0])   # framåt
        elif bend_dir == 'down_back':
            hint = np.array([-0.5, -1, 0])
        else:
            hint = np.array([0, 1, 0])
        
        # Vinkelrät komponent av hint mot d_hat
        perp = hint - np.dot(hint, d_hat) * d_hat
        perp_norm = np.linalg.norm(perp)
        if perp_norm < 1e-6:
            # Hint parallell med d_hat — använd ett alternativt hint
            hint = np.array([0, 0, 1])
            perp = hint - np.dot(hint, d_hat) * d_hat
            perp_norm = np.linalg.norm(perp)
        perp = perp / perp_norm
        
        return mid + h * perp
    
    def render(self, canvas):
        """Rita föraren i 3D-canvas med fyllda volymer som syns från alla vyer."""
        body_fill = '#A1887F'         # ljus brun-grå för kropp/kläder
        body_dark = '#6D4C41'         # mörkare för skuggsidor
        limb_fill = '#8D6E63'         # för armar och ben
        head_fill = '#FFCCBC'         # hudfärg
        head_stroke = '#5D4037'
        opacity = 0.92
        limb_width = 6.0              # bredd på lemmar (cm)
        torso_depth = 18.0            # bålens djup i x-led
        
        # === BÅLEN som låda med djup i alla riktningar ===
        # Höft och axlar ges utsträckning i x-led för att skapa volym
        torso_half_d = torso_depth / 2
        
        # Höftens fyra hörn (kvadrat sett från ovan)
        hip_back_left = self.hip_left + np.array([-torso_half_d, 0, 0])
        hip_back_right = self.hip_right + np.array([-torso_half_d, 0, 0])
        hip_front_left = self.hip_left + np.array([+torso_half_d, 0, 0])
        hip_front_right = self.hip_right + np.array([+torso_half_d, 0, 0])
        
        # Axlarnas fyra hörn (axelmitten lutar framåt p.g.a. torso_angle, 
        # så axel-x är redan offset framåt jämfört med höft-x)
        sh_back_left = self.shoulder_left + np.array([-torso_half_d, 0, 0])
        sh_back_right = self.shoulder_right + np.array([-torso_half_d, 0, 0])
        sh_front_left = self.shoulder_left + np.array([+torso_half_d, 0, 0])
        sh_front_right = self.shoulder_right + np.array([+torso_half_d, 0, 0])
        
        # Sex sidor av bål-lådan
        # Framsida (axel→höft framifrån, +x)
        canvas.polygon3d([hip_front_left, hip_front_right,
                           sh_front_right, sh_front_left],
                          fill=body_fill, opacity=opacity)
        # Baksida (-x)
        canvas.polygon3d([hip_back_left, sh_back_left,
                           sh_back_right, hip_back_right],
                          fill=body_dark, opacity=opacity)
        # Vänster sida (-z)
        canvas.polygon3d([hip_back_left, hip_front_left,
                           sh_front_left, sh_back_left],
                          fill=body_fill, opacity=opacity)
        # Höger sida (+z)
        canvas.polygon3d([hip_back_right, sh_back_right,
                           sh_front_right, hip_front_right],
                          fill=body_fill, opacity=opacity)
        # Topp (axlarna)
        canvas.polygon3d([sh_back_left, sh_front_left,
                           sh_front_right, sh_back_right],
                          fill=body_dark, opacity=opacity)
        # Botten (höften)
        canvas.polygon3d([hip_back_left, hip_back_right,
                           hip_front_right, hip_front_left],
                          fill=body_dark, opacity=opacity)
        
        # === HUVUD ===
        canvas.circle3d(self.head_center, radius=8,
                         fill=head_fill, stroke=head_stroke,
                         stroke_width=0.6, opacity=opacity)
        # Hals
        canvas.line3d(self.shoulder_mid, self.head_center,
                       color=body_dark, width=3.5, opacity=opacity)
        
        # === LEMMAR som "kors" av två fyllda rektanglar (+-tvärsnitt) ===
        def render_limb(p1, p2, fill_color, width):
            """
            Rita en lem som två korsade rektanglar:
            - en med bredd i z-led (syns framifrån)
            - en med bredd i x-led (syns från sidan)
            Båda har samma längdaxel mellan p1 och p2.
            """
            d = p2 - p1
            d_norm = np.linalg.norm(d)
            if d_norm < 1e-6:
                return
            d_hat = d / d_norm
            half_w = width / 2
            
            # Bredd-riktning 1: z-axeln, projicerad ortogonalt mot d_hat
            z_axis = np.array([0, 0, 1])
            w_dir_z = z_axis - np.dot(z_axis, d_hat) * d_hat
            wn = np.linalg.norm(w_dir_z)
            if wn > 1e-6:
                w_dir_z = w_dir_z / wn
                # Rektangel 1: bredd i z
                corners_z = [
                    p1 - half_w * w_dir_z,
                    p1 + half_w * w_dir_z,
                    p2 + half_w * w_dir_z,
                    p2 - half_w * w_dir_z,
                ]
                canvas.polygon3d(corners_z, fill=fill_color, opacity=opacity)
            
            # Bredd-riktning 2: x-axeln, projicerad ortogonalt mot d_hat
            x_axis = np.array([1, 0, 0])
            w_dir_x = x_axis - np.dot(x_axis, d_hat) * d_hat
            wn = np.linalg.norm(w_dir_x)
            if wn > 1e-6:
                w_dir_x = w_dir_x / wn
                # Rektangel 2: bredd i x
                corners_x = [
                    p1 - half_w * w_dir_x,
                    p1 + half_w * w_dir_x,
                    p2 + half_w * w_dir_x,
                    p2 - half_w * w_dir_x,
                ]
                canvas.polygon3d(corners_x, fill=fill_color, opacity=opacity)
        
        # Armar
        for shoulder, elbow, hand in [
            (self.shoulder_left, self.elbow_left, self.hand_left),
            (self.shoulder_right, self.elbow_right, self.hand_right),
        ]:
            render_limb(shoulder, elbow, limb_fill, width=limb_width * 0.85)
            render_limb(elbow, hand, limb_fill, width=limb_width * 0.7)
            canvas.circle3d(elbow, 2.0, fill=body_dark,
                             stroke='white', stroke_width=0.3, opacity=opacity)
        
        # Ben
        for hip, knee, foot in [
            (self.hip_left, self.knee_left, self.foot_left),
            (self.hip_right, self.knee_right, self.foot_right),
        ]:
            render_limb(hip, knee, limb_fill, width=limb_width)
            render_limb(knee, foot, limb_fill, width=limb_width * 0.8)
            canvas.circle3d(knee, 2.2, fill=body_dark,
                             stroke='white', stroke_width=0.3, opacity=opacity)
        
        # Leder
        for p in [self.hip_left, self.hip_right, self.shoulder_left,
                  self.shoulder_right]:
            canvas.circle3d(p, 2.2, fill=body_dark,
                             stroke='white', stroke_width=0.3, opacity=opacity)
        
        # Händer och fötter som markörer
        for p in [self.hand_left, self.hand_right]:
            canvas.circle3d(p, 2.0, fill='#1565C0',
                             stroke='white', stroke_width=0.3, opacity=opacity)
        for p in [self.foot_left, self.foot_right]:
            canvas.circle3d(p, 2.5, fill='#1B5E20',
                             stroke='white', stroke_width=0.3, opacity=opacity)


# ============================================================
# Demo etapp 3
# ============================================================
def demo_etapp3():
    """Etapp 3: lägg till 3D-förare med utbredning i höft och axlar."""
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    track_width = 30
    z_left = -track_width / 2
    z_right = +track_width / 2
    
    theta_global = np.radians(60)
    
    # Skapa 3D-föraren
    rider3d = Rider3D(
        height=194,
        saddle_xy=(0, 113),
        handlebar_xy=(35, 110),
        pedal_center_xy=(0, 45),
        pedal_radius=17,
        foot_track_z=15,
        hand_track_z=20,
    )
    
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar etapp 3 vy: {view_name}")
        camera = Camera(view=view_name)
        
        # Extents
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        for inst, z_off in [
            (machine2d.front.left, z_left), (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left), (machine2d.rear.right, z_right),
        ]:
            for p in inst.foot_path(30):
                all_points.append(to_3d(p, z=z_off))
        # Förarens nyckelpunkter
        for p in [rider3d.head_top, rider3d.hip_left, rider3d.hip_right,
                  rider3d.shoulder_left, rider3d.shoulder_right,
                  rider3d.hand_left, rider3d.hand_right,
                  rider3d.foot_left, rider3d.foot_right]:
            all_points.append(p)
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        x_min, x_max = min(xs) - 15, max(xs) + 15
        y_min, y_max = min(ys) - 10, max(ys) + 10
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark
        if view_name == 'side':
            canvas.line3d(np.array([x_min, 0, 0]), np.array([x_max, 0, 0]),
                          color='#555', width=0.5)
        elif view_name == 'front':
            canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                          color='#555', width=0.5)
        elif view_name == 'iso':
            corners = [
                np.array([-80, 0, -30]), np.array([150, 0, -30]),
                np.array([150, 0, 30]),  np.array([-80, 0, 30]),
            ]
            for i in range(4):
                canvas.line3d(corners[i], corners[(i+1) % 4],
                              color='#999', width=0.3, opacity=0.5)
        
        # Ramen (z=0)
        nodes_3d = {name: to_3d(p, z=0) for name, p in machine2d.frame.nodes.items()}
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#5D4037', width=1.6, opacity=0.85)
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.3, fill='#3E2723',
                            stroke='white', stroke_width=0.4)
        
        # Vevaxlar
        for ax_pos in [machine2d.frame.A_rear, machine2d.frame.A_front]:
            canvas.line3d(np.array([ax_pos[0], ax_pos[1], z_left]),
                          np.array([ax_pos[0], ax_pos[1], z_right]),
                          color='#222', width=2.0, opacity=0.9)
        
        # Benen
        for inst, z_off in [
            (machine2d.front.left, z_left),
            (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left),
            (machine2d.rear.right, z_right),
        ]:
            render_leg_3d(canvas, inst, theta_global, z_off, opacity=0.85)
            render_foot_path_3d(canvas, inst, z_off,
                                 color='#1976D2', width=0.35, opacity=0.3)
        
        # Föraren
        rider3d.render(canvas)
        
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 3: maskinen med förare · vy = {view_name}</text>')
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="11" '
                        f'font-size="2.8" fill="#666" text-anchor="middle">'
                        f'spårvidd {track_width} cm · höft {Rider3D.HIP_WIDTH} cm · '
                        f'axlar {Rider3D.SHOULDER_WIDTH} cm</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e3_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


def render_handlebar_3d(canvas, H_pos, half_width=20, color='#222',
                          width=2.5, opacity=0.95):
    """
    Rita styret som en horisontell stång i z-led genom punkten H.
    
    Args:
        H_pos: H i 2D (x,y) eller 3D (z används inte, vi sätter z=0)
        half_width: halv styrbredd i cm (totalbredd = 2 × half_width)
    """
    if len(H_pos) == 2:
        h_center = np.array([H_pos[0], H_pos[1], 0])
    else:
        h_center = np.asarray(H_pos)
    
    h_left = h_center + np.array([0, 0, -half_width])
    h_right = h_center + np.array([0, 0, +half_width])
    
    canvas.line3d(h_left, h_right, color=color, width=width, opacity=opacity)
    
    # Handtag-bollar i ändarna
    canvas.circle3d(h_left, 1.8, fill='#000', stroke='white',
                     stroke_width=0.4, opacity=opacity)
    canvas.circle3d(h_right, 1.8, fill='#000', stroke='white',
                     stroke_width=0.4, opacity=opacity)
    # Centrumpunkt
    canvas.circle3d(h_center, 1.2, fill='#444', stroke='white',
                     stroke_width=0.3, opacity=opacity)


# ============================================================
# Demo etapp 4: rita maskinen med styre och uppdaterad ram
# ============================================================
def demo_etapp4():
    """
    Etapp 4: lägg till styret som tvärställd stång + använd nya ramen 
    med N-noden.
    """
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    track_width = 30
    z_left = -track_width / 2
    z_right = +track_width / 2
    handlebar_half_width = 20  # cm halv styrbredd
    
    theta_global = np.radians(60)
    
    rider3d = Rider3D(
        height=194,
        saddle_xy=(0, 113),
        handlebar_xy=(35, 110),
        pedal_center_xy=(0, 45),
        pedal_radius=17,
        foot_track_z=15,
        hand_track_z=handlebar_half_width,  # händer vid styrets ändar
    )
    
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar etapp 4 vy: {view_name}")
        camera = Camera(view=view_name)
        
        # Extents
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        for inst, z_off in [
            (machine2d.front.left, z_left), (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left), (machine2d.rear.right, z_right),
        ]:
            for p in inst.foot_path(30):
                all_points.append(to_3d(p, z=z_off))
        for p in [rider3d.head_top, rider3d.hip_left, rider3d.hip_right,
                  rider3d.shoulder_left, rider3d.shoulder_right,
                  rider3d.hand_left, rider3d.hand_right,
                  rider3d.foot_left, rider3d.foot_right]:
            all_points.append(p)
        # Styret
        H = machine2d.frame.H
        all_points.append(np.array([H[0], H[1], -handlebar_half_width]))
        all_points.append(np.array([H[0], H[1], +handlebar_half_width]))
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        x_min, x_max = min(xs) - 15, max(xs) + 15
        y_min, y_max = min(ys) - 10, max(ys) + 10
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark
        if view_name == 'side':
            canvas.line3d(np.array([x_min, 0, 0]), np.array([x_max, 0, 0]),
                          color='#555', width=0.5)
        elif view_name == 'front':
            canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                          color='#555', width=0.5)
        elif view_name == 'iso':
            corners = [
                np.array([-80, 0, -30]), np.array([150, 0, -30]),
                np.array([150, 0, 30]),  np.array([-80, 0, 30]),
            ]
            for i in range(4):
                canvas.line3d(corners[i], corners[(i+1) % 4],
                              color='#999', width=0.3, opacity=0.5)
        
        # Ramen (z=0) — nu med N-noden
        nodes_3d = {name: to_3d(p, z=0) for name, p in machine2d.frame.nodes.items()}
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#5D4037', width=1.6, opacity=0.85)
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.3, fill='#3E2723',
                            stroke='white', stroke_width=0.4)
            canvas.text3d(p, name, size=3.0, color='black', weight='bold',
                          dx=3, dy=-1.5)
        
        # Vevaxlar
        for ax_pos in [machine2d.frame.A_rear, machine2d.frame.A_front]:
            canvas.line3d(np.array([ax_pos[0], ax_pos[1], z_left]),
                          np.array([ax_pos[0], ax_pos[1], z_right]),
                          color='#222', width=2.0, opacity=0.9)
        
        # STYRET — horisontell stång genom H
        render_handlebar_3d(canvas, machine2d.frame.H, 
                             half_width=handlebar_half_width)
        
        # Benen
        for inst, z_off in [
            (machine2d.front.left, z_left),
            (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left),
            (machine2d.rear.right, z_right),
        ]:
            render_leg_3d(canvas, inst, theta_global, z_off, opacity=0.85)
            render_foot_path_3d(canvas, inst, z_off,
                                 color='#1976D2', width=0.35, opacity=0.3)
        
        # Föraren
        rider3d.render(canvas)
        
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 4: med styre + N-fästpunkt · vy = {view_name}</text>')
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="11" '
                        f'font-size="2.8" fill="#666" text-anchor="middle">'
                        f'spårvidd {track_width} cm · styrbredd {2*handlebar_half_width} cm · '
                        f'N upp {Frame.N_OFFSET_UP} cm över A_front</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e4_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


# ============================================================
# Driveline — vevaxlar, drev och kedjor i 3D
# ============================================================
class Driveline:
    """
    Modellerar drivlinan: pedalvev, bakvevaxel, framvevaxel med
    deras drev och kedjor.
    
    Konvention för z-positioner:
        ramens centerlinje vid z=0
        lagerhus från z=-2 till z=+2 genom ramen
        drev innanför vevarmen, vid z=±3
        vevarmens ankarpunkt vid z=±5
        pedal/vevtapp vid z=±15 (yttre ände)
    
    Pedalvev har drev på BÅDA sidor (driver båda vevaxlar).
    Bakvevaxel har drev bara på VÄNSTER sida (z=-3).
    Framvevaxel har drev bara på HÖGER sida (z=+3).
    """
    
    # Z-positioner (cm)
    LAGERHUS_HALF = 2.0      # lagerhuset från z=±2
    DREV_Z = 3.0             # drev sitter vid z=±3
    VEVARM_ANCHOR_Z = 5.0    # vevarmens fäste på axeln vid z=±5
    OUTER_Z = 15.0           # pedalens yttre ände / vevtapp vid z=±15
    
    # Storleksval (cm i full skala)
    PEDAL_DREV_R = 4.0       # pedalvevens drev
    VEV_DREV_R = 10.0        # vevaxlarnas drev (= utväxling 1:2.5)
    
    def __init__(self, P_pos, A_rear_pos, A_front_pos):
        """
        Args:
            P_pos: pedalvevens centrum (x, y) — 2D-position
            A_rear_pos: bakvevaxelns centrum (x, y)
            A_front_pos: framvevaxelns centrum (x, y)
        """
        self.P = np.asarray(P_pos, dtype=float)
        self.A_rear = np.asarray(A_rear_pos, dtype=float)
        self.A_front = np.asarray(A_front_pos, dtype=float)
    
    def axle_endpoints(self, center_xy):
        """Returnera axelns ändpunkter i 3D (genom centrum, från z=-15 till +15)."""
        cx, cy = center_xy[0], center_xy[1]
        return (np.array([cx, cy, -self.OUTER_Z]),
                np.array([cx, cy, +self.OUTER_Z]))
    
    def render(self, canvas, theta_global=0.0):
        """Rita drivlinan i 3D-canvas.
        
        Args:
            theta_global: aktuell vevvinkel (för att placera pedaler/vevarmar)
        """
        # === AXLAR (kompletta från z=-15 till +15) ===
        for center in [self.P, self.A_rear, self.A_front]:
            p_left, p_right = self.axle_endpoints(center)
            canvas.line3d(p_left, p_right, color='#222', width=1.8, opacity=0.9)
        
        # === LAGERHUS ===
        for center in [self.P, self.A_rear, self.A_front]:
            p_left = np.array([center[0], center[1], -self.LAGERHUS_HALF])
            p_right = np.array([center[0], center[1], +self.LAGERHUS_HALF])
            canvas.line3d(p_left, p_right, color='#444', width=4.0,
                          opacity=0.95)
        
        # === SVEP-DISKAR ===
        # Genomsynliga diskar som visar omfånget av pedalernas/vevtapparnas
        # cirkulära rörelse. Placeras vid z där pedalen/vevtappen rör sig.
        
        # Pedalvevens svep: pedalradie 17 cm (pedalvevarmens längd), vid z=±15
        self._render_sweep_disk(canvas, self.P, z=-self.OUTER_Z,
                                 radius=17.0, color='#FF9800', opacity=0.12,
                                 label='pedalsvep V')
        self._render_sweep_disk(canvas, self.P, z=+self.OUTER_Z,
                                 radius=17.0, color='#FF9800', opacity=0.12,
                                 label='pedalsvep H')
        
        # Vevaxlarnas svep: vevarmen AC = 15 cm, vid z=±15 (där benens vevtapp sitter)
        for center, label in [(self.A_rear, 'bak'), (self.A_front, 'fram')]:
            self._render_sweep_disk(canvas, center, z=-self.OUTER_Z,
                                     radius=15.0, color='#1976D2', opacity=0.10,
                                     label=f'vev_{label}_V')
            self._render_sweep_disk(canvas, center, z=+self.OUTER_Z,
                                     radius=15.0, color='#1976D2', opacity=0.10,
                                     label=f'vev_{label}_H')
        
        # === DREV ===
        self._render_drev(canvas, self.P, z=-self.DREV_Z, radius=self.PEDAL_DREV_R)
        self._render_drev(canvas, self.P, z=+self.DREV_Z, radius=self.PEDAL_DREV_R)
        self._render_drev(canvas, self.A_rear, z=-self.DREV_Z, radius=self.VEV_DREV_R)
        self._render_drev(canvas, self.A_front, z=+self.DREV_Z, radius=self.VEV_DREV_R)
        
        # === KEDJOR ===
        self._render_chain(canvas, self.P, -self.DREV_Z, self.PEDAL_DREV_R,
                           self.A_rear, self.VEV_DREV_R)
        self._render_chain(canvas, self.P, +self.DREV_Z, self.PEDAL_DREV_R,
                           self.A_front, self.VEV_DREV_R)
        
        # === PEDALVEVARMAR OCH PEDALER ===
        # Vevarmen ligger PLANT i xy-planet vid z=±VEVARM_ANCHOR_Z.
        # Pedaltappen sticker ut i z-led från vevarmens spets (z=±5 till z=±15).
        # Pedalen är en platta 6×2×10 cm som sitter centrerad på pedaltappen,
        # alltså från z=±5 till z=±15.
        # Föraren trampar mitt på pedalen (vid z=±10).
        
        # Pedalrotation: vid theta=0 är vänster pedal i topp (90°), höger i botten
        pedal_angle_left = -theta_global + np.pi / 2
        pedal_angle_right = pedal_angle_left + np.pi
        pedal_radius = 17.0
        
        cx, cy = self.P[0], self.P[1]
        
        for angle, z_sign in [
            (pedal_angle_left, -1),
            (pedal_angle_right, +1),
        ]:
            z_arm = z_sign * self.VEVARM_ANCHOR_Z   # ±5: vevarmens z-plan
            z_pedal_inner = z_arm                    # ±5: pedalens inre ände
            z_pedal_outer = z_sign * self.OUTER_Z    # ±15: pedalens yttre ände
            
            # Vevarmens fästpunkt på axeln (vid pedalvevens centrum)
            arm_anchor = np.array([cx, cy, z_arm])
            # Vevarmens spets (där pedaltappen sitter)
            arm_tip_xy = np.array([
                cx + pedal_radius * np.cos(angle),
                cy + pedal_radius * np.sin(angle),
            ])
            arm_tip = np.array([arm_tip_xy[0], arm_tip_xy[1], z_arm])
            
            # Vevarmen (i xy-planet vid z=z_arm)
            canvas.line3d(arm_anchor, arm_tip,
                          color='#37474F', width=2.5, opacity=0.95)
            
            # Pedaltappen (axel som sticker ut i z-led, från z=±5 till z=±15)
            pedal_tap_outer = np.array([arm_tip_xy[0], arm_tip_xy[1], z_pedal_outer])
            canvas.line3d(arm_tip, pedal_tap_outer,
                          color='#222', width=1.5, opacity=0.95)
            
            # Pedalen som platta 6×2×10 cm
            # Pedalens centrum är vid mitten av pedaltappen i z-led: 
            # (z_arm + z_pedal_outer) / 2 = z_sign * 10
            z_pedal_center = z_sign * 10
            
            # Pedalplattans halva utsträckning
            half_x = 3.0   # 6 cm bred i x-led
            half_y = 1.0   # 2 cm tjock i y-led
            half_z = 5.0   # 10 cm lång i z-led
            
            # Plattans 8 hörn
            corners = []
            for sx in [-1, +1]:
                for sy in [-1, +1]:
                    for sz in [-1, +1]:
                        corners.append(np.array([
                            arm_tip_xy[0] + sx * half_x,
                            arm_tip_xy[1] + sy * half_y,
                            z_pedal_center + sz * half_z,
                        ]))
            
            # Plattans 12 kanter (4 längs varje axel)
            # Vi indexerar hörnen så att de motsvarar (sx, sy, sz) bits 
            # där (sx,sy,sz) → index = (sx_bit)*4 + (sy_bit)*2 + (sz_bit)
            # hörn-ordning ovan: (-1,-1,-1)(-1,-1,+1)(-1,+1,-1)(-1,+1,+1)
            #                   (+1,-1,-1)(+1,-1,+1)(+1,+1,-1)(+1,+1,+1)
            # = index 0-7
            edges = [
                # Längs x-axeln (sy, sz fixa, sx varierar): 0-4, 1-5, 2-6, 3-7
                (0, 4), (1, 5), (2, 6), (3, 7),
                # Längs y-axeln: 0-2, 1-3, 4-6, 5-7
                (0, 2), (1, 3), (4, 6), (5, 7),
                # Längs z-axeln: 0-1, 2-3, 4-5, 6-7
                (0, 1), (2, 3), (4, 5), (6, 7),
            ]
            for i, j in edges:
                canvas.line3d(corners[i], corners[j],
                              color='#1B5E20', width=1.0, opacity=0.85)
            
            # Förarens fot landar mitt på pedalen i z-led: z_pedal_center
            # (Vi lagrar detta för att kunna synka föraren senare)
        
        # === BENVEVAXLARNAS VEVARMAR ===
        # Vid varje vevaxel sticker en vevarm ut till z=±15 där benet börjar.
        # Den är benets AC-länk (vevarmen från A till vevtapp C), 
        # roterar med vevvinkeln. Men eftersom benets kinematik redan ritar 
        # AC-länken (som diagonal i benets plan), behöver vi inte rita den igen.
        # Vi ritar bara den korta "tappen" från axelns z-position ut till 
        # benets plan, som markerar var vevarmen fäster i axeln.
        # 
        # I praktiken är vevarmen AC ett rakt rör som går från (A, z=0 på axeln) 
        # ut till (C, z=±15 i benets plan). Den ritas redan av render_leg_3d.
        pass
    
    def _render_sweep_disk(self, canvas, center_xy, z, radius, color, 
                            opacity=0.15, label=''):
        """
        Rita en genomsynlig disk som visar svepområdet för pedaler/vevtappar.
        Disken ligger i ett plan vinkelrätt mot z-axeln (alltså i xy-planet 
        vid given z) — vilket är fel mot benets plan men korrekt för svep 
        sett från sidan. 
        
        Faktum är att pedalens svep ligger i ett xy-plan vid z=±15 — så det 
        är ett xy-plan, inte ett yz-plan. Vevtappens svep är samma sak.
        """
        # Sample punkter på cirkeln
        n_pts = 48
        cx, cy = center_xy[0], center_xy[1]
        
        prev = None
        for i in range(n_pts + 1):
            t = 2 * np.pi * i / n_pts
            p = np.array([cx + radius * np.cos(t),
                          cy + radius * np.sin(t),
                          z])
            if prev is not None:
                canvas.line3d(prev, p, color=color,
                              width=0.6, opacity=opacity * 3)
            prev = p
        
        # Fyll med en streckad inre cirkel för "disk"-känsla
        # (vi kan inte göra solid fyllning i SVG-canvas på enkelt sätt — 
        # använd flera koncentriska cirklar med låg opacitet)
        for r_inner in np.linspace(radius * 0.85, radius * 0.15, 5):
            prev = None
            for i in range(n_pts + 1):
                t = 2 * np.pi * i / n_pts
                p = np.array([cx + r_inner * np.cos(t),
                              cy + r_inner * np.sin(t),
                              z])
                if prev is not None:
                    canvas.line3d(prev, p, color=color,
                                  width=0.3, opacity=opacity)
                prev = p
    
    def _render_drev(self, canvas, center_xy, z, radius):
        """Rita ett kedjedrev som en cirkel i z-planet."""
        # Rita drevet som en cirkel i xy-planet vid given z
        # I 3D blir det en cirkel; vi sample många punkter och drar linjer
        n_pts = 24
        cx, cy = center_xy[0], center_xy[1]
        
        # Yttre cirkel
        prev = None
        for i in range(n_pts + 1):
            t = 2 * np.pi * i / n_pts
            p = np.array([cx + radius * np.cos(t),
                          cy + radius * np.sin(t),
                          z])
            if prev is not None:
                canvas.line3d(prev, p, color='#1565C0',
                              width=1.0, opacity=0.85)
            prev = p
        
        # Mittpunkt
        canvas.circle3d(np.array([cx, cy, z]), 1.0, fill='#0D47A1',
                        stroke='white', stroke_width=0.4)
    
    def _render_chain(self, canvas, p1_xy, z, r1, p2_xy, r2,
                       color='#444', n_dots=80):
        """
        Rita en kedja mellan två drev som tät punktrad.
        
        Kedjan består av två raka segment som tangerar drevens cirklar,
        plus två bågar runt drevens halva.
        """
        # Centra i 3D vid kedjans z-plan
        c1 = np.array([p1_xy[0], p1_xy[1], z])
        c2 = np.array([p2_xy[0], p2_xy[1], z])
        
        # Riktning mellan centra
        d_vec = c2 - c1
        d = np.linalg.norm(d_vec[:2])  # bara xy-avstånd
        if d < 1e-6:
            return
        d_hat = d_vec / np.linalg.norm(d_vec)
        # Perpendikulär i xy-planet (för att hitta tangentpunkter)
        perp = np.array([-d_hat[1], d_hat[0], 0])
        
        # Eftersom dreven har olika radier blir tangentlinjerna inte parallella
        # med centrumlinjen. Vi använder en förenkling: anta dreven är ungefär 
        # lika stora (för visualisering) och rita raka tangenter.
        # För precist resultat: använd extern tangent-formel
        # Yttre tangentpunkter: lutning theta så att (r1 - r2) / d = sin(theta)
        if abs(r1 - r2) < d:
            sin_th = (r2 - r1) / d
            cos_th = np.sqrt(max(0, 1 - sin_th**2))
        else:
            sin_th = 0
            cos_th = 1
        
        # Övre tangenten
        # Tangentpunkter
        t1_upper = c1 + r1 * (sin_th * d_hat + cos_th * perp)
        t2_upper = c2 + r2 * (sin_th * d_hat + cos_th * perp)
        # Undre tangenten
        t1_lower = c1 + r1 * (sin_th * d_hat - cos_th * perp)
        t2_lower = c2 + r2 * (sin_th * d_hat - cos_th * perp)
        
        # Bygg kedjepunkter
        # 1) Övre tangent c1→c2
        # 2) Båge runt c2 från övre tangentpunkt till nedre tangentpunkt
        # 3) Nedre tangent c2→c1
        # 4) Båge runt c1 från nedre till övre tangentpunkt
        
        def dots_on_segment(p_start, p_end, n):
            return [p_start + (p_end - p_start) * (i / n) for i in range(n)]
        
        def dots_on_arc(center, r, angle_start, angle_end, n, z_val):
            # Wrappa angle_end > angle_start
            while angle_end < angle_start:
                angle_end += 2 * np.pi
            pts = []
            for i in range(n):
                a = angle_start + (angle_end - angle_start) * (i / n)
                pts.append(np.array([center[0] + r * np.cos(a),
                                     center[1] + r * np.sin(a),
                                     z_val]))
            return pts
        
        # Beräkna vinklar för bågarna
        ang_t1_upper = np.arctan2(t1_upper[1] - c1[1], t1_upper[0] - c1[0])
        ang_t1_lower = np.arctan2(t1_lower[1] - c1[1], t1_lower[0] - c1[0])
        ang_t2_upper = np.arctan2(t2_upper[1] - c2[1], t2_upper[0] - c2[0])
        ang_t2_lower = np.arctan2(t2_lower[1] - c2[1], t2_lower[0] - c2[0])
        
        # Bygg alla kedjepunkter i ordning
        pts = []
        # Övre tangent (c1→c2)
        pts.extend(dots_on_segment(t1_upper, t2_upper, n_dots // 4))
        # Båge runt c2 (övre till nedre, vinkel växer eller minskar?)
        pts.extend(dots_on_arc(c2, r2, ang_t2_upper, ang_t2_lower,
                                n_dots // 4, z))
        # Nedre tangent (c2→c1)
        pts.extend(dots_on_segment(t2_lower, t1_lower, n_dots // 4))
        # Båge runt c1 (nedre till övre)
        pts.extend(dots_on_arc(c1, r1, ang_t1_lower, ang_t1_upper,
                                n_dots // 4, z))
        
        # Rita som täta punkter (små cirklar)
        for p in pts:
            canvas.circle3d(p, 0.4, fill=color, stroke=None,
                            stroke_width=0, opacity=0.9)


# ============================================================
# Demo etapp 5: drivlinan
# ============================================================
def demo_etapp5():
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    track_width = 30
    z_left = -track_width / 2
    z_right = +track_width / 2
    handlebar_half_width = 20
    
    theta_global = np.radians(60)
    
    rider3d = Rider3D(
        height=194,
        saddle_xy=(0, 113),
        handlebar_xy=(35, 110),
        pedal_center_xy=(0, 45),
        pedal_radius=17,
        theta_global=theta_global,   # synka med driveline
        foot_track_z=10,              # mitten av pedalplattan
        hand_track_z=handlebar_half_width,
    )
    
    driveline = Driveline(
        P_pos=machine2d.frame.P,
        A_rear_pos=machine2d.frame.A_rear,
        A_front_pos=machine2d.frame.A_front,
    )
    
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar etapp 5 vy: {view_name}")
        camera = Camera(view=view_name)
        
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        for inst, z_off in [
            (machine2d.front.left, z_left), (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left), (machine2d.rear.right, z_right),
        ]:
            for p in inst.foot_path(30):
                all_points.append(to_3d(p, z=z_off))
        for p in [rider3d.head_top, rider3d.hip_left, rider3d.hip_right,
                  rider3d.shoulder_left, rider3d.shoulder_right,
                  rider3d.hand_left, rider3d.hand_right,
                  rider3d.foot_left, rider3d.foot_right]:
            all_points.append(p)
        # Drivlinans extents
        for c in [machine2d.frame.P, machine2d.frame.A_rear, machine2d.frame.A_front]:
            all_points.append(np.array([c[0], c[1], -Driveline.OUTER_Z]))
            all_points.append(np.array([c[0], c[1], +Driveline.OUTER_Z]))
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        x_min, x_max = min(xs) - 15, max(xs) + 15
        y_min, y_max = min(ys) - 10, max(ys) + 10
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark
        if view_name == 'side':
            canvas.line3d(np.array([x_min, 0, 0]), np.array([x_max, 0, 0]),
                          color='#555', width=0.5)
        elif view_name == 'front':
            canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                          color='#555', width=0.5)
        elif view_name == 'iso':
            corners = [
                np.array([-80, 0, -30]), np.array([150, 0, -30]),
                np.array([150, 0, 30]),  np.array([-80, 0, 30]),
            ]
            for i in range(4):
                canvas.line3d(corners[i], corners[(i+1) % 4],
                              color='#999', width=0.3, opacity=0.5)
        
        # Ramen (z=0)
        nodes_3d = {name: to_3d(p, z=0) for name, p in machine2d.frame.nodes.items()}
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#5D4037', width=1.6, opacity=0.85)
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.3, fill='#3E2723',
                            stroke='white', stroke_width=0.4)
        
        # DRIVLINAN
        driveline.render(canvas, theta_global=theta_global)
        
        # Styret
        render_handlebar_3d(canvas, machine2d.frame.H,
                             half_width=handlebar_half_width)
        
        # Benen (utan att duplicera vevaxlarna — drivlinan har redan ritat dem)
        for inst, z_off in [
            (machine2d.front.left, z_left),
            (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left),
            (machine2d.rear.right, z_right),
        ]:
            render_leg_3d(canvas, inst, theta_global, z_off, opacity=0.85)
            render_foot_path_3d(canvas, inst, z_off,
                                 color='#1976D2', width=0.35, opacity=0.3)
        
        # Föraren
        rider3d.render(canvas)
        
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 5: drivlina med kedjor · vy = {view_name}</text>')
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="11" '
                        f'font-size="2.8" fill="#666" text-anchor="middle">'
                        f'pedaldrev R={Driveline.PEDAL_DREV_R}cm · '
                        f'vevdrev R={Driveline.VEV_DREV_R}cm · '
                        f'utväxling 1:{Driveline.VEV_DREV_R/Driveline.PEDAL_DREV_R:.1f}</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e5_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


# ============================================================
# Saddle — limpformad sadel som sträcker sig mellan A_rear och A_front
# ============================================================
class Saddle:
    """
    Limpformad sadel — BREDARE bakåt (där föraren sitter), SMALARE framåt.
    
    Ovansidan har lätt konkavitet vid sittpunkten (x=0) för komfort.
    """
    
    def __init__(self, x_rear, x_front, top_y, thickness=7,
                 width_rear=12, width_front=8, concavity=1.5):
        self.x_rear = x_rear
        self.x_front = x_front
        self.top_y = top_y
        self.thickness = thickness
        self.width_rear = width_rear
        self.width_front = width_front
        self.concavity = concavity
    
    def width_at(self, x):
        t = (x - self.x_rear) / (self.x_front - self.x_rear)
        return self.width_rear + t * (self.width_front - self.width_rear)
    
    def half_w_at(self, x):
        return self.width_at(x) / 2
    
    def top_curve(self, x):
        # Konkavitet centrerad runt x=0 (där föraren sitter)
        sigma = 12
        dip = self.concavity * np.exp(-(x ** 2) / (2 * sigma ** 2))
        return self.top_y - dip
    
    def render(self, canvas):
        # Färger för olika sidor av sadeln (mörkare under, ljusare topp)
        color_top = '#8D6E63'      # ljust läder ovansida
        color_bottom = '#3E2723'   # mörk underside
        color_side = '#5D4037'     # medium på sidor
        color_end = '#6D4C41'      # på ändar
        opacity = 0.95
        
        n = 20
        xs = np.linspace(self.x_rear, self.x_front, n)
        
        # Punkter
        top_left  = [np.array([x, self.top_curve(x), -self.half_w_at(x)]) for x in xs]
        top_right = [np.array([x, self.top_curve(x), +self.half_w_at(x)]) for x in xs]
        bot_left  = [np.array([x, self.top_curve(x) - self.thickness, -self.half_w_at(x)]) for x in xs]
        bot_right = [np.array([x, self.top_curve(x) - self.thickness, +self.half_w_at(x)]) for x in xs]
        
        # === OVANSIDA (rad av små rektanglar för att följa konkaviteten) ===
        for i in range(len(xs) - 1):
            quad = [top_left[i], top_left[i+1], top_right[i+1], top_right[i]]
            canvas.polygon3d(quad, fill=color_top, opacity=opacity)
        
        # === UNDERSIDA ===
        for i in range(len(xs) - 1):
            quad = [bot_left[i], bot_right[i], bot_right[i+1], bot_left[i+1]]
            canvas.polygon3d(quad, fill=color_bottom, opacity=opacity)
        
        # === VÄNSTER SIDA ===
        for i in range(len(xs) - 1):
            quad = [top_left[i], bot_left[i], bot_left[i+1], top_left[i+1]]
            canvas.polygon3d(quad, fill=color_side, opacity=opacity)
        
        # === HÖGER SIDA ===
        for i in range(len(xs) - 1):
            quad = [top_right[i], top_right[i+1], bot_right[i+1], bot_right[i]]
            canvas.polygon3d(quad, fill=color_side, opacity=opacity)
        
        # === BAKÄNDA ===
        quad = [top_left[0], top_right[0], bot_right[0], bot_left[0]]
        canvas.polygon3d(quad, fill=color_end, opacity=opacity)
        
        # === FRAMÄNDA ===
        quad = [top_left[-1], bot_left[-1], bot_right[-1], top_right[-1]]
        canvas.polygon3d(quad, fill=color_end, opacity=opacity)


# ============================================================
# Demo etapp 6: lägg till sadeln
# ============================================================
def demo_etapp6():
    machine2d = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    
    track_width = 30
    z_left = -track_width / 2
    z_right = +track_width / 2
    handlebar_half_width = 20
    
    theta_global = np.radians(60)
    
    rider3d = Rider3D(
        height=194,
        saddle_xy=(0, 113),
        handlebar_xy=(35, 110),
        pedal_center_xy=(0, 45),
        pedal_radius=17,
        theta_global=theta_global,
        foot_track_z=10,
        hand_track_z=handlebar_half_width,
    )
    
    driveline = Driveline(
        P_pos=machine2d.frame.P,
        A_rear_pos=machine2d.frame.A_rear,
        A_front_pos=machine2d.frame.A_front,
    )
    
    saddle = Saddle(
        x_rear=-15,                  # 15 cm bakom föraren
        x_front=30,                  # 30 cm framför föraren
        top_y=113,
        thickness=7,
        width_rear=12,               # bredare där föraren sitter
        width_front=8,               # smalare framåt
        concavity=1.5,
    )
    
    views = ['side', 'front', 'top', 'iso']
    
    for view_name in views:
        print(f"Renderar etapp 6 vy: {view_name}")
        camera = Camera(view=view_name)
        
        all_points = []
        for name, p in machine2d.frame.nodes.items():
            all_points.append(to_3d(p, z=0))
        for inst, z_off in [
            (machine2d.front.left, z_left), (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left), (machine2d.rear.right, z_right),
        ]:
            for p in inst.foot_path(30):
                all_points.append(to_3d(p, z=z_off))
        for p in [rider3d.head_top, rider3d.hip_left, rider3d.hip_right,
                  rider3d.shoulder_left, rider3d.shoulder_right,
                  rider3d.hand_left, rider3d.hand_right,
                  rider3d.foot_left, rider3d.foot_right]:
            all_points.append(p)
        for c in [machine2d.frame.P, machine2d.frame.A_rear, machine2d.frame.A_front]:
            all_points.append(np.array([c[0], c[1], -Driveline.OUTER_Z]))
            all_points.append(np.array([c[0], c[1], +Driveline.OUTER_Z]))
        # Sadelns hörn
        for x in [saddle.x_rear, saddle.x_front]:
            for z in [-saddle.half_w_at(x), +saddle.half_w_at(x)]:
                all_points.append(np.array([x, saddle.top_y, z]))
                all_points.append(np.array([x, saddle.top_y - saddle.thickness, z]))
        
        proj = [camera.project(p) for p in all_points]
        xs = [s[0] for s in proj]
        ys = [s[1] for s in proj]
        x_min, x_max = min(xs) - 15, max(xs) + 15
        y_min, y_max = min(ys) - 10, max(ys) + 10
        
        canvas = Canvas3D(camera, x_min, x_max, y_min, y_max, pad=10)
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        # Mark
        if view_name == 'side':
            canvas.line3d(np.array([x_min, 0, 0]), np.array([x_max, 0, 0]),
                          color='#555', width=0.5)
        elif view_name == 'front':
            canvas.line3d(np.array([0, 0, -50]), np.array([0, 0, 50]),
                          color='#555', width=0.5)
        elif view_name == 'iso':
            corners = [
                np.array([-80, 0, -30]), np.array([150, 0, -30]),
                np.array([150, 0, 30]),  np.array([-80, 0, 30]),
            ]
            for i in range(4):
                canvas.line3d(corners[i], corners[(i+1) % 4],
                              color='#999', width=0.3, opacity=0.5)
        
        # Ramen
        nodes_3d = {name: to_3d(p, z=0) for name, p in machine2d.frame.nodes.items()}
        for n1, n2, _ in machine2d.frame.links:
            canvas.line3d(nodes_3d[n1], nodes_3d[n2],
                          color='#5D4037', width=1.6, opacity=0.85)
        for name, p in nodes_3d.items():
            canvas.circle3d(p, radius=1.3, fill='#3E2723',
                            stroke='white', stroke_width=0.4)
        
        # Drivlinan
        driveline.render(canvas, theta_global=theta_global)
        
        # SADELN
        saddle.render(canvas)
        
        # Styret
        render_handlebar_3d(canvas, machine2d.frame.H,
                             half_width=handlebar_half_width)
        
        # Benen
        for inst, z_off in [
            (machine2d.front.left, z_left),
            (machine2d.front.right, z_right),
            (machine2d.rear.left, z_left),
            (machine2d.rear.right, z_right),
        ]:
            render_leg_3d(canvas, inst, theta_global, z_off, opacity=0.85)
            render_foot_path_3d(canvas, inst, z_off,
                                 color='#1976D2', width=0.35, opacity=0.3)
        
        # Föraren
        rider3d.render(canvas)
        
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="7" '
                        f'font-size="4.5" fill="#222" text-anchor="middle" '
                        f'font-weight="bold">Etapp 6: med sadel · vy = {view_name}</text>')
        canvas.add_raw(f'<text x="{canvas.width/2:.1f}" y="11" '
                        f'font-size="2.8" fill="#666" text-anchor="middle">'
                        f'sadel {saddle.x_front - saddle.x_rear:.0f} cm lång '
                        f'(från x={saddle.x_rear} till x={saddle.x_front}), '
                        f'bredd {saddle.width_rear}→{saddle.width_front} cm</text>')
        
        fname = f'/mnt/user-data/outputs/m3d_e6_{view_name}.svg'
        canvas.save(fname)
        print(f"  → {fname}")


if __name__ == '__main__':
    demo_etapp6()
