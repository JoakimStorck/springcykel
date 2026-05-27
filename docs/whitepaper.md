**Springcykel**

*En pedaldriven fyrbent ridbar maskin*

Designdokument och teknisk specifikation

*Version 3.0 — 27 maj 2026*

# Sammanfattning

Springcykeln är en pedaldriven fyrbent ridbar maskin som ersätter cykelhjul med fyra identiska benmekanismer baserade på Theo Jansens linkage. Maskinen är dimensionerad för en förare på 140–210 cm och rör sig som en gångmaskin snarare än rullande, med en framdriftshastighet på omkring 6 km/h vid normal trampfrekvens och upp till 12 km/h vid hög. Projektet är ett konstnärligt och tekniskt utforskande av vad som händer när cykelns rotationsbaserade framdrift ersätts med Jansens karakteristiska gångrörelse.

Detta dokument beskriver designval, ergonomiska överväganden, mekaniska lösningar och ekonomiska aspekter. Projektet är medvetet hållet öppet och fritt för andra att bygga vidare på, i samma anda som Theo Jansen själv valt för sin mekanism.

# Konceptet

## Bakgrund

Theo Jansens benmekanism (1990) är en elvalänkig konstruktion som omvandlar axelrotation till en stegande rörelse. Mekanismen har en karakteristisk stödfas där foten rör sig längs en nästan rak horisontell linje — vilket ger en stabil och energieffektiv gångrörelse över ojämn mark.

Jansens egna Strandbeesten är vinddrivna och autonoma. Sedan dess har flera konstnärer och makers byggt pedaldrivna varianter — bland andra Adam Savage (2016, San Francisco Exploratorium), JP:s Strandbeest Bicycle (2016), Panterragaffe (Vancouver Maker Faire 2011), CARV Walking Bicycle (2019) och Pedaalbeest (Aat Dirks & Ad Lakerveld). Springcykeln tar plats i denna tradition men med flera egna val.

## Unika designval

Det som skiljer Springcykeln från tidigare ridbara Jansen-maskiner:

- Fyra fysiskt identiska ben (mot tidigare maskiners ofta asymmetriska sex- eller åttabens-konfigurationer)
- Två separata vevpartier (fram/bak) i trav (180° fasförskjutning), vilket ger ett naturligt fyrbent gångmönster
- 3D-fackverkskonstruktion av benen — varje ben är ett tredimensionellt fackverk snarare än en plan länkmekanism, för sidostabilitet vid kurvkörning
- Triangelstöd och teleskop ankrar mitt på benets B-axel (z=±10 cm), vilket eliminerar vridmoment vid B-leden
- Styrning via asymmetrisk kammekanism som förlänger AB-länken på inre sidan i en sväng, vilket ger differentiell steglängd
- Styret roterar mekaniskt med styrutslag — upp till ±60° vid maximalt slag — och föraren följer med via koordinerad rörelse av armar och torso
- Ergonomisk sittposition beräknad så att benens vinklar vid pedalens lägsta läge är cirka 95 % av maxutsträckning — anpassat för förarlängd
- Komplett kinematisk simuleringsmodell med interaktiv 3D-visualisering, inklusive 3D-IK för föraren med abduktion från höften, samt rörlig mark som visar både framdrift och sväng

# Mekanisk design

## Benmekanismen

Varje ben följer Jansens originalproportioner (de "heliga talen") för de elva grundlänkarna:

| Länk | Längd (cm) |
| --- | --- |
| AC (vev) | 15.0 |
| CD | 50.0 |
| BD | 41.5 |
| DE | 55.8 |
| BE | 40.1 |
| CF | 61.9 |
| BF | 39.3 |
| EG | 39.4 |
| FG | 36.7 |
| FH (fot) | 49.0 |
| GH | 65.7 |

Mekanismen producerar följande karakteristik i grundutförande:

- Steglängd per vevvarv: 67.91 cm
- Fotlyftning över mark: 22.46 cm
- Stödfas: 68 % av cykeln (foten på marken)
- Avstånd vevcentrum till mark: 91.83 cm

