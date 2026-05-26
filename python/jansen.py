"""
Jansens benmekanism — Python-implementation
=============================================

Beräknar geometri och fotbana för Theo Jansens 11-bar benmekanism.

Topologi
--------
Mekanismen har 8 leder och 11 stänger plus en fast avståndsstång (A-B):

    Leder:
      A — vevcentrum (fast)
      B — fast pivot (fast)
      C — vevtapp på vevskivans rand
      D, E — leder som bildar övre delen av benet
      F — mellanled
      G — nedre mellanled  
      H — foten

    Stänger (med Jansens "heliga tal" i cm):
      AC = 15.0   (vevradie)
      CD = 50.0,  BD = 41.5,  DE = 55.8,  BE = 40.1
      CF = 61.9,  BF = 39.3
      EG = 39.4,  FG = 36.7
      FH = 49.0,  GH = 65.7

    Fasta punkter:
      A vid origo
      B vid (+38, +7.8) — alltså 38 cm åt höger och 7.8 cm nedanför A
      (avstånd A-B = sqrt(38^2 + 7.8^2) ≈ 38.79 cm)

Koordinatkonvention
-------------------
Benets lokala koordinatsystem:
  - x växer i den riktning som projektionen av AB pekar
    (alltså: lokal positiv x pekar mot B från A)
  - y växer nedåt
  - foten H har störst y-värde (längst ner)
  - vevvinkeln θ mäts medurs från positiva x-axeln

Konsekvenser av att lokal x-axel pekar mot B:
  - I varje ben sitter B alltid på lokal positiv x
  - Foten H rör sig under stödfasen i positiv x-riktning lokalt
    (alltså bort från A, mot B-sidan)
  - I världen vänds detta så att benet kliver MOT B i lokala koord, vilket
    motsvarar att maskinen rör sig från B-sidan av varje ben — d.v.s. om
    frambenens lokala x-axel pekar bakåt i världen så kliver maskinen
    framåt under stödfas.

Spårningsmetod
--------------
Cirkelskärningsmetoden (forward kinematics). Varje cirkelskärning har två
lösningar; vi väljer KONSEKVENT sida ('sign') genom hela vevcykeln för att
undvika branch-hopp vid singulariteter. Den korrekta sign-konfigurationen
för Jansens originalmekanism med B på positiv x är (-1, -1, +1, -1, +1)
för (D, E, F, G, H).

Användning
----------
    from jansen import jansen_pose, foot_path
    
    # Beräkna ledpositioner vid godtycklig vevvinkel
    pose = jansen_pose(theta=np.pi/3)  # 60 grader
    print(pose['H'])  # fotposition
    
    # Beräkna hela fotbanan
    path = foot_path(n_points=360)
"""

import numpy as np


# ============================================================
# Stångenheter (cm) — Jansens "heliga tal"
# ============================================================
AC = 15.0    # vevradie
CD = 50.0
BD = 41.5
DE = 55.8
BE = 40.1
CF = 61.9
BF = 39.3
EG = 39.4
FG = 36.7
FH = 49.0
GH = 65.7

# Fasta lederna i benets lokala koordinatsystem (y växer nedåt)
# B ligger på positiv x — lokal x-axel pekar i AB-riktning
A = np.array([0.0, 0.0])
B = np.array([+38.0, 7.8])

# Sign-konfiguration som ger Jansens klassiska fotbana med B på positiv x
# (en för varje cirkelskärning: D, E, F, G, H)
SIGNS = (-1, -1, +1, -1, +1)


def circle_intersect(c1, r1, c2, r2, sign):
    """
    Hitta skärningspunkt mellan två cirklar.
    
    Args:
        c1, c2: cirklarnas centra som numpy-arrays
        r1, r2: cirklarnas radier
        sign: +1 eller -1, väljer vilken av de två skärningarna att returnera
              (+1 = vänster om vektorn c1->c2, -1 = höger om)
    
    Returns:
        Skärningspunkt som numpy-array, eller None om cirklarna inte skär varandra
    """
    c1 = np.asarray(c1, dtype=float)
    c2 = np.asarray(c2, dtype=float)
    diff = c2 - c1
    dist = np.linalg.norm(diff)
    
    # Ingen skärning om cirklarna är för långt isär eller en innesluten i den andra
    if dist > r1 + r2 + 1e-9 or dist < abs(r1 - r2) - 1e-9:
        return None
    
    # Avstånd längs c1->c2 till skärningskordans mitt
    a_proj = (r1**2 - r2**2 + dist**2) / (2 * dist)
    # Halva längden av skärningskordan
    h_dist = np.sqrt(max(0.0, r1**2 - a_proj**2))
    
    # Mittpunkt på skärningskordan
    midpoint = c1 + (a_proj / dist) * diff
    # Vinkelrät enhetsvektor (90° moturs från c1->c2 i y-uppåt-system,
    # vilket blir 90° medurs i y-nedåt-system)
    perp = np.array([-diff[1], diff[0]]) / dist
    
    return midpoint + sign * h_dist * perp


