"""
Jansen-baserad fyrbent maskin — modulär design med inbyggd SVG-rendering.

Arkitektur:
    Canvas       — samlar SVG-element och hanterar koordinattransformation
    Leg          — Jansens ben i lokala koord
    LegInstance  — ben placerat i världen (position, orientering, fas)
    LegPair      — två LegInstance som delar vevaxel (spegelpar)
    Machine      — hela maskinen, kan rita sig själv

Konventioner:
    Lokala benkoord: x växer mot B, y växer nedåt
    Globala koord:   x växer framåt (färdriktning), y växer uppåt (höjd)
    Origo: en punkt på marken under främre vevaxeln
"""

import numpy as np
from typing import Optional, List


# ============================================================
# Jansens "heliga tal" (cm)
# ============================================================
AC = 15.0
CD = 50.0; BD = 41.5; DE = 55.8; BE = 40.1
CF = 61.9; BF = 39.3
EG = 39.4; FG = 36.7
FH = 49.0; GH = 65.7

A_LOCAL = np.array([0.0, 0.0])
B_LOCAL = np.array([+38.0, 7.8])

SIGNS = (-1, -1, +1, -1, +1)


def _circle_intersect(c1, r1, c2, r2, sign):
    c1 = np.asarray(c1, dtype=float)
    c2 = np.asarray(c2, dtype=float)
    diff = c2 - c1
    dist = np.linalg.norm(diff)
    if dist > r1 + r2 + 1e-9 or dist < abs(r1 - r2) - 1e-9:
        return None
    aa = (r1**2 - r2**2 + dist**2) / (2 * dist)
    hh = np.sqrt(max(0.0, r1**2 - aa**2))
    mid = c1 + (aa / dist) * diff
    perp = np.array([-diff[1], diff[0]]) / dist
    return mid + sign * hh * perp


# ============================================================
# Canvas — samlar SVG-element och hanterar y-flipp
# ============================================================
class Canvas:
    """Samlar SVG-element. Världens y-uppåt -> SVG:s y-nedåt."""
    
    # Stil-defaultvärden som kan överrides per element
    DEFAULT_STYLES = {
        'frame': {'color': '#444', 'width': 1.5, 'opacity': 1.0},
        'frame_node': {'fill': '#222', 'radius': 1.6, 'opacity': 1.0},
        'leg_link': {'width': 1.2, 'opacity': 1.0},  # färg per länk
        'leg_joint': {'fill': '#222', 'radius': 1.0, 'opacity': 1.0},
        'fixed_joint': {'fill': '#000', 'radius': 1.4, 'opacity': 1.0},
        'crank_arm': {'color': '#1565C0', 'width': 1.4, 'opacity': 1.0},
        'crank_disk': {'fill': '#E3F2FD', 'stroke': '#90CAF9', 'opacity': 0.5},
        'foot_path': {'color': '#1976D2', 'width': 0.4, 'opacity': 0.35},
        'ground': {'color': '#555', 'width': 0.5, 'opacity': 1.0},
        'AB_dashed': {'color': '#888', 'width': 0.3, 'opacity': 1.0},
    }
    
    def __init__(self, x_min, x_max, y_min, y_max, pad=10):
        self.x_min = x_min - pad
        self.x_max = x_max + pad
        self.y_min = y_min - pad
        self.y_max = y_max + pad
        self.width = self.x_max - self.x_min
        self.height = self.y_max - self.y_min
        self.elements = []
    
    def w(self, p):
        """Världskoord -> SVG-koord."""
        return (p[0] - self.x_min, self.y_max - p[1])
    
    def add(self, s):
        self.elements.append(s)
    
    def line(self, p1, p2, color='#333', width=0.5, dasharray=None, opacity=1.0):
        s1, s2 = self.w(p1), self.w(p2)
        attrs = (f'x1="{s1[0]:.2f}" y1="{s1[1]:.2f}" '
                 f'x2="{s2[0]:.2f}" y2="{s2[1]:.2f}" '
                 f'stroke="{color}" stroke-width="{width}"')
        if dasharray: attrs += f' stroke-dasharray="{dasharray}"'
        if opacity != 1.0: attrs += f' opacity="{opacity}"'
        self.add(f'<line {attrs}/>')
    
    def circle(self, p, r, fill='none', stroke='#333', stroke_width=0.4,
               dasharray=None, opacity=1.0):
        sp = self.w(p)
        attrs = (f'cx="{sp[0]:.2f}" cy="{sp[1]:.2f}" r="{r}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"')
        if dasharray: attrs += f' stroke-dasharray="{dasharray}"'
        if opacity != 1.0: attrs += f' opacity="{opacity}"'
        self.add(f'<circle {attrs}/>')
    
    def text(self, p, content, size=3.0, color='#222', anchor='start',
             weight='normal', dx=0, dy=0):
        sp = self.w(p)
        attrs = (f'x="{sp[0]+dx:.2f}" y="{sp[1]+dy:.2f}" '
                 f'font-size="{size}" fill="{color}" '
                 f'text-anchor="{anchor}" font-weight="{weight}" '
                 f'paint-order="stroke" stroke="white" stroke-width="0.7"')
        self.add(f'<text {attrs}>{content}</text>')
    
    def path(self, points, color='#333', width=0.5, opacity=1.0, closed=True):
        if len(points) == 0: return
        pts = []
        for i, p in enumerate(points):
            sp = self.w(p)
            pts.append(f"{'M' if i == 0 else 'L'} {sp[0]:.2f} {sp[1]:.2f}")
        if closed: pts.append("Z")
        attrs = (f'd="{" ".join(pts)}" fill="none" '
                 f'stroke="{color}" stroke-width="{width}" opacity="{opacity}"')
        self.add(f'<path {attrs}/>')
    
    def grid(self, spacing=10, color='#e8e8e8'):
        x = int(np.floor(self.x_min / spacing) * spacing)
        while x < self.x_max:
            sx = x - self.x_min
            self.add(f'<line x1="{sx:.1f}" y1="0" x2="{sx:.1f}" '
                     f'y2="{self.height:.1f}" stroke="{color}" stroke-width="0.2"/>')
            x += spacing
        y = int(np.floor(self.y_min / spacing) * spacing)
        while y < self.y_max:
            sy = self.y_max - y
            self.add(f'<line x1="0" y1="{sy:.1f}" x2="{self.width:.1f}" '
                     f'y2="{sy:.1f}" stroke="{color}" stroke-width="0.2"/>')
            y += spacing
    
    def to_svg(self, width_px=1000):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {self.width:.1f} {self.height:.1f}" '
                f'width="{width_px}" '
                f'font-family="Helvetica, Arial, sans-serif">\n'
                f'<rect width="{self.width:.1f}" height="{self.height:.1f}" '
                f'fill="#fafafa"/>\n'
                + '\n'.join(self.elements) + '\n</svg>')
    
    def save(self, filename, width_px=1000):
        with open(filename, 'w') as f:
            f.write(self.to_svg(width_px))