## 3D-fackverk för sidostabilitet

En plan Jansen-mekanism — alla elva stänger i samma plan — är i praktiken inte tillräckligt stabil i sidled för en ridbar maskin. Föraren genererar kraftiga sidolaster vid acceleration, inbromsning och inte minst vid lutning i kurva. Ett plant ben tål inte detta utan att vrida sig.

Lösningen är att göra varje ben till en tredimensionell fackverkskonstruktion. Fyra av Jansens leder — B, E, F och G — dupliceras till ett *sekundärplan* förskjutet 10 cm från det ursprungliga planet. Det ursprungliga planet ligger 15 cm ut från ramens mitt på varje sida (z = ±15 cm); sekundärplanet ligger 5 cm ut (z = ±5 cm), alltså inåt mot ramen. Detta ger:

- Ursprungliga planet (z1): elva Jansen-stänger som driver kinematiken
- Sekundärplanet (z2): fyra stänger (B2–E2, B2–F2, E2–G2, F2–G2) som speglar fyrhörningen B–E–F–G i z1
- Tvärbalkar i z-led: fyra korta stänger (B–B2, E–E2, F–F2, G–G2) som binder samman planen
- Apex-trianglar: ledderna D och H förbinds till sekundärplanet via stängerna D–B2, D–E2, H–F2 och H–G2 — vilket bildar två trianglar (D-B2-E2 och H-F2-G2) som tar upp vridmoment

Totalt 23 stänger per ben istället för 11, alltså 92 benstänger för hela maskinen. Sekundärplanet bidrar inte till kinematiken — B2, E2, F2 och G2 följer rent passivt med sina motsvarigheter i z1-planet, förskjutna i z. Den enda funktionen är strukturell.

Konstruktionen påminner i form om en fackverkbro där två parallella plan binds samman med tvärbalkar och diagonaler. För benens dimensioneringsproblem är fördelarna betydande: vridstyvhet kring benets längdaxel, böjstyvhet i z-led, och redundans om en stång skulle skadas.

## Ram

Ramen är en symmetrisk konstruktion av rörstänger med sidoramar vid z=±10 cm — alltså **mitt på** benets B-axel som spänner från B1 vid z=±15 till B2 vid z=±5. Att placera triangelstödet och styrteleskopet i samma plan som B-axelns mittpunkt eliminerar det vridmoment som annars skulle uppstå om kraften togs upp asymmetriskt längs axelns längd.

### Ramnoder

Ramen består av följande noder:

| Nod | x (cm) | y (cm) | z (cm) |
| --- | --- | --- | --- |
| A_front_left | 50 | 91.83 | -10 |
| A_front_right | 50 | 91.83 | +10 |
| A_front (central) | 50 | 91.83 | 0 |
| A_rear_left | 0 | 91.83 | -10 |
| A_rear_right | 0 | 91.83 | +10 |
| A_rear (central) | 0 | 91.83 | 0 |
| P_left | 0 | 50 | -10 |
| P_right | 0 | 50 | +10 |
| M_left | 44 | 62.0 | -10 |
| M_right | 44 | 62.0 | +10 |
| Q (sadelstolpens topp) | 0 | 113 | 0 |
| N (styraxelns fästpunkt) | 50 | 108.83 | 0 |
| H (styrets centrum) | 50 | 124 | 0 |

A-noderna ligger vid vevaxlarnas centrum. P är pedalvevaxelns mittpunkt. M är frambenens kam/triangelstödets pivotpunkt. Q, N och H är centrala (z=0) eftersom de hör till sadel och styre som ligger på maskinens mittlinje.

### Ramlänkar

Ramen är **y-formad** sett uppifrån: centrala noderna A_front och A_rear (vid z=0) tar upp diagonalstagen från P och M på båda sidor, vilket ger en strukturellt enkel men styv konstruktion.

Per sida finns två länkar (vertikalt och snett framåt):

