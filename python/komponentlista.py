"""
Generera en tabell över alla delar med dimensioner.
Sparas både som textfil och CSV för enkel referens vid utskrift.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import numpy as np
from machine import Machine, AC, CD, BD, DE, BE, CF, BF, EG, FG, FH, GH

SCALE = 0.2  # 1:5


def build_parts_list():
    """Bygg lista över alla delar med dimensioner."""
    machine = Machine(
        crank_height=91.83, wheelbase=50,
        pedal_height=45.0, sadle_height=113.0,
        pedal_radius=17.0, rider_height=194,
        handlebar_x=35, handlebar_y=110,
        gait='trot', steer=0.0,
    )
    nodes = machine.frame.nodes
    rider = machine.rider
    
    parts = []
    
    # === BENSTÄNGER ===
    leg_links = [
        # Ursprungliga 11 stänger (z1-planet) — Jansens topologi
        ('AC', AC, 'vevarm: A → vevtapp C'),
        ('CD', CD, 'från vevtapp till övre led D'),
        ('BD', BD, 'från fast led B till övre led D'),
        ('DE', DE, 'från övre led D till led E'),
        ('BE', BE, 'från fast led B till led E (z1-plan)'),
        ('CF', CF, 'från vevtapp till nedre led F'),
        ('BF', BF, 'från fast led B till nedre led F (z1-plan)'),
        ('EG', EG, 'från E ner till knäled G (z1-plan)'),
        ('FG', FG, 'från F till knäled G (z1-plan)'),
        ('FH', FH, 'från F till foten H'),
        ('GH', GH, 'från knäled G till foten H'),
        # 3D-fackverk i z2-planet (samma topologi som BEFG i z1)
        ('B2E2', BE, 'B2 till E2 i sekundärplan (z2)'),
        ('B2F2', BF, 'B2 till F2 i sekundärplan (z2)'),
        ('E2G2', EG, 'E2 till G2 i sekundärplan (z2)'),
        ('F2G2', FG, 'F2 till G2 i sekundärplan (z2)'),
        # Tvärbalkar mellan z1 och z2 (konstant längd = z_offset = 10 cm)
        ('BB2', 10.0, 'tvärbalk B → B2 (z-led, 10 cm)'),
        ('EE2', 10.0, 'tvärbalk E → E2 (z-led, 10 cm)'),
        ('FF2', 10.0, 'tvärbalk F → F2 (z-led, 10 cm)'),
        ('GG2', 10.0, 'tvärbalk G → G2 (z-led, 10 cm)'),
        # Apex-trianglar: D respektive H är spetsar som binder samman planen
        # 3D-längd = sqrt(2D-längd² + 10²)
        ('DB2',  42.69, 'apex-stång D → B2 (=√(41.5² + 10²))'),
        ('DE2',  56.69, 'apex-stång D → E2 (=√(55.8² + 10²))'),
        ('HF2',  50.01, 'apex-stång H → F2 (=√(49.0² + 10²))'),
        ('HG2',  66.46, 'apex-stång H → G2 (=√(65.7² + 10²))'),
    ]
    
    for name, length_cm, desc in leg_links:
        length_mm = length_cm * SCALE * 10
        parts.append({
            'kategori': 'Ben',
            'namn': f'ben_{name}',
            'antal': 4,
            'langd_full_cm': length_cm,
            'langd_skala_mm': length_mm,
            'tjocklek_mm': 3.0,
            'bredd_mm': 6.0,
            'olja_diam_mm': 10.0,
            'antal_hal': 2,
            'beskrivning': desc,
        })
    
    # === VEVSKIVOR ===
    parts.append({
        'kategori': 'Vevenhet',
        'namn': 'vevskiva',
        'antal': 2,
        'langd_full_cm': '',
        'langd_skala_mm': 'Ø70',
        'tjocklek_mm': 4.0,
        'bredd_mm': '',
        'olja_diam_mm': '',
        'antal_hal': 3,
        'beskrivning': 'cirkulär skiva R=35mm, hål för axel (centrum) + 2 vevtappar 180° förskjutna vid R=30mm',
    })
    
    # === PEDALVEV ===
    parts.append({
        'kategori': 'Vevenhet',
        'namn': 'pedalvev',
        'antal': 1,
        'langd_full_cm': '',
        'langd_skala_mm': 'Ø44',
        'tjocklek_mm': 4.0,
        'bredd_mm': '',
        'olja_diam_mm': '',
        'antal_hal': 3,
        'beskrivning': 'cirkulär skiva R=22mm, hål för axel + 2 pedaltappar vid R=17mm',
    })
    
    # === RAMLÄNKAR ===
    ram_links = [
        ('PQ', nodes['P'], nodes['Q'], nodes['A_rear'],
         'vertikal stolpe pedalvev→sadel; M5-hål för bakre vevaxel i mitten'),
        ('A_rear-B_rear', nodes['A_rear'], nodes['B_rear'], None,
         'bakvevaxel till bakbens fasta led'),
        ('P-B_rear', nodes['P'], nodes['B_rear'], None,
         'diagonal stagning från pedalvev'),
        ('A_rear-A_front', nodes['A_rear'], nodes['A_front'], None,
         'huvudbalk mellan vevaxlarna'),
        ('A_front-B_front', nodes['A_front'], nodes['B_front'], None,
         'framvevaxel till frambens fasta led'),
        ('P-M', nodes['P'], nodes['M'], None,
         'del 1 av lång stagning'),
        ('M-B_front', nodes['M'], nodes['B_front'], None,
         'del 2 av lång stagning'),
        ('A_front-M', nodes['A_front'], nodes['M'], None,
         'fackverkstag'),
        ('B_front-H', nodes['B_front'], nodes['H'], None,
         'styraxel från B_front upp till handtag'),
    ]
    
    for name, p1, p2, mid_node, desc in ram_links:
        length_cm = np.linalg.norm(p2 - p1)
        length_mm = length_cm * SCALE * 10
        n_holes = 2 if mid_node is None else 3
        if mid_node is not None:
            t = np.dot(mid_node - p1, p2 - p1) / np.dot(p2 - p1, p2 - p1)
            mid_x_mm = t * length_mm
            desc = desc + f' (extra hål Ø5mm vid x={mid_x_mm:.1f}mm)'
        
        parts.append({
            'kategori': 'Ram',
            'namn': f'ram_{name}',
            'antal': 1,
            'langd_full_cm': length_cm,
            'langd_skala_mm': length_mm,
            'tjocklek_mm': 5.0,
            'bredd_mm': 8.0,
            'olja_diam_mm': 12.0,
            'antal_hal': n_holes,
            'beskrivning': desc,
        })
    
    # === FÖRARDELAR ===
    rider_segments = [
        ('bal', rider.hip, rider.shoulder, 'bål: höft till axel'),
        ('huvud', None, None, 'huvud: skiva R=13mm, ett centrumhål'),
        ('overarm_vanster', rider.shoulder, rider.elbow, 'vänster axel till armbåge'),
        ('underarm_vanster', rider.elbow, rider.hand, 'vänster armbåge till hand'),
        ('overarm_hoger', rider.shoulder, rider.elbow, 'höger axel till armbåge'),
        ('underarm_hoger', rider.elbow, rider.hand, 'höger armbåge till hand'),
        ('lar_vanster', rider.hip, rider.knee_left, 'vänster höft till knä'),
        ('underben_vanster', rider.knee_left, rider.foot_left, 'vänster knä till fot'),
        ('lar_hoger', rider.hip, rider.knee_right, 'höger höft till knä'),
        ('underben_hoger', rider.knee_right, rider.foot_right, 'höger knä till fot'),
    ]
    
    for name, p1, p2, desc in rider_segments:
        if p1 is None:
            length_cm = ''
            length_mm = 'Ø26'
            n_holes = 1
        else:
            length_cm = np.linalg.norm(p2 - p1)
            length_mm = length_cm * SCALE * 10
            n_holes = 2
        parts.append({
            'kategori': 'Förare',
            'namn': f'forare_{name}',
            'antal': 1,
            'langd_full_cm': length_cm,
            'langd_skala_mm': length_mm if isinstance(length_mm, str) else length_mm,
            'tjocklek_mm': 5.0,
            'bredd_mm': 5.0,
            'olja_diam_mm': 10.0,
            'antal_hal': n_holes,
            'beskrivning': desc,
        })
    
    parts.append({
        'kategori': 'Förare',
        'namn': 'forare_fot',
        'antal': 2,
        'langd_full_cm': '',
        'langd_skala_mm': 30.0,
        'tjocklek_mm': 5.0,
        'bredd_mm': 5.0,
        'olja_diam_mm': 10.0,
        'antal_hal': 1,
        'beskrivning': 'fot: kort plattlänk med ett hål för pedaltapp',
    })
    
    return parts


def format_value(v):
    """Formattera värde för tabell."""
    if isinstance(v, float):
        return f'{v:.1f}'
    return str(v)


def write_text_table(parts, filename):
    """Skriv tabell som tydlig textfil."""
    headers = [
        ('kategori',         'Kategori',       10),
        ('namn',             'Namn',           28),
        ('antal',            'Ant',            4),
        ('langd_full_cm',    'L full(cm)',     11),
        ('langd_skala_mm',   'L 1:5(mm)',      10),
        ('tjocklek_mm',      'Tj(mm)',         7),
        ('bredd_mm',         'Br(mm)',         7),
        ('olja_diam_mm',     'Ölja(mm)',       9),
        ('antal_hal',        'Hål',            4),
        ('beskrivning',      'Beskrivning',    60),
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 150 + "\n")
        f.write("SPRINGCYKEL — KOMPONENTLISTA I SKALA 1:5\n")
        f.write("=" * 150 + "\n\n")
        f.write("Designparametrar:\n")
        f.write("  Skala: 1:5 (alla mått × 0.2)\n")
        f.write("  M3-hål: Ø3.2 mm (radie 1.6 mm)\n")
        f.write("  Benstänger: 3 mm tjocka, 6 mm breda, ölja Ø10 mm\n")
        f.write("  Ramstänger: 5 mm tjocka, 8 mm breda, ölja Ø12 mm\n")
        f.write("  Förardelar: 5 × 5 mm tvärsnitt, ölja Ø10 mm\n")
        f.write("\n")
        
        # Header
        line = ''
        for key, label, width in headers:
            line += f'{label:<{width}} '
        f.write(line + '\n')
        f.write('-' * 150 + '\n')
        
        # Data
        current_kategori = None
        for p in parts:
            if p['kategori'] != current_kategori:
                if current_kategori is not None:
                    f.write('\n')
                current_kategori = p['kategori']
            
            line = ''
            for key, label, width in headers:
                v = format_value(p[key])
                if len(v) > width - 1:
                    v = v[:width-1]
                line += f'{v:<{width}} '
            f.write(line + '\n')
        
        # Summering
        f.write('\n' + '=' * 150 + '\n')
        total_count = sum(p['antal'] for p in parts)
        f.write(f'TOTALT ANTAL DELAR ATT TILLVERKA: {total_count}\n')
        f.write('=' * 150 + '\n\n')
        
        f.write("MONTERINGSANVISNINGAR:\n")
        f.write("- M3-skruvar fungerar som pivot-pinnar för alla leder.\n")
        f.write("- För ramnoder med >2 ankommande stänger: stapla stängerna i ordning\n")
        f.write("  på samma M3-skruv, eventuellt med tunna brickor mellan.\n")
        f.write("- Vid PQ-länken: borra extra hål Ø5 mm vid angiven position för\n")
        f.write("  bakre vevaxel (denna går igenom stolpen, inte i en led).\n")
        f.write("- Vevaxlarna: M5 eller likn. grövre axel som går genom vevskiva\n")
        f.write("  och PQ-stolpen vid A_rear, och genom huvudbalken vid A_front.\n")
        f.write("- Vevtappar och pedaltappar: M3-skruvar genom skivornas yttre hål.\n")
        f.write("- Lederna ska vara fritt vridbara — undvik att dra åt skruvarna helt.\n")
        f.write("\n")
        f.write("3D-FACKVERK PER BEN (sidostyvhet):\n")
        f.write("- Noderna B, E, F, G dupliceras till z2-planet 10 cm inåt mot ramen.\n")
        f.write("- Tvärbalkarna BB2/EE2/FF2/GG2 är 10 cm långa stänger som förbinder\n")
        f.write("  leden i z1 med motsvarande i z2 (parallellt med ramen).\n")
        f.write("- Stängerna B2E2/B2F2/E2G2/F2G2 utgör en kopia av topologin BEFG i\n")
        f.write("  z2-planet — de har samma längder som motsvarigheter i z1.\n")
        f.write("- D-leden i z1 binds samman med B2 och E2 via apex-stängerna DB2/DE2,\n")
        f.write("  som bildar triangeln D-B2-E2 tillsammans med B2E2.\n")
        f.write("- H-foten i z1 binds samman med F2 och G2 via HF2/HG2 — triangeln\n")
        f.write("  H-F2-G2 tillsammans med F2G2.\n")
        f.write("- B-axeln (M5) går genom hela ramen→B1→B2-linjen och tar upp\n")
        f.write("  sidobelastning för båda B-lederna.\n")
        f.write("- Vid B-leden: B-axeln + stängerna BD, BE, BF, BB2 möts (5 element).\n")
        f.write("  Vid B2-leden: B-axeln + B2E2, B2F2, BB2, DB2 möts (5 element).\n")
        f.write("  Använd lite längre M3-skruv och brickor mellan stängerna.\n")


def write_csv_table(parts, filename):
    """Skriv som CSV för Excel/Tinkercad."""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'kategori', 'namn', 'antal',
            'langd_full_cm', 'langd_skala_mm',
            'tjocklek_mm', 'bredd_mm', 'olja_diam_mm',
            'antal_hal', 'beskrivning'
        ])
        writer.writeheader()
        for p in parts:
            writer.writerow(p)


if __name__ == '__main__':
    parts = build_parts_list()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.normpath(os.path.join(script_dir, '..', 'docs'))
    text_file = os.path.join(docs_dir, 'komponentlista.txt')
    csv_file = os.path.join(docs_dir, 'komponentlista.csv')
    
    write_text_table(parts, text_file)
    write_csv_table(parts, csv_file)
    
    print(f"Komponentlista sparad som:")
    print(f"  {os.path.abspath(text_file)}")
    print(f"  {os.path.abspath(csv_file)}")
    print(f"\nTotalt antal delar: {sum(p['antal'] for p in parts)}")