# ============================================================
# Leg
# ============================================================
class Leg:
    """
    Jansens ben med fasta länklängder.
    
    Länklängderna kan justeras individuellt genom `link_adjustments`-parametern,
    vilket är användbart för att simulera teleskopiska länkar.
    
    Args:
        signs: branch-konfiguration (default Jansens klassiska)
        link_adjustments: dict {länknamn: offset_cm}, t.ex. {'BD': +2.0}
                          ger ett ben där BD är 2 cm längre än standard.
                          Länknamn kan vara 'AC', 'CD', 'BD', 'DE', 'BE',
                          'CF', 'BF', 'EG', 'FG', 'FH', 'GH', 'ABx', 'ABy'.
                          ('ABx' och 'ABy' justerar B-leden i lokal x/y.)
    """
    
    BASE_LENGTHS = {
        'AC': AC, 'CD': CD, 'BD': BD, 'DE': DE, 'BE': BE,
        'CF': CF, 'BF': BF, 'EG': EG, 'FG': FG, 'FH': FH, 'GH': GH,
    }
    
    LINK_COLORS = {
        ('C', 'D'): '#2E7D32', ('B', 'D'): '#C62828',
        ('D', 'E'): '#E57373', ('B', 'E'): '#C62828',
        ('C', 'F'): '#EF6C00', ('B', 'F'): '#9E9D24',
        ('E', 'G'): '#7B1FA2', ('F', 'G'): '#0288D1',
        ('F', 'H'): '#1565C0', ('G', 'H'): '#1565C0',
    }
    
    def __init__(self, signs=SIGNS, link_adjustments=None):
        self.signs = signs
        self.link_adjustments = link_adjustments or {}
        
        # Aktuella länklängder (bas + justering)
        adj = self.link_adjustments
        self.AC = AC + adj.get('AC', 0)
        self.CD = CD + adj.get('CD', 0)
        self.BD = BD + adj.get('BD', 0)
        self.DE = DE + adj.get('DE', 0)
        self.BE = BE + adj.get('BE', 0)
        self.CF = CF + adj.get('CF', 0)
        self.BF = BF + adj.get('BF', 0)
        self.EG = EG + adj.get('EG', 0)
        self.FG = FG + adj.get('FG', 0)
        self.FH = FH + adj.get('FH', 0)
        self.GH = GH + adj.get('GH', 0)
        
        # B-leden kan också flyttas
        self.B = np.array([
            B_LOCAL[0] + adj.get('ABx', 0),
            B_LOCAL[1] + adj.get('ABy', 0),
        ])
    
    @property
    def LINKS(self):
        return [
            ('A', 'C', self.AC),
            ('C', 'D', self.CD), ('B', 'D', self.BD),
            ('D', 'E', self.DE), ('B', 'E', self.BE),
            ('C', 'F', self.CF), ('B', 'F', self.BF),
            ('E', 'G', self.EG), ('F', 'G', self.FG),
            ('F', 'H', self.FH), ('G', 'H', self.GH),
        ]
    
    def pose(self, theta):
        s_D, s_E, s_F, s_G, s_H = self.signs
        C = A_LOCAL + self.AC * np.array([np.cos(theta), -np.sin(theta)])
        D = _circle_intersect(C, self.CD, self.B, self.BD, s_D)
        if D is None: return None
        E = _circle_intersect(D, self.DE, self.B, self.BE, s_E)
        if E is None: return None
        F = _circle_intersect(C, self.CF, self.B, self.BF, s_F)
        if F is None: return None
        G = _circle_intersect(E, self.EG, F, self.FG, s_G)
        if G is None: return None
        H = _circle_intersect(F, self.FH, G, self.GH, s_H)
        if H is None: return None
        return {'A': A_LOCAL.copy(), 'B': self.B.copy(),
                'C': C, 'D': D, 'E': E, 'F': F, 'G': G, 'H': H}
    
    def foot_path(self, n_points=360):
        """Beräkna fotbanan i lokala koord."""
        thetas = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        path = []
        for t in thetas:
            p = self.pose(t)
            if p is None:
                return None  # Geometrin är ogiltig vid denna konfiguration
            path.append(p['H'])
        return np.array(path)
    
    def metrics(self):
        """Beräkna nyckelparametrar för fotbanan."""
        path = self.foot_path(360)
        if path is None:
            return None
        return {
            'step_length': float(path[:,0].max() - path[:,0].min()),
            'foot_lift': float(path[:,1].max() - path[:,1].min()),
            'foot_path': path,
        }