- A_rear ↔ P (vertikal stötta från bakvevaxel till pedalvevaxel)
- M ↔ A_front (snett framåt från frambenens M-pivot till framvevaxel)

Centrala stag (från sidonoderna till central nod):

- A_rear ↔ A_front (central balk längs maskinens mittlinje)
- A_rear ↔ M_left och A_rear ↔ M_right
- P_left ↔ A_front och P_right ↔ A_front

Tvärbalkar mellan sidorna, en per nod:

- A_front_left ↔ A_front_right
- A_rear_left ↔ A_rear_right
- P_left ↔ P_right
- M_left ↔ M_right

Styre och sadel:

- A_front_left ↔ N och A_front_right ↔ N (styraxelns nedre fästpunkt)
- N ↔ H (styrstolpen — roterar med styret, se nedan)

Sadelstolpen (från A_rear-tvärbalkens mitt upp till sadeln) byggs dynamiskt eftersom dess längd beror på vald sadelhöjd.

## Vevaxlar och drivlina

Tre vevaxlar lagras i sidoramen (z=±10):

- **Pedalvevaxeln** vid (0, 50). Lagring vid z=±10. Vevarmen sitter *utanpå* sidoramen vid z=±12, med 2 cm tjocklek. Pedaltappen sticker ut 10 cm i z-led från vevarmen, alltså från z=±12 till z=±22. Pedalplattans centrum ligger vid z=±17 där föraren har sin fot.
- **Bakvevaxeln** vid (0, 91.83). Sträcker sig till z=±15 där benets C-punkt ankrar på vevarmen.
- **Framvevaxeln** vid (50, 91.83). Samma princip som bakvevaxeln.

Pedalvevaxelns dimensionering — vevarm utanpå ramen, tapp 10 cm — ger föraren fri svängrum för foten utan att benet är i vägen. Att lagringen sitter i sidoramen och vevarmen utanpå är samma princip som på en konventionell cykel.

Drevet på pedalvevaxeln är 4 cm i radie; drevet på fram- och bakvevaxlarna är 10 cm — vilket ger en utväxling 1:2.5 från pedalen till benen. Två kedjor överför rotation från pedalvevaxeln till respektive bens-vevaxel.

## Styrning

Styrning sker via *differentiell steglängd*: inre sidan av maskinen tar kortare steg än yttre sidan i en sväng, vilket vrider maskinen kring ett centrum mellan benen. Mekanismen utnyttjar att Jansens benkinematik är känslig för positionen av B-leden — en förlängning av AB-länken (avståndet från vevaxel till benets B-fästpunkt) på ena sidan av maskinen ger där kortare steg, medan motsatta sidan förblir oförändrad.

### Styrvinkel och utslag

Styret kan vridas upp till ±60° från neutralläge. Vinkeln mappas linjärt till AB-förlängning:

| Styrvinkel | AB-offset på inre sida | Steglängd inre | Karaktär |
| --- | --- | --- | --- |
| 0° | 0 cm | 67.9 cm | Rakt fram |
| ±15° | 1 cm | 66.4 cm | Mjuk sväng |
| ±30° | 2 cm | 64.8 cm | Normal sväng |
| ±45° | 3 cm | 63.1 cm | Tightare sväng |
| ±60° | 4 cm | 61.4 cm | Max utslag |

Vid maxutslag är steglängdsasymmetrin 6.5 cm vilket vid 30 cm spårvidd ger en svängradie omkring 3 m. Det är inom körfältsbredd för normal cykelväg.

### Asymmetrisk justering

Mekanismens arbetsområde är begränsat av Jansens kinematik. Simulering av fotbanan för olika AB-längder visar:

| AB-justering | Steglängd | Fotlyft | Anmärkning |
|---|---|---|---|
| −1 cm | 69.4 cm | 65.7 cm | Gångarten förstörd |
| 0 cm | 67.9 cm | 22.5 cm | Baseline |
| +1 cm | 66.4 cm | 15.4 cm | |
| +2 cm | 64.8 cm | 11.6 cm | |
| +3 cm | 63.1 cm |  9.2 cm | |
| +4 cm | 61.4 cm |  8.6 cm | Designgräns |
| +7 cm | 56.3 cm | 13.4 cm | Brytpunkt (Jansen kollapsar) |

Förkortning av AB är teoretiskt möjlig men praktiskt obrukbar: mekanismen tappar sin karakteristiska gång redan vid −0.5 cm. Designen tillåter därför endast *förlängning* av AB. Yttre sidan i en sväng står kvar vid baseline (offset 0); inre sidan ökar upp till +4 cm.

### Triangelmekanism för B-leden

Direkt translation av B i x-led är mekaniskt komplicerat — B-axeln skulle behöva glida i x-led samtidigt som den bär böjnings- och vridkrafter från benen, vilket kräver kostsamma glidlagringar. Lösningen är en *triangelmekanism* där en av sidorna är teleskopisk:

- **Bakben:** triangeln A_rear—P—B_rear. Sidan A_rear→B_rear teleskoperas längs sin egen axel; sidan P→B_rear behåller fast längd 51.0 cm och har ett gångjärn vid P. När teleskopet förlängs vandrar B_rear i en cirkulär båge kring P.
- **Framben:** motsvarande triangel A_front—M—B_front. Sidan A_front→B_front teleskoperas; sidan M→B_front behåller fast längd 49.2 cm med gångjärn vid M.

Triangelstödet och teleskopet ligger vid z=±10 — alltså mitt på B-axeln som spänner från B1 (z=±15) till B2 (z=±5). Denna symmetriska infästning eliminerar det vridmoment som annars skulle uppstå om kraften togs upp asymmetriskt.

Triangelgeometrin löser belastningsproblemet: teleskopet utsätts endast för axiell kraft längs AB, eftersom alla sidolaster tas upp av den fasta P→B-stången (eller M→B-stången för frambenet) via gångjärnet. Inga vridmoment, ingen böjning, ingen glidning vinkelrätt mot teleskopets axel.

### Kamprofil

Aktuering av teleskopet sker via en kam (kamskiva med profilerad nock) monterad på en kamaxel som sitter på ramen. Kammens periferi pressar mot teleskopets inre rör, och en returfjäder håller följaren mot kammen samt återställer baseline-läget när styret släpps.

Kamprofilen designas asymmetriskt så att kammen bara är aktiv åt ett håll:

- Vid kamvinkel 0° (mittläge, styret rakt): följaren pressar inte teleskopet — AB är vid baseline 38.79 cm.
- Vid kamvinkel +α (styrutslag åt kammens aktiva sida): följaren pressas successivt utåt, AB förlängs upp till +4 cm vid maxutslag.
- Vid kamvinkel −α (motsatt utslag): kammen har en platt sektor — följaren rör sig inte. AB förblir baseline.

Vänster sidas kam aktiveras vid vänstersväng; höger sidas vid högersväng. I rakt läge är båda kammarna i vilolägets platta sektor.

### Två kamaxlar driver fyra ben

Fram- och bakbenen på samma sida ska justeras tillsammans — annars divergerar deras steglängder och maskinen vrider sig okontrollerbart kring en vertikal axel. En naturlig lösning är att låta en gemensam kamaxel löpa längs ramens sida med två kammar — en vid varje ben. Då har maskinen totalt två kamaxlar (vänster och höger), inte fyra separata kammar.

Styret kopplas till de två kamaxlarna via en länkmekanism som driver dem åt motsatta håll: vid vänstersväng vrids vänster axels kammar in i sin aktiva sektor, höger axels kammar förblir i vilo (och vice versa).

### Biverkning: fotlyft på inre sida

En konsekvens av Jansens kinematik är att fotbanan inte bara *krymper* horisontellt vid AB-förlängning — den *lyfts* också vertikalt. Vid maxutslag når inre fötter inte längre marken om maskinen hålls upprätt:

| Ben | Fotbanans lägsta punkt över vevcentrum | Lyft från marken |
|---|---|---|
| Framben | 100.0 cm | 8.2 cm |
| Bakben | 96.9 cm | 5.0 cm |

För balansens skull måste föraren luta maskinen inåt i sin sväng, precis som en cyklist gör för att kompensera för centripetalaccelerationen. När maskinen lutar inåt sänks inre sidan och inre fötter återställer markkontakt automatiskt. Vid 4 cm AB-offset kräver fullständig markåterställning ungefär 15° lutning för frambenet, ~10° för bakbenet — inom samma lutningsintervall som en cyklist använder i en lugn kurva.

# Ergonomi

## Förarens anpassning

Maskinen är dimensionerad för en förare på 194 cm men anpassningsbar i intervallet 140–210 cm via två justeringar:

- Sadelhöjd: justerbar 106–140 cm från marken via sadelstångens position
- Förarens horisontella sittposition på sadeln (x-position) varierar beroende på förarens längd och vald sadelhöjd

## Ergonomiska målsättningar

Två huvudkriterier styr förarens placering:

- **Benens utsträckning:** vid pedalens lägsta position ska benet vara utsträckt till 95 % av maxlängden. Detta motsvarar 25–35° knäböj — den ergonomiskt rekommenderade vinkeln för cykling som skyddar knäna från överbelastning samtidigt som det ger god kraftöverföring.
- **Armarnas position:** överarmen ska vinkla framåt från axeln för att handen ska nå styret naturligt. Bålen lutar 15–30° framåt beroende på proportioner.

## 3D-IK med abduktion från höften

Eftersom pedaltappen sticker ut till z=±17 — utanför maskinens ramplan — kan föraren inte sitta med benen rakt nedhängande. Lösningen är ergonomiskt vald: föraren abducerar benen lätt från höften, så att låret pekar något snett utåt mot pedalen, knäet hamnar något utåt, och foten landar på pedalplattan.

Vid normal sittposition (höft ungefär 9 cm från mittlinjen, pedalplatta vid 17 cm) blir abduktionsvinkeln cirka 7° — en mild lutning som motsvarar vad cyklister gör när pedalerna är något bredare än höften.

Algoritmen för 3D-IK börjar med fotens önskade världs-position och räknar baklänges:

1. **Abduktionsvinkel** (lateral lutning av låret) från höft till fot i ett vertikalt plan som innehåller båda
2. **Framåt-vinkel** (höftens roll) i det laterala plan som benet nu pekar mot
3. **Knäböjning** via lagen om cosinus baserat på 3D-avståndet höft-fot

Detta gör att benets vinklar alltid är geometriskt korrekta för fotens position.

## Sadelns form

Sadeln är 45 cm lång (x=-15 till x=30 från ramens bakvevaxel). Formen är fast:

- Sittpunkt vid x=25 (sadelns lägsta y-koordinat)
- Bakdel vid x=0: alltid 11 cm högre än sittpunkten
- Mjuk båge mellan x=0 och x=25 via cosinus-interpolation
- Sadelns bredd taperar från 12 cm bak till 8 cm fram
- Konkavitet (sadeldipp): 1.5 cm vid sittpunkten

Bakdelens högre position gör att sadeln kröker sig över bakvevaxeln och ger högre sittposition för långa förare som behöver mer benutrymme.

## Styrning och kroppsvridning

När föraren vrider styret följer hela överkroppen med på ett koordinerat sätt:

- **Styret roterar** kring styrstolpens vertikala axel (genom N och H) med upp till ±60°
- **Händerna följer handtagen** automatiskt eftersom föraren håller i dem (IK-mål för armarna är handtagens nuvarande världs-position)
- **Armarna anpassar sig** via 3D-IK — vid stora utslag sträcker sig den ena armen ut och den andra böjs in
- **Torsen vrider sig** proportionellt mot styrvinkeln: bröstkorgen 35 %, magen 10 %, huvudet 15 % — totalt cirka 27° vridning av övre kroppen vid maxutslag