def jansen_pose(theta, signs=SIGNS):
    """
    Beräkna alla ledpositioner vid vevvinkel theta.
    
    Args:
        theta: vevvinkel i radianer (0 = vev pekar rakt åt höger,
               positiva värden roterar medurs i y-nedåt-vy)
        signs: tuple (s_D, s_E, s_F, s_G, s_H) av +1/-1 för cirkelskärningarna
               (default: Jansens korrekta konfiguration)
    
    Returns:
        dict {'A','B','C','D','E','F','G','H'} med numpy-arrays för varje led,
        eller None om mekanismen inte är konstruerbar vid den vinkeln
    """
    s_D, s_E, s_F, s_G, s_H = signs
    
    # Vevtapp C ligger på vevskivans rand. Tecknet på sin(theta) gör att
    # positiva theta roterar medurs i y-nedåt-vy.
    C = A + AC * np.array([np.cos(theta), -np.sin(theta)])
    
    # Övre del: D, E
    D = circle_intersect(C, CD, B, BD, s_D)
    if D is None: return None
    
    E = circle_intersect(D, DE, B, BE, s_E)
    if E is None: return None
    
    # Mellandel: F
    F = circle_intersect(C, CF, B, BF, s_F)
    if F is None: return None
    
    # Nedre del: G, H (fot)
    G = circle_intersect(E, EG, F, FG, s_G)
    if G is None: return None
    
    H = circle_intersect(F, FH, G, GH, s_H)
    if H is None: return None
    
    return {'A': A, 'B': B, 'C': C, 'D': D, 'E': E, 'F': F, 'G': G, 'H': H}


def foot_path(n_points=360, signs=SIGNS):
    """
    Beräkna hela fotbanan över en komplett vevcykel.
    
    Args:
        n_points: antal punkter att sampla cykeln med
        signs: sign-konfiguration (default: Jansens)
    
    Returns:
        numpy-array av form (n_points, 2) med fotpositioner
    """
    thetas = np.linspace(0, 2*np.pi, n_points, endpoint=False)
    path = []
    for theta in thetas:
        pose = jansen_pose(theta, signs)
        if pose is None:
            raise RuntimeError(f"Geometri ogiltig vid theta = {np.degrees(theta):.1f}°")
        path.append(pose['H'])
    return np.array(path)


def all_poses(n_points=360, signs=SIGNS):
    """
    Beräkna alla ledpositioner över en komplett vevcykel.
    
    Args:
        n_points: antal punkter att sampla cykeln med
        signs: sign-konfiguration
    
    Returns:
        Lista av pose-dicts, en per vinkel
    """
    thetas = np.linspace(0, 2*np.pi, n_points, endpoint=False)
    poses = []
    for theta in thetas:
        pose = jansen_pose(theta, signs)
        if pose is None:
            raise RuntimeError(f"Geometri ogiltig vid theta = {np.degrees(theta):.1f}°")
        poses.append(pose)
    return poses


def analyze(signs=SIGNS, n_points=360):
    """
    Analysera mekanismens prestanda: steglängd, fothöjd, höjd över mark, etc.
    
    Returns:
        dict med nyckelparametrar
    """
    path = foot_path(n_points, signs)
    
    step_length = path[:,0].max() - path[:,0].min()
    foot_lift = path[:,1].max() - path[:,1].min()
    ground_y = path[:,1].max()  # foten längst ner = störst y
    crank_height = ground_y - A[1]  # avstånd från vevcentrum till mark
    
    # Stödfas: del av cykeln där foten är nära marken
    threshold = ground_y - foot_lift * 0.2
    stance_mask = path[:,1] > threshold
    stance_fraction = stance_mask.sum() / len(stance_mask)
    
    return {
        'step_length_cm': float(step_length),
        'foot_lift_cm': float(foot_lift),
        'crank_height_above_ground_cm': float(crank_height),
        'stance_fraction': float(stance_fraction),
        'step_to_crank_ratio': float(step_length / AC),
        'lift_to_crank_ratio': float(foot_lift / AC),
        'foot_x_range': (float(path[:,0].min()), float(path[:,0].max())),
        'foot_y_range': (float(path[:,1].min()), float(path[:,1].max())),
    }


# ============================================================
# Om koden körs direkt: skriv ut nyckeldata
# ============================================================
if __name__ == '__main__':
    print("Jansens benmekanism — Python-implementation")
    print("=" * 50)
    print()
    
    stats = analyze()
    print(f"Vevradie:                {AC} cm")
    print(f"Avstånd A-B:             {np.linalg.norm(B - A):.2f} cm")
    print(f"Steglängd:               {stats['step_length_cm']:.2f} cm")
    print(f"Fotlyftning:             {stats['foot_lift_cm']:.2f} cm")
    print(f"Höjd vevcentrum-mark:    {stats['crank_height_above_ground_cm']:.2f} cm")
    print(f"Andel cykel i stödfas:   {stats['stance_fraction']*100:.0f}%")
    print(f"Steg/vev-förhållande:    {stats['step_to_crank_ratio']:.2f}")
    print(f"Lyft/vev-förhållande:    {stats['lift_to_crank_ratio']:.2f}")
    print()
    
    print("Ledpositioner vid θ = 60° (matchar Wikipedia-bilden):")
    pose = jansen_pose(np.pi/3)
    for name in 'ABCDEFGH':
        p = pose[name]
        print(f"  {name}: ({p[0]:7.2f}, {p[1]:7.2f})")