# ============================================================
# LegInstance
# ============================================================
class LegInstance:
    def __init__(self, leg: Leg, A_world, yaw_deg=0.0, phase_deg=0.0, 
                 mirror_x=False, reverse=False, label=''):
        """
        Args:
            leg: Leg-objekt
            A_world: vevcentrums världsposition
            yaw_deg: 0 = lokal x framåt, 180 = lokal x bakåt
            phase_deg: fasoffset
            mirror_x: spegla benets kinematik i x-axeln
            reverse: om True, vrid vevaxeln åt motsatt håll. Motsvarar att
                     vevaxeln drivs av en kedja som ger motsatt rotation
                     jämfört med referenskonventionen.
            label: namn för identifiering
        """
        self.leg = leg
        self.A_world = np.asarray(A_world, dtype=float)
        self.yaw_rad = np.radians(yaw_deg)
        self.phase_rad = np.radians(phase_deg)
        self.mirror_x = mirror_x
        self.reverse = reverse
        self.label = label
    
    def _local_to_world(self, p_local):
        x_l, y_l = p_local[0], p_local[1]
        if self.mirror_x:
            x_l = -x_l
        x_oriented = np.cos(self.yaw_rad) * x_l
        y_oriented = -y_l
        return self.A_world + np.array([x_oriented, y_oriented])
    
    def pose(self, theta_global):
        # Vid reverse: vevaxeln roterar baklänges
        theta_for_leg = -theta_global if self.reverse else theta_global
        local = self.leg.pose(theta_for_leg + self.phase_rad)
        if local is None: return None
        return {name: self._local_to_world(p) for name, p in local.items()}
    
    def foot_path(self, n_points=360):
        thetas = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        return np.array([self.pose(t)['H'] for t in thetas])
    
    def render(self, canvas, theta_global, show_path=True,
               show_crank_disk=True, show_labels=False, opacity=1.0):
        pose = self.pose(theta_global)
        if pose is None: return
        
        if show_path:
            path = self.foot_path(360)
            canvas.path(path, color='#1976D2', width=0.4, opacity=0.35)
        
        if show_crank_disk:
            canvas.circle(pose['A'], AC, fill='#E3F2FD', stroke='#90CAF9',
                          stroke_width=0.3, dasharray='2,1.5', opacity=0.5)
        
        canvas.line(pose['A'], pose['B'], color='#888', width=0.3, 
                    dasharray='3,2', opacity=opacity)
        canvas.line(pose['A'], pose['C'], color='#1565C0', width=1.4,
                    opacity=opacity)
        
        for p1, p2, _ in self.leg.LINKS:
            if p1 == 'A' and p2 == 'C': continue
            color = self.leg.LINK_COLORS.get((p1, p2), '#666')
            canvas.line(pose[p1], pose[p2], color=color, width=1.2, opacity=opacity)
        
        for name, p in pose.items():
            is_fixed = name in ('A', 'B')
            r = 1.4 if is_fixed else 1.0
            fill = '#000' if is_fixed else '#222'
            canvas.circle(p, r, fill=fill, stroke='white', stroke_width=0.3,
                          opacity=opacity)
            if show_labels:
                lbl = f'{name}{self.label}' if self.label else name
                canvas.text(p, lbl, size=3.5, color='black', weight='bold',
                            dx=2, dy=-1.5)


# ============================================================
# LegPair — två ben på samma vevaxel
# ============================================================
class LegPair:
    """Två ben på samma vevaxel, 180° fasförskjutna.
    
    'left' och 'right' representerar vänster och höger sida av maskinen.
    De kan ha olika Leg-objekt (med olika link_adjustments) för differentiell
    styrning.
    """
    
    def __init__(self, leg: Leg, A_world, yaw_deg=0.0, phase_deg=0.0,
                 mirror_x=False, reverse=False, label='', leg_right=None):
        """
        Args:
            leg: Leg-objekt för vänster ben
            leg_right: Leg-objekt för höger ben. Om None används 'leg' för båda.
        """
        self.A_world = np.asarray(A_world, dtype=float)
        self.yaw_deg = yaw_deg
        leg_for_right = leg_right if leg_right is not None else leg
        self.left = LegInstance(leg, A_world, yaw_deg=yaw_deg,
                                phase_deg=phase_deg, mirror_x=mirror_x,
                                reverse=reverse,
                                label=f'{label}V' if label else 'V')
        self.right = LegInstance(leg_for_right, A_world, yaw_deg=yaw_deg,
                                 phase_deg=phase_deg + 180, mirror_x=mirror_x,
                                 reverse=reverse,
                                 label=f'{label}H' if label else 'H')
    
    def render(self, canvas, theta_global, show_paths=True, show_labels=False):
        # Båda benen, men dela vevskiva (rita bara en gång)
        self.left.render(canvas, theta_global, show_path=show_paths,
                         show_crank_disk=True, show_labels=show_labels,
                         opacity=0.85)
        self.right.render(canvas, theta_global, show_path=show_paths,
                          show_crank_disk=False, show_labels=show_labels,
                          opacity=0.55)