Detta speglar hur en cyklist faktiskt rör sig — det är inte bara armarna som tar utslaget, hela kroppen följer med.

# Prestanda

## Trampfrekvens och framdriftshastighet

Vid utväxling 1:2.5 och steglängd 67.91 cm per vevvarv blir framdriftens hastighet som funktion av trampfrekvens (pedal-rpm):

| Trampfrekvens (rpm) | Vevvarv per minut | Framdrift (km/h) | Karaktär |
| --- | --- | --- | --- |
| 10 | 25 | 1.0 | Långsamt skritt |
| 20 | 50 | 2.0 | Mycket långsam |
| 40 | 100 | 4.1 | Normal promenad |
| 60 | 150 | 6.1 | Rask promenad |
| 90 | 225 | 9.2 | Långsam jogg |
| 120 | 300 | 12.2 | Jogg |

UI-modellens slider tillåter trampfrekvens från 10 till 120 rpm, med default 10 rpm för säker uppstart.

Detta är gång- till joggfart — långsamt i jämförelse med en konventionell cykel, men förväntat för en gångmaskin. Den långsamma hastigheten är delvis en konsekvens av att fötterna måste lyftas och sänkas vid varje steg, vilket är mindre energieffektivt än rullande hjul men ger förmåga att klara ojämn terräng som hjul inte kan.

## Visualiseringsmodell

Modellens 3D-visualisering återger maskinens rörelse genom rummet:

- **Markens rutmönster rör sig** under maskinen — vid rak körning sopar mönstret bakåt med hastighet som motsvarar beräknad framdrift; vid sväng roterar marken runt svängcentrum med vinkelhastighet som motsvarar svängradien.
- **Styret roterar mekaniskt** med styrutslaget och förarens kropp följer med (se Ergonomi ovan).
- **Förarens fötter spårar pedalerna** exakt med 3D-IK genom hela trampcykeln.

## Kraftöverföring och begränsningar

Maximal kontinuerlig kraft från en tränad cyklist är cirka 150–250 W. Vid 6 km/h motsvarar detta ungefär 90–150 N drivkraft, vilket vid lätt marklutning bör vara tillräckligt för framdrift. För backar krävs antingen mer kraft (kortare körtid) eller assistans.

# Materialval och konstruktion

## Ramen

Förslag på material för ramkonstruktionen:

| Komponent | Material | Motivering |
| --- | --- | --- |
| Ramrör (huvuddel) | Stål 25CrMo4 eller 4130 | Hög hållfasthet, lättsvetsat, beprövat |
| Sadelstång och styrstam | Aluminium 7075-T6 | Lägre vikt på höga punkter |
| Benen (fackverk) | Aluminium 7075-T6 eller stål 25CrMo4 | Många stänger; aluminium ger viktreduktion, stål bättre svetsbarhet |
| Vevaxlar | Härdat stål | Hög rotationsbelastning |
| Lagerhus | Standard cykellager | Massproducerat |
| Drev och kedjor | Cykelstandard | Tillgängligt och billigt |
| Pedaler | Aluminium med gummigrepp | Standardpedal |
| Styrkam och kamaxel | Härdat stål | Hög punktbelastning, slitage |
| Teleskopstång (AB) | Stål med splines eller passnings-tolerans | Axiell glidning, vridning ej tillåten |

3D-fackverket gör benen mer komplexa att tillverka men varje enskild stång är fortfarande en rak rörbit med två (i några fall tre) hål. Hålbilden kan CNC-fräsas i serier för konsekvent montering.

## Vikt och dimensioner

Uppskattad totalvikt (grov estimat):

- Ram (stål): 12–18 kg
- Fyra ben (komplett 3D-fackverk): 22–32 kg (5.5–8 kg per ben)
- Vevaxlar, lager, dreva, kedjor: 4–6 kg
- Styrmekanism (kammar, kamaxlar, teleskop, returfjädrar): 2–4 kg
- Sadel, styre, mindre komponenter: 2–3 kg
- Totalt: 42–63 kg

