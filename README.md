# Springcykel

En pedaldriven fyrbent ridbar maskin baserad på Theo Jansens benmekanism.
Konstprojekt och tekniskt utforskande.

Se [docs/whitepaper.md](docs/whitepaper.md) för fullständig designbeskrivning.

## Katalogstruktur

```
springcykel/
├── python/      Kinematik och geometri-export
├── web/         Interaktiv 3D-visualisering (Three.js)
└── docs/        Whitepaper och genererade artefakter
```

## Installation

Python-beroenden:

```
pip install -r requirements.txt
```

Eller i virtuell miljö (rekommenderas):

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3D-visualiseringen behöver inga beroenden installerade lokalt — Three.js
laddas via CDN vid sidladdning.

## Köra 3D-visualiseringen

Visualiseringen behöver en lokal webbserver (inte file://) eftersom
JS-modulerna hämtar `machine_geometry.json` via fetch.

```
cd web/
python3 -m http.server 8000
```

Öppna sedan http://localhost:8000/

## Regenerera geometri

Efter ändringar i Python-modellen:

```
python3 python/export_geometry.py     # → web/machine_geometry.json
python3 python/komponentlista.py      # → docs/komponentlista.{txt,csv}
python3 python/export_stl.py          # → docs/stl/*.stl (för 3D-print)
```

Scripten kan köras från valfri katalog — sökvägar löses relativt
scriptens egen position.

## Arkitektur i korthet

Tre lager med tydligt ansvar:

- **Python** äger all numerisk geometri (dimensioner, vinklar, Jansen-konstanter).
  `jansen.py` är ren matematik. `machine.py` lägger till ram och förare.
  `machine3d.py` utvidgar till 3D. `export_geometry.py` skriver ut allt
  till JSON.
- **JSON** (`machine_geometry.json`) är överlämningsformatet. Inga
  beräkningar lever här.
- **JavaScript** ansvarar för rendering, IK, animation och UI. Läser
  JSON via fetch vid sidladdning.

Regeln är: *tal hör hemma i Python, form och animation hör hemma i JS*.
Detta ger en enda sanning för varje siffra.

## Licens

- **Kod** (`*.py`, `*.js`, `*.html`): MIT, se [LICENSE-CODE](LICENSE-CODE)
- **Design och dokumentation** (whitepaper, JSON-data, eventuella ritningar):
  CC BY-SA 4.0, se [LICENSE-DOCS](LICENSE-DOCS)