# ============================================================
# Rider — schematisk förare med antropometriska proportioner
# ============================================================
class Rider:
    """
    Schematisk förare, parameteriserad av total längd.
    
    Proportionerna följer ergonomiska riktvärden. Föraren sitter på sadeln
    (Q) med lätt framåtlutning, händerna på styret, fötterna på pedaler
    som är 180° fasförskjutna (vänster och höger).
    
    Args:
        height: total kroppslängd i cm (default 180)
        sadle_world: sadelns världsposition (höften sitter här)
        handlebar_world: styrhandtagens världsposition
        pedal_world: pedalvevcentrum
        pedal_radius: pedalvevarmens längd
        pedal_phase_deg: vänster pedals fasvinkel kring P (0=framåt,
                         90=upp, 180=bakåt, 270=ner)
        torso_angle_deg: ryggradens lutning framåt från lodrätt
        style: stilval för rendering
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
    
    def __init__(self, height=180, sadle_world=None, handlebar_world=None,
                 pedal_world=None, pedal_radius=17.0, pedal_phase_deg=90,
                 torso_angle_deg=10, style=None):
        self.height = height
        self.sadle = np.asarray(sadle_world, dtype=float) if sadle_world is not None else None
        self.handlebar = np.asarray(handlebar_world, dtype=float) if handlebar_world is not None else None
        self.pedal = np.asarray(pedal_world, dtype=float) if pedal_world is not None else None
        self.pedal_radius = pedal_radius
        self.pedal_phase = np.radians(pedal_phase_deg)
        self.torso_angle = np.radians(torso_angle_deg)
        self.style = style or {}
        
        self._compute_joints()
    
    def _segment(self, name):
        return self.height * self.PROPORTIONS[name]
    
    def _compute_joints(self):
        """Beräkna alla led-positioner."""
        self.hip = self.sadle.copy()
        
        torso_len = self._segment('torso')
        self.shoulder = self.hip + torso_len * np.array([
            np.sin(self.torso_angle),
            np.cos(self.torso_angle),
        ])
        
        head_len = self._segment('head')
        self.head_top = self.shoulder + head_len * np.array([
            np.sin(self.torso_angle),
            np.cos(self.torso_angle),
        ])
        
        if self.handlebar is not None:
            self.hand = self.handlebar.copy()
            self.elbow, self.arm_reach = self._compute_intermediate(
                self.shoulder, self.hand,
                self._segment('upper_arm'),
                self._segment('forearm'),
                bend_direction='down_back',
            )
        else:
            self.hand = None
            self.elbow = None
            self.arm_reach = None
        
        # Båda fötterna
        if self.pedal is not None:
            pedal_left = self.pedal + self.pedal_radius * np.array([
                np.cos(self.pedal_phase),
                np.sin(self.pedal_phase),
            ])
            right_phase = self.pedal_phase + np.pi
            pedal_right = self.pedal + self.pedal_radius * np.array([
                np.cos(right_phase),
                np.sin(right_phase),
            ])
            
            # Beräkna knän — och om benet inte når, sätt foten där den faktiskt
            # hamnar (vid maximal sträckning)
            self.knee_left, self.leg_left_reach = self._compute_intermediate(
                self.hip, pedal_left,
                self._segment('thigh'),
                self._segment('shin'),
                bend_direction='forward',
            )
            self.knee_right, self.leg_right_reach = self._compute_intermediate(
                self.hip, pedal_right,
                self._segment('thigh'),
                self._segment('shin'),
                bend_direction='forward',
            )
            
            # Om benet inte räcker fram, beräkna var foten faktiskt hamnar
            # (vid maximal sträckning från knäet)
            if self.leg_left_reach == 'overreach':
                shin_len = self._segment('shin')
                direction = (pedal_left - self.knee_left)
                direction = direction / max(np.linalg.norm(direction), 1e-6)
                self.foot_left = self.knee_left + shin_len * direction
            else:
                self.foot_left = pedal_left
            
            if self.leg_right_reach == 'overreach':
                shin_len = self._segment('shin')
                direction = (pedal_right - self.knee_right)
                direction = direction / max(np.linalg.norm(direction), 1e-6)
                self.foot_right = self.knee_right + shin_len * direction
            else:
                self.foot_right = pedal_right
        else:
            self.foot_left = self.foot_right = None
            self.knee_left = self.knee_right = None
            self.leg_left_reach = self.leg_right_reach = None
    
    @staticmethod
    def _compute_intermediate(p1, p2, len1, len2, bend_direction='forward'):
        """
        Inverse kinematik för en två-länkad arm/ben.
        
        Returnerar (mellanpunkt, reach_status) där:
            mellanpunkt: position för armbåge/knä
            reach_status: 'ok' = nådde målet
                          'overreach' = benet är för kort, sträckt rakt mot målet
                          'underreach' = benet är för långt (kan inte vika ihop)
        
        Om reach_status != 'ok', representerar p2 inte fotens faktiska position
        utan en oåtkomlig önskemål. Anroparen får bestämma vad som händer.
        
        bend_direction: 'forward' = knä framåt, 'down_back' = armbåge bakåt-ned
        """
        p1 = np.asarray(p1, dtype=float)
        p2 = np.asarray(p2, dtype=float)
        d = np.linalg.norm(p2 - p1)
        
        if d > len1 + len2:
            # Benet är för kort — sträckt rakt mot målet
            direction = (p2 - p1) / d
            intermediate = p1 + len1 * direction
            return intermediate, 'overreach'
        
        if d < abs(len1 - len2):
            # För nära — benet kan inte vika ihop så mycket
            direction = (p2 - p1) / d if d > 1e-6 else np.array([0, 1])
            intermediate = p1 + len1 * direction
            return intermediate, 'underreach'
        
        a = (len1**2 - len2**2 + d**2) / (2 * d)
        h_sq = max(0, len1**2 - a**2)
        h = np.sqrt(h_sq)
        mid = p1 + (a / d) * (p2 - p1)
        perp = np.array([-(p2[1] - p1[1]), p2[0] - p1[0]]) / d
        candidates = [mid + h * perp, mid - h * perp]
        
        if bend_direction == 'forward':
            return max(candidates, key=lambda p: p[0]), 'ok'
        elif bend_direction == 'down_back':
            return min(candidates, key=lambda p: p[0] + p[1] * 0.5), 'ok'
        else:
            return candidates[0], 'ok'
    
    def render(self, canvas):
        """Rita föraren som streckfigur. Båda benen och båda armarna."""
        # Stilval
        style = {
            'limb_color': '#4E342E',
            'limb_width': 2.5,
            'joint_fill': '#3E2723',
            'joint_radius': 1.6,
            'head_radius': 6.5,
            'head_fill': '#FFCCBC',
            'head_stroke': '#5D4037',
            'opacity': 0.9,
            'foot_radius': 1.8,
        }
        style.update(self.style)
        
        # === Bål (höft -> axel) ===
        canvas.line(self.hip, self.shoulder,
                    color=style['limb_color'], width=style['limb_width'],
                    opacity=style['opacity'])
        
        # === Huvud ===
        head_center = self.shoulder + (self.head_top - self.shoulder) * 0.6
        canvas.circle(head_center, style['head_radius'],
                      fill=style['head_fill'], stroke=style['head_stroke'],
                      stroke_width=0.6, opacity=style['opacity'])
        
        # === Arm: axel -> armbåge -> hand ===
        if self.elbow is not None and self.hand is not None:
            canvas.line(self.shoulder, self.elbow,
                        color=style['limb_color'], width=style['limb_width'],
                        opacity=style['opacity'])
            canvas.line(self.elbow, self.hand,
                        color=style['limb_color'], width=style['limb_width'],
                        opacity=style['opacity'])
        
        # === Ben: rita BÅDA benen ===
        # Vänster ben — färga rött om det inte når pedalen
        if self.knee_left is not None and self.foot_left is not None:
            left_color = '#D32F2F' if self.leg_left_reach == 'overreach' else style['limb_color']
            canvas.line(self.hip, self.knee_left,
                        color=left_color, width=style['limb_width'],
                        opacity=style['opacity'])
            canvas.line(self.knee_left, self.foot_left,
                        color=left_color, width=style['limb_width'],
                        opacity=style['opacity'])
        
        # Höger ben
        if self.knee_right is not None and self.foot_right is not None:
            right_opacity = style['opacity'] * 0.6
            right_color = '#D32F2F' if self.leg_right_reach == 'overreach' else style['limb_color']
            canvas.line(self.hip, self.knee_right,
                        color=right_color, width=style['limb_width'],
                        opacity=right_opacity)
            canvas.line(self.knee_right, self.foot_right,
                        color=right_color, width=style['limb_width'],
                        opacity=right_opacity)
        
        # === Leder som tydliga punkter ===
        joints_full = [self.hip, self.shoulder]
        if self.elbow is not None: joints_full.append(self.elbow)
        if self.knee_left is not None: joints_full.append(self.knee_left)
        for p in joints_full:
            canvas.circle(p, style['joint_radius'],
                          fill=style['joint_fill'], stroke='white',
                          stroke_width=0.4, opacity=style['opacity'])
        
        # Höger ben-leder med lägre opacity
        if self.knee_right is not None:
            canvas.circle(self.knee_right, style['joint_radius'],
                          fill=style['joint_fill'], stroke='white',
                          stroke_width=0.4, opacity=style['opacity'] * 0.6)
        
        # Fötter som tydliga markörer
        if self.foot_left is not None:
            canvas.circle(self.foot_left, style['foot_radius'],
                          fill='#1B5E20', stroke='white', stroke_width=0.4,
                          opacity=style['opacity'])
        if self.foot_right is not None:
            canvas.circle(self.foot_right, style['foot_radius'],
                          fill='#1B5E20', stroke='white', stroke_width=0.4,
                          opacity=style['opacity'] * 0.6)


# ============================================================
# Frame — maskinens ram med ramnoder och stagningar
# ============================================================
class Frame:
    """
    Maskinens ram med separat fram- och bakvevaxel och triangulärt fackverk.
    
    Noder:
        A_rear — bakvevcentrum (under sadeln)
        A_front — framvevcentrum (förskjuten framåt)
        P — pedalvevcentrum
        Q — sadelposition
        B_front, B_rear — benens fasta leder
        M — fackverksnod nedanför framdelen (för triangulär stelhet nedåt)
        N — fackverksnod ovanför framdelen (för styrets fäste)
        H — styrhandtagens centrum
    
    Länkstruktur (triangulärt fackverk):
        Bakdel: P-A_rear, A_rear-Q, A_rear-B_rear, P-B_rear  → bildar trianglar
        Huvudbalk: A_rear-A_front
        Framdel ned: A_front-B_front, A_front-M, M-P, M-B_front
        Framdel upp: A_front-N (rakt uppåt), N-B_front (triangulering uppåt)
        Styraxel: N-H (kort)
    """
    
    N_OFFSET_UP = 17.0  # cm rakt uppåt från A_front till N
    
    def __init__(self, A_front_world, A_rear_world, P_height, Q_height,
                 B_front_world, B_rear_world,
                 handlebar_pos=None,
                 m_fraction=0.5, m_offset_y=-5.0,
                 n_offset_up=None,
                 pedal_radius=17.0, style=None):
        """
        m_fraction: var på P-B_front-linjen M projicerar (0=vid P, 1=vid B_front)
        m_offset_y: vertikal förskjutning av M från P-B_front-linjen (cm,
                    negativ = nedåt i världen).
        n_offset_up: hur långt uppåt över A_front som N sitter (cm). Default 17.
        """
        self.A_front = np.asarray(A_front_world, dtype=float)
        self.A_rear = np.asarray(A_rear_world, dtype=float)
        self.P = np.array([self.A_rear[0], P_height])
        self.Q = np.array([self.A_rear[0], Q_height])
        self.B_front = np.asarray(B_front_world, dtype=float)
        self.B_rear = np.asarray(B_rear_world, dtype=float)
        self.pedal_radius = pedal_radius
        self.style = style or {}
        
        # M (nedre fackverksnod)
        m_on_line = self.P + m_fraction * (self.B_front - self.P)
        self.M = m_on_line + np.array([0, m_offset_y])
        
        # N (övre fackverksnod) — rakt upp från A_front
        if n_offset_up is None:
            n_offset_up = self.N_OFFSET_UP
        self.N = self.A_front + np.array([0, n_offset_up])
        
        if handlebar_pos is not None:
            self.H = np.asarray(handlebar_pos, dtype=float)
        else:
            self.H = None
    
    @property
    def nodes(self):
        n = {
            'A_front': self.A_front, 'A_rear': self.A_rear,
            'P': self.P, 'Q': self.Q,
            'B_front': self.B_front, 'B_rear': self.B_rear,
            'M': self.M, 'N': self.N,
        }
        if self.H is not None:
            n['H'] = self.H
        return n
    
    @property
    def links(self):
        ls = [
            # Bakdel
            ('P', 'A_rear', 'pedalrör'),
            ('A_rear', 'Q', 'sadelrör'),
            ('A_rear', 'B_rear', 'A_bak→B_bak'),
            ('P', 'B_rear', 'staging P→B_bak'),
            
            # Huvudbalk
            ('A_rear', 'A_front', 'huvudbalk'),
            
            # Framdel nedåt — triangulärt fackverk
            ('A_front', 'B_front', 'A_fram→B_fram'),
            ('P', 'M', 'P→M (del 1 av stagning)'),
            ('M', 'B_front', 'M→B_fram (del 2 av stagning)'),
            ('A_front', 'M', 'fackverkstag (nedåt)'),
            
            # Framdel uppåt — triangulering för styrets fäste
            ('A_front', 'N', 'fackverkstag (uppåt)'),
            ('N', 'B_front', 'N→B_fram (triangulering)'),
        ]
        if self.H is not None:
            # Styret monteras från N istället för B_front
            ls.append(('N', 'H', 'styraxel'))
        return ls
    
    def render(self, canvas):
        s = canvas.DEFAULT_STYLES['frame'].copy()
        s.update(self.style.get('frame', {}))
        
        nodes = self.nodes
        for n1, n2, _ in self.links:
            canvas.line(nodes[n1], nodes[n2],
                        color=s['color'], width=s['width'], opacity=s['opacity'])
        
        # Pedalvevsskiva
        pedal_style = self.style.get('pedal_disk', {
            'fill': '#FFF3E0', 'stroke': '#FB8C00', 'opacity': 0.4
        })
        canvas.circle(self.P, self.pedal_radius,
                      fill=pedal_style['fill'],
                      stroke=pedal_style['stroke'],
                      stroke_width=0.4, dasharray='2,1.5',
                      opacity=pedal_style['opacity'])
        
        # Styrhandtag
        if self.H is not None:
            canvas.line([self.H[0] - 3, self.H[1]], [self.H[0] + 3, self.H[1]],
                        color='#222', width=2.0)
            canvas.circle(self.H, 1.8, fill='#333', stroke='white',
                          stroke_width=0.4)
        
        # Ramnoder
        ns = canvas.DEFAULT_STYLES['frame_node'].copy()
        ns.update(self.style.get('frame_node', {}))
        for name, p in nodes.items():
            canvas.circle(p, ns['radius'], fill=ns['fill'],
                          stroke='white', stroke_width=0.4, opacity=ns['opacity'])
            canvas.text(p, name, size=3.5, color='black', weight='bold',
                        dx=3, dy=-1.5)


# ============================================================
# Machine
# ============================================================
class Machine:
    """
    Fyrbent maskin med separat fram- och bakvevaxel.
    
    Args:
        crank_height: vevcentrumens höjd över marken (cm)
        wheelbase: avstånd mellan fram- och bakvevaxel (cm)
        pedal_height: pedalvevcentrums höjd (cm)
        sadle_height: sadelns höjd (cm)
        pedal_radius: pedalvevarmens längd (cm)
        rider_height: förarens längd (cm), None om ingen förare
        handlebar_x: styrets x-position (cm), None = auto baserat på A_front
        handlebar_y: styrets höjd (cm), None = auto baserat på sadelhöjd
        gait: 'trot' eller 'walk'
        styles: stil-overrides
    """
    
    # Baseline AB-värden i lokala bencoord
    AB_BASE_X = 38.0
    AB_BASE_Y = 7.8
    AB_BASELINE = float(np.sqrt(AB_BASE_X**2 + AB_BASE_Y**2))  # 38.79 cm
    
    # AB-justeringsspann vid full styrutslag.
    # Inre sidan: AB förlängs upp till +1.5 cm (mekanikgräns +1.71)
    # Yttre sidan: AB kortas till -0.8 cm (mekanikgräns -0.99)
    # Marginal lämnad för att undvika mekanikbrott.
    STEER_AB_INNER = 1.5   # förlängning av AB på inre sidan
    STEER_AB_OUTER = 0.8   # förkortning av AB på yttre sidan
    
    def __init__(self, crank_height=91.83, wheelbase=40,
                 pedal_height=45.0, sadle_height=135.0,
                 pedal_radius=17.0, rider_height=180,
                 handlebar_x=None, handlebar_y=None,
                 gait='trot', steer=0.0,
                 styles=None):
        """
        Args:
            steer: styrutslag mellan -1 (full vänster) och +1 (full höger).
                   Vid steer=0 är båda sidor på baseline.
                   Vid vänstersväng (steer<0): vänster sida är inre, dess AB 
                   förlängs (kortare steg). Höger sida är yttre, dess AB 
                   förkortas (längre steg).
        """
        self.crank_height = crank_height
        self.wheelbase = wheelbase
        self.pedal_height = pedal_height
        self.sadle_height = sadle_height
        self.pedal_radius = pedal_radius
        self.rider_height = rider_height
        self.gait = gait
        self.steer = float(np.clip(steer, -1, 1))
        self.styles = styles or {}
        
        # AB-justeringar per sida (asymmetrisk styrning)
        # 
        # Vid vänstersväng (steer<0):
        #   Vänster sida = INRE: AB förlängs med STEER_AB_INNER (kortare steg)
        #   Höger sida   = YTTRE: AB kortas med STEER_AB_OUTER (längre steg)
        # Vid högersväng (steer>0): tvärtom.
        # 
        # |steer| skalar linjärt — vid steer=±0.5 får vi halva justeringen.
        if self.steer < 0:
            # Vänstersväng: vänster inre, höger yttre
            ab_offset_left = -self.steer * self.STEER_AB_INNER     # +1.5 vid steer=-1
            ab_offset_right = self.steer * self.STEER_AB_OUTER     # -0.8 vid steer=-1
        else:
            # Högersväng (eller rakt): höger inre, vänster yttre
            ab_offset_left = -self.steer * self.STEER_AB_OUTER     # -0.8 vid steer=+1
            ab_offset_right = self.steer * self.STEER_AB_INNER     # +1.5 vid steer=+1
        
        # Konvertera till link_adjustments för varje sida
        link_adj_left = self._ab_offset_to_adjustments(ab_offset_left)
        link_adj_right = self._ab_offset_to_adjustments(ab_offset_right)
        
        self.ab_offset_left = ab_offset_left
        self.ab_offset_right = ab_offset_right
        
        # Vi behöver två Leg-objekt: en med vänster sidans justering, 
        # en med höger sidans justering
        leg_left = Leg(link_adjustments=link_adj_left)
        leg_right = Leg(link_adjustments=link_adj_right)
        
        # Bakre vevaxel: vid origo
        A_rear = np.array([0.0, crank_height])
        # Främre vevaxel: framåt
        A_front = np.array([wheelbase, crank_height])
        
        if gait == 'trot':
            front_phase, rear_phase = 0, 180
        elif gait == 'walk':
            front_phase, rear_phase = 0, 90
        else:
            raise ValueError(f"Okänd gångart: {gait}")
        
        # Skapa LegPair där 'left' och 'right' ben har sina egna Leg-objekt
        # med rätt AB-justering för respektive sida.
        self.front = LegPair(leg_left, A_front, yaw_deg=0, mirror_x=False,
                             reverse=True,
                             phase_deg=front_phase, label='F',
                             leg_right=leg_right)
        self.rear = LegPair(leg_left, A_rear, yaw_deg=180, mirror_x=False,
                            reverse=False,
                            phase_deg=rear_phase, label='B',
                            leg_right=leg_right)
        
        B_front_world = self.front.left.pose(0)['B']
        B_rear_world = self.rear.left.pose(0)['B']
        
        # Styrposition
        if handlebar_x is None:
            handlebar_x = wheelbase + 20
        if handlebar_y is None:
            handlebar_y = sadle_height - 25
        handlebar_pos = np.array([handlebar_x, handlebar_y])
        
        self.frame = Frame(
            A_front_world=A_front,
            A_rear_world=A_rear,
            P_height=pedal_height,
            Q_height=sadle_height,
            B_front_world=B_front_world,
            B_rear_world=B_rear_world,
            handlebar_pos=handlebar_pos,
            pedal_radius=pedal_radius,
            style=self.styles,
        )
        
        # Föraren
        if rider_height is not None:
            self.rider = Rider(
                height=rider_height,
                sadle_world=np.array([0, sadle_height]),
                handlebar_world=handlebar_pos,
                pedal_world=np.array([0, pedal_height]),
                pedal_radius=pedal_radius,
                pedal_phase_deg=90,
                style=self.styles.get('rider', {}),
            )
            self._check_rider_reach()
        else:
            self.rider = None
    
    @classmethod
    def _ab_offset_to_adjustments(cls, ab_offset):
        """
        Konvertera AB-förlängning till link_adjustments för ABx och ABy.
        Båda komponenterna skalas proportionellt så AB-stångens riktning 
        bevaras.
        """
        new_AB = cls.AB_BASELINE + ab_offset
        scale = new_AB / cls.AB_BASELINE
        dABx = cls.AB_BASE_X * (scale - 1)
        dABy = cls.AB_BASE_Y * (scale - 1)
        return {'ABx': dABx, 'ABy': dABy}
    
    def _check_rider_reach(self):
        """Sampla över hela pedalcykeln och kolla om föraren når överallt."""
        if self.rider is None: return
        
        leg_total = self.rider._segment('thigh') + self.rider._segment('shin')
        # Maximalt avstånd höft till någon punkt på pedalcirkeln
        hip = self.rider.hip
        pedal_center = self.rider.pedal
        pedal_radius = self.rider.pedal_radius
        max_dist = np.linalg.norm(pedal_center - hip) + pedal_radius
        min_dist = max(0, np.linalg.norm(pedal_center - hip) - pedal_radius)
        
        warnings = []
        if max_dist > leg_total:
            shortfall = max_dist - leg_total
            warnings.append(
                f"VARNING: Föraren ({self.rider_height} cm) når INTE pedalen i "
                f"dess längsta läge — saknar {shortfall:.1f} cm. "
                f"(maximalt avstånd höft–pedal {max_dist:.1f} cm, "
                f"benlängd lår+underben {leg_total:.1f} cm)"
            )
        
        # Kolla armarna
        arm_total = self.rider._segment('upper_arm') + self.rider._segment('forearm')
        hand_dist = np.linalg.norm(self.rider.handlebar - self.rider.shoulder)
        if hand_dist > arm_total:
            shortfall = hand_dist - arm_total
            warnings.append(
                f"VARNING: Föraren når INTE styret — saknar {shortfall:.1f} cm. "
                f"(avstånd axel–styre {hand_dist:.1f} cm, "
                f"armlängd {arm_total:.1f} cm)"
            )
        
        for w in warnings:
            print(w)
    
    def world_extents(self):
        x_min, x_max, y_min, y_max = 1e9, -1e9, 1e9, -1e9
        for inst in [self.front.left, self.front.right,
                     self.rear.left, self.rear.right]:
            path = inst.foot_path(60)
            x_min = min(x_min, path[:,0].min())
            x_max = max(x_max, path[:,0].max())
            y_min = min(y_min, path[:,1].min())
            y_max = max(y_max, path[:,1].max())
        for p in self.frame.nodes.values():
            x_min = min(x_min, p[0])
            x_max = max(x_max, p[0])
            y_min = min(y_min, p[1])
            y_max = max(y_max, p[1])
        x_min = min(x_min, self.frame.P[0] - self.frame.pedal_radius)
        x_max = max(x_max, self.frame.P[0] + self.frame.pedal_radius)
        if self.rider:
            rider_points = [self.rider.head_top, self.rider.shoulder, self.rider.hand,
                            self.rider.elbow]
            if self.rider.foot_left is not None:
                rider_points.append(self.rider.foot_left)
            if self.rider.foot_right is not None:
                rider_points.append(self.rider.foot_right)
            if self.rider.knee_left is not None:
                rider_points.append(self.rider.knee_left)
            if self.rider.knee_right is not None:
                rider_points.append(self.rider.knee_right)
            for p in rider_points:
                if p is not None:
                    x_min = min(x_min, p[0] - 7)
                    x_max = max(x_max, p[0] + 7)
                    y_min = min(y_min, p[1] - 7)
                    y_max = max(y_max, p[1] + 7)
        y_min = min(y_min, -5)
        return x_min, x_max, y_min, y_max
    
    def render_leg_sweep(self, canvas, n_steps=24, opacity=0.06):
        for i in range(n_steps):
            theta = 2 * np.pi * i / n_steps
            self.front.left.render(canvas, theta, show_path=False,
                                   show_crank_disk=False, show_labels=False,
                                   opacity=opacity)
            self.front.right.render(canvas, theta, show_path=False,
                                    show_crank_disk=False, show_labels=False,
                                    opacity=opacity)
            self.rear.left.render(canvas, theta, show_path=False,
                                  show_crank_disk=False, show_labels=False,
                                  opacity=opacity)
            self.rear.right.render(canvas, theta, show_path=False,
                                   show_crank_disk=False, show_labels=False,
                                   opacity=opacity)
    
    def render(self, theta_global=0.0, filename=None, width_px=1100,
               title=None, show_sweep=False):
        x_min, x_max, y_min, y_max = self.world_extents()
        canvas = Canvas(x_min, x_max, y_min, y_max, pad=15)
        
        canvas.grid(spacing=10, color='#ececec')
        canvas.grid(spacing=50, color='#d0d0d0')
        
        sy_mark = canvas.w([0, 0])[1]
        canvas.add(f'<line x1="0" y1="{sy_mark:.1f}" '
                   f'x2="{canvas.width:.1f}" y2="{sy_mark:.1f}" '
                   f'stroke="#555" stroke-width="0.5"/>')
        canvas.text([canvas.x_min + 5, -3], 'mark (y=0)', size=2.8, color='#555')
        
        sx_origo = canvas.w([0, 0])[0]
        canvas.add(f'<line x1="{sx_origo:.1f}" y1="0" '
                   f'x2="{sx_origo:.1f}" y2="{canvas.height:.1f}" '
                   f'stroke="#999" stroke-width="0.3" stroke-dasharray="2,1"/>')
        
        arrow_y = -5
        a_start = canvas.w([20, arrow_y])
        a_end = canvas.w([60, arrow_y])
        canvas.add(f'<line x1="{a_start[0]:.1f}" y1="{a_start[1]:.1f}" '
                   f'x2="{a_end[0]:.1f}" y2="{a_end[1]:.1f}" '
                   f'stroke="#2E7D32" stroke-width="0.9"/>')
        canvas.add(f'<polygon points="{a_end[0]:.1f},{a_end[1]:.1f} '
                   f'{a_end[0]-3:.1f},{a_end[1]-1.6:.1f} '
                   f'{a_end[0]-3:.1f},{a_end[1]+1.6:.1f}" fill="#2E7D32"/>')
        canvas.text([40, arrow_y + 2], 'färdriktning',
                    size=3.2, color='#2E7D32', anchor='middle', weight='600')
        
        if show_sweep:
            self.render_leg_sweep(canvas, n_steps=24, opacity=0.06)
        
        self.frame.render(canvas)
        
        self.front.render(canvas, theta_global, show_paths=True, show_labels=False)
        self.rear.left.render(canvas, theta_global, show_path=True,
                              show_crank_disk=True, show_labels=False, opacity=0.85)
        self.rear.right.render(canvas, theta_global, show_path=True,
                               show_crank_disk=False, show_labels=False, opacity=0.55)
        
        if self.rider:
            self.rider.render(canvas)
        
        if title is None:
            sweep_note = ' · med svept benområde' if show_sweep else ''
            rider_note = f' · förare {self.rider_height} cm' if self.rider else ''
            title = (f'Jansen-maskin · θ={np.degrees(theta_global):.0f}° · '
                     f'wheelbase {self.wheelbase} cm{rider_note}{sweep_note}')
        canvas.add(f'<text x="{canvas.width/2:.1f}" y="7" '
                   f'font-size="4.5" fill="#222" text-anchor="middle" '
                   f'font-weight="bold">{title}</text>')
        
        if filename:
            canvas.save(filename, width_px=width_px)
        return canvas


# ============================================================
# Demo
# ============================================================
if __name__ == '__main__':
    print("Bygger Jansen-maskin: rakt, vänstersväng, högersväng...")
    
    # Tre maskiner med olika steer-värden
    for steer, suffix in [(0.0, ''), (-1.0, '_steer_left'), (+1.0, '_steer_right')]:
        machine = Machine(
            crank_height=91.83, wheelbase=50,
            pedal_height=45.0, sadle_height=113.0,
            pedal_radius=17.0, rider_height=194,
            handlebar_x=35, handlebar_y=110,
            gait='trot', steer=steer,
        )
        fname = f'/mnt/user-data/outputs/machine{suffix}.svg'
        machine.render(theta_global=np.radians(60), filename=fname)
        print(f"  steer={steer:+.1f}: AB_v={machine.ab_offset_left:+.2f}, "
              f"AB_h={machine.ab_offset_right:+.2f} → {fname}")
    
    # Sweep med rakt läge
    machine = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    machine.render(theta_global=np.radians(60), 
                   filename='/mnt/user-data/outputs/machine_sweep.svg',
                   show_sweep=True)