Detta är betydligt tyngre än en cykel (8–15 kg). Vikten ligger lågt (vevarmar och ben), vilket ger god stabilitet. För att hålla nere vikten är aluminium på benen ett intressant alternativ till stål — kostnaden är högre men kan motiveras av den dynamiska viktbesparingen.

# Ekonomi

## Materialkostnader

Uppskattade materialkostnader för en enskild prototyp byggd i Sverige (2026 års prisnivå, inklusive moms):

| Post | Uppskattad kostnad (SEK) |
| --- | --- |
| Stålrör (25CrMo4 eller likn.) för ram | 3 000–6 000 |
| Aluminiumrör för sadelstång/styrstam | 500–1 000 |
| Stångmaterial för ben (92 stänger i 3D-fackverk) | 8 000–16 000 |
| Vevaxlar (3 st, härdat stål) | 2 000–4 000 |
| Lager (cykelstandard, ~20 st) | 1 500–3 000 |
| Dreva och kedjor | 1 500–2 500 |
| Pedaler och cyklist-standardkomponenter | 500–1 000 |
| Sadel (anpassad, eventuellt 3D-printad form) | 1 000–3 000 |
| Styre och styrlänkar | 500–1 500 |
| Styrmekanism (kammar, axlar, teleskop, fjädrar) | 2 000–5 000 |
| Lager, bultar, distanser, småmaterial | 2 000–4 000 |
| Lack/ytbehandling | 500–1 500 |
| Summa material | 23 000–48 500 |

## Arbete och tid

Tidsuppskattning för en kvalificerad verkstad/byggare:

- Mekanisk konstruktion (skär, böj, svetsa stål): 80–120 timmar
- Bensystem (92 stänger i 3D-fackverk med exakta hålbilder): 80–120 timmar
- Styrmekanism (kammar, kamaxlar, teleskopkoppling, länkar): 30–50 timmar
- Montering, justering, intrimning: 40–60 timmar
- Lack, ytbehandling, finishing: 10–20 timmar
- Totalt arbete: 240–370 timmar

Vid en verkstadstaxa på 750–1 200 SEK/h blir arbetskostnaden 180 000 – 440 000 SEK. För egen byggnad i hemverkstad eller kollektivt makerspace (där tiden är "fritid") sjunker den faktiska kostnaden till bara materialposterna.

## Total kostnad

| Scenario | Total kostnad (SEK) |
| --- | --- |
| Egen byggnad i hemverkstad | 23 000–48 500 |
| Byggd kollektivt på makerspace | 28 000–60 000 |
| Beställd från professionell verkstad | 200 000–490 000 |

Det är värt att notera att liknande projekt (CARV Walking Bicycle, Panterragaffe) inte sålts kommersiellt utan byggts som enstaka prototyper. Det är inte en produkt med klar massmarknad — det är ett konstprojekt eller ett tekniskt experiment.

# Programvara och simuleringsmodell

Projektet inkluderar en komplett interaktiv simuleringsmodell som körs i webbläsare. Modellen är uppbyggd i tre lager:

**Python-lagret** (kinematik och dimensioner):

| Fil | Funktion |
| --- | --- |
| jansen.py | Theo Jansens benmekanism, ren matematisk modell |
| machine.py | 2D-modell med ram, ben, ryttare och styrjusteringar |
| machine3d.py | 3D-utbyggnad av modellen |
| export_geometry.py | Genererar machine_geometry.json från Python-modellen |
| export_stl.py | Genererar STL-filer för 3D-print |
| komponentlista.py | Genererar komponentlista (116 delar) |

**Datalager**:

| Fil | Funktion |
| --- | --- |
| machine_geometry.json | Komplett geometri som JS-lagret läser |

**JS-lagret** (rendering, animation, UI):

| Fil | Funktion |
| --- | --- |
| index.html | Tunn shell med UI-element och import map |
| js/main.js | Orkestrering — läser JSON och bygger upp scenen |
| js/setup.js | Scen, kamera, ljus, mark (med rörelse), OrbitControls |
| js/helpers.js | Gemensamma mesh-primitiver |
| js/frame.js | Ramnoder och dynamisk sadelstång |
| js/saddle.js | Sadelns 3D-form och topp-funktion |
| js/driveline.js | Axlar, drev, kedjor, pedalvevar |
| js/legs.js | Jansen-kinematik och 3D-fackverket |
| js/handlebar.js | Styret med rotation, kopplat till styrutslaget |
| js/steering.js | Styrmekanismens triangelmatematik |
| js/steering_render.js | Visualisering av triangelstöd och teleskop |
| js/mannequin.js | Artikulerad förar-figur med 3D-IK för ben och armar |
| js/rider.js | Placering, IK-mål, automatisk sadelhöjd |
| js/animation.js | Animationsloop med framdrift och markens rotation |
| js/ui.js | DOM-events och slider-bindning |
| js/video.js | Manuskriptbaserad MediaRecorder-inspelning |

Arkitekturens grundprincip är att numeriska värden (mått, dimensioner, konstanter) hör hemma i Python-lagret och förmedlas via JSON till JS, medan visuell form, IK-algoritmer och animation lever i JS. Detta ger en enda sanning för varje siffra och underlättar parallell utveckling.

# Öppen källkod och spridning

## Designfilosofi

Projektet följer en lång tradition av öppen delning inom Jansen-relaterade konstruktioner. Theo Jansen själv har valt att inte patentera sin mekanism, och de pedaldrivna varianterna som följt har också varit publika makerprojekt. Springcykeln fortsätter i samma anda.

## Licens

Föreslagna licenser för olika typer av material:

- Källkod (Python, HTML, JavaScript): MIT License
- Designfiler (STL, JSON, ritningar): CC BY-SA 4.0
- Dokumentation (whitepaper, instruktioner): CC BY-SA 4.0

Detta tillåter andra att bygga, modifiera och även sälja sina egna versioner, förutsatt att de hänvisar till ursprungsverket och bidrar tillbaka under samma villkor.

# Framtida arbete

Aspekter som ännu inte är fullständigt utvecklade eller verifierade:

- Styrmekanismens kammar och kamaxlar är konceptuellt löst och kinematiskt validerade, men inte fysiskt prototypbyggda eller dimensionerade för verkliga belastningar.
- Realistiska kedjor som lindar sig runt dreven (just nu förenklade tangenter i 3D-visualiseringen).
- Animation av styrmekanismens egenrörelse i 3D — kamrotation, teleskopförlängning, lutningskompensation.
- Materialval och dimensionering med hänsyn till verklig last och utmattning.
- Säkerhetsanalys: vad händer vid kedjebrott, plötslig stopp, kullning?
- Fysisk prototyp i mindre skala (1:5) för validering av kinematik och styrning före full byggnad.
- Inbromsningsmekanism (bromsskivor på en av vevaxlarna?).
- Praktisk testning av lutningsstyrning — hur intuitiv är den för en cyklist som inte är van vid att en sväng kräver aktivt lutande?

# Avslutning

Springcykeln är ett konstprojekt vid skärningen mellan ergonomi, mekanik och konstnärligt uttryck. Den är inte avsedd som ett praktiskt transportmedel — bilen, cykeln och tunnelbanan är alla effektivare. Vad Springcykeln däremot ger är en visuell och kinestetisk upplevelse av Jansens mekanism i mänsklig skala, driven av förarens egen kraft.

Genom att hålla designen öppen hoppas vi att andra kan bygga vidare, förbättra och anpassa konstruktionen till sina egna ändamål. Det är vad Theo Jansen själv gjort möjligt, och det är så hela traditionen av ridbara gångmaskiner har växt.

*— Slut på dokumentet —*
