**Springcykel**

*En pedaldriven fyrbent ridbar maskin*

Designdokument och teknisk specifikation

*Version 2.0 — Maj 2026*

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
- Styrning via asymmetrisk kammekanism som förlänger AB-länken på inre sidan i en sväng, vilket ger differentiell steglängd
- Ergonomisk sittposition beräknad så att benens vinklar vid pedalens lägsta läge är cirka 95 % av maxutsträckning — anpassat för förarlängd
- Komplett kinematisk simuleringsmodell med interaktiv 3D-visualisering och stöd för manuskriptbaserad videoinspelning

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

## Ram och bensystem

Ramen är konstruerad som ett rörstaglerverk med stål- eller aluminiumrör. Centrala dimensioner:

| Mått | Värde (cm) |
| --- | --- |
| Hjulbas (fram–bak vevcentrum) | 50 |
| Spårvidd (mellan vänster och höger ben) | 30 |
| Höjd: mark till vevcentrum | 91.83 |
| Höjd: mark till sadel (justerbar) | 106–140 |
| Höjd: mark till styre | 124 |

Två separata vevpartier driver fram- respektive bakbenen. Vänster och höger ben på samma vevparti är 180° fasförskjutna. Fram- och bakbenparet är också 180° fasförskjutna mot varandra — vilket ger ett trav-mönster: när vänster fram-fot och höger bak-fot är på marken, är höger fram-fot och vänster bak-fot i luften.

## Drivlina

Föraren trampar på pedaler som sitter på en separat pedalvevaxel. Två kedjor överför rotation från pedalvevaxeln till fram- respektive bakvevaxeln. Drevet på pedalvevaxeln är 4 cm i radie; drevet på bens-vevaxlarna är 10 cm — vilket ger en utväxling 1:2.5.

Den laterala (z-axiella) ordningen från ramcentrum och utåt på varje sida:

| z (cm) | Komponent |
| --- | --- |
| 0 – ±2 | Lagerhus där axeln möter ramen |
| ±2 – ±3 | Drev för kedjedrift (1 cm tjockt) |
| ±3 – ±5 | Vevarm fastsatt på drev/axel (2 cm tjock) |
| ±5 | B2-leden (sekundärplanet i 3D-fackverket) |
| ±5 – ±15 | Pedaltapp + pedalplatta (plattan trädd på tappen) |
| ±15 | B1-leden (Jansens ursprungliga B-fästpunkt) |

Pedalvevaxeln slutar vid ±5 (vid vevarmens utsida), medan fram- och bakvevaxlarna fortsätter ut till ±15 där benens C-punkt sitter på respektive vevarm. B-axeln på ramen sträcker sig från ramcentrum och passerar genom både B2-leden (vid z = ±5) och B1-leden (vid z = ±15), så att en enda axel tar upp sidobelastning från båda lederna i 3D-fackverket.

## Styrning

Styrning sker via *differentiell steglängd*: inre sidan av maskinen tar kortare steg än yttre sidan i en sväng, vilket vrider maskinen kring en centroid mellan benen. Mekanismen utnyttjar att Jansens benkinematik är känslig för positionen av B-leden — en förlängning av AB-länken (avståndet från vevaxel till benets B-fästpunkt) på ena sidan av maskinen ger där kortare steg, medan motsatta sidan förblir oförändrad.

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

Förkortning av AB är teoretiskt möjlig men praktiskt obrukbar: mekanismen tappar sin karakteristiska gång redan vid −0.5 cm där fotlyftet växer från 22 till 30 cm, och bryter helt vid omkring −1.3 cm. Designen tillåter därför endast *förlängning* av AB. Yttre sidan i en sväng står kvar vid baseline (offset 0); inre sidan ökar upp till +4 cm.

### Triangelmekanism för B-leden

Direkt translation av B i x-led är mekaniskt komplicerat — B-axeln skulle behöva glida i x-led samtidigt som den bär böjnings- och vridkrafter från benen, vilket kräver kostsamma glidlagringar med stora dimensioner. Lösningen är en *triangelmekanism* där en av sidorna är teleskopisk:

- **Bakben:** triangeln A_rear—P—B_rear. Sidan A_rear→B_rear teleskoperas längs sin egen axel; sidan P→B_rear behåller fast längd 51.0 cm och har ett gångjärn vid P. När teleskopet förlängs vandrar B_rear i en cirkulär båge kring P.
- **Framben:** motsvarande triangel A_front—M—B_front. Sidan A_front→B_front teleskoperas; sidan M→B_front behåller fast längd 49.2 cm med gångjärn vid M.

Eftersom B rör sig i en båge (inte rent i x-led) ändras både den horisontella och vertikala komponenten av AB-vektorn med utslaget. Det är inte ett problem för Jansen-kinematiken — modellen hanterar redan båda komponenterna parametriskt.

Triangelgeometrin löser belastningsproblemet helt: teleskopet utsätts endast för axiell kraft längs AB, eftersom alla sidolaster tas upp av den fasta P→B-stången (eller M→B-stången för frambenet) via gångjärnet. Inga vridmoment, ingen böjning, ingen glidning vinkelrätt mot teleskopets axel. Mekaniskt är detta en betydligt enklare lösning än ett fritt-bärande glidteleskop.

### Kamprofil

Aktuering av teleskopet sker via en kam (kamskiva med profilerad nock) monterad på en kamaxel som sitter på ramen. Kammens periferi pressar mot teleskopets inre rör, och en returfjäder håller följaren mot kammen samt återställer baseline-läget när styret släpps.

Kamprofilen designas asymmetriskt så att kammen bara är aktiv åt ett håll:

- Vid kamvinkel 0° (mittläge, styret rakt): följaren pressar inte teleskopet — AB är vid baseline 38.79 cm.
- Vid kamvinkel +α (styrutslag åt kammens aktiva sida): följaren pressas successivt utåt, AB förlängs upp till +4 cm vid maxutslag.
- Vid kamvinkel −α (motsatt utslag): kammen har en platt sektor — följaren rör sig inte. AB förblir baseline.

Detta gör att varje kam bara aktiverar sin sida i den ena svängriktningen. Vänster sidas kam aktiveras vid vänstersväng; höger sidas vid högersväng. I rakt läge är båda kammarna i vilolägets platta sektor.

Kamprofilens form bestämmer även styrkänslan — om följaren ska röra sig linjärt mot styrvinkeln, eller progressivt (mer utslag krävs nära ändlägena). Detta är ett designval som kan justeras utan att ändra resten av mekanismen.

### Två kamaxlar driver fyra ben

Fram- och bakbenen på samma sida ska justeras tillsammans — annars divergerar deras steglängder och maskinen vrider sig okontrollerbart kring en vertikal axel. En naturlig lösning är att låta en gemensam kamaxel löpa längs ramens sida med två kammar — en vid varje ben. Då har maskinen totalt två kamaxlar (vänster och höger), inte fyra separata kammar.

Styret kopplas till de två kamaxlarna via en länkmekanism som driver dem åt motsatta håll: vid vänstersväng vrids vänster axels kammar in i sin aktiva sektor, höger axels kammar förblir i vilo (och vice versa). Mekanisk länk via stänger och vinkelarmar är robustast; bowdenwires är ett tunnare alternativ men kräver kompensationsfjädrar.

### Prestanda

Vid maximalt styrutslag (+4 cm AB-förlängning på inre sidan):

| Storhet | Värde |
|---|---|
| Steglängd yttre sida | 67.9 cm |
| Steglängd inre sida | 61.4 cm (fram) / 61.7 cm (bak) |
| Steglängdsasymmetri | 6.5 cm |
| Svängradie (vid 30 cm spårvidd) | 2.97 m |

Detta är inom körfältsbredd för normal cykelväg och möjliggör vändning i de flesta gatorum.

### Biverkning: fotlyft på inre sida

En konsekvens av Jansens kinematik är att fotbanan inte bara *krymper* horisontellt vid AB-förlängning — den *lyfts* också vertikalt. Vid maxutslag når inre fötter inte längre marken om maskinen hålls upprätt:

| Ben | Fotbanans lägsta punkt över vevcentrum | Lyft från marken |
|---|---|---|
| Framben | 100.0 cm | 8.2 cm |
| Bakben | 96.9 cm | 5.0 cm |

Frambenet lyfter mer än bakbenet eftersom de har olika triangelgeometri: bakbenets P→B-stöd är längre (51 cm) och har en mer gynnsam vinkel mot A→B, vilket gör att förlängning av AB ger en flackare båge för B. Frambenet har M→B (49.2 cm) med en mer aggressiv vinkel.

### Markkontakt under sväng

Att fötterna lyfts upp från marken är inte i sig ett problem — det löses av samma rörelse som föraren ändå utför. För balansens skull *måste* föraren luta maskinen inåt i sin sväng, precis som en cyklist gör för att kompensera för centripetalaccelerationen. När maskinen lutar inåt sänks inre sidan och höjs yttre — och inre fötter återställer markkontakt automatiskt.

Vid 4 cm AB-offset kräver fullständig markåterställning ungefär 15° lutning åt yttre sida för frambenet, ~10° för bakbenet. Det är inom samma lutningsintervall som en cyklist använder i en lugn kurva, så det följer naturligt av körningen utan att kräva särskild styrteknik.

Båda sidornas ben bidrar därför till framdriften, om än med olika belastning: yttre sidan tar längre steg och bär mer av maskinens vikt rakt ner i ramens stödriktning, inre sidan tar kortare steg men trycker mot marken i en mer sidoriktad vinkel. Hur kraftfördelningen ser ut i detalj beror på dynamiken — körhastighet, kurvradie och förarens viktfördelning — och låter sig knappast simuleras utan fysisk prototyp.

### Öppna designfrågor

- Exakt placering av kamaxlarna på ramen.
- Returfjäderns dimensionering — måste övervinna benens normala dragkrafter utan att göra styret tungt.
- Kopplingsmekanik från styraxeln (N→H) till de två kamaxlarna — bowdenwires med korsad ledning, kuggdrev eller stång och vinkelarm är alla rimliga alternativ.
- Eventuell aktiv lutningskompensation — t.ex. genom att förskjuta sadelns eller styrets pivotpunkt under sväng.

# Ergonomi

## Förarens anpassning

Maskinen är dimensionerad för en förare på 194 cm men anpassningsbar i intervallet 140–210 cm via två justeringar:

- Sadelhöjd: justerbar 106–140 cm från marken via sadelstångens position
- Förarens horisontella sittposition på sadeln (x-position) varierar beroende på förarens längd och vald sadelhöjd

## Ergonomiska målsättningar

Två huvudkriterier styr förarens placering:

- **Benens utsträckning:** vid pedalens lägsta position ska benet vara utsträckt till 95 % av maxlängden. Detta motsvarar 25–35° knäböj — den ergonomiskt rekommenderade vinkeln för cykling som skyddar knäna från överbelastning samtidigt som det ger god kraftöverföring.
- **Armarnas position:** överarmen ska vinkla framåt från axeln för att handen ska nå styret naturligt. Bålen lutar 15–30° framåt beroende på proportioner.

## Automatisk anpassning

Mjukvarumodellen beräknar automatiskt:

- Optimal sadelhöjd: föraren placeras vid x=0 (höften rakt över pedalen) med 95 % benutsträckning. Klipps till 106–140 cm-intervallet.
- Vid sadelhöjd utanför intervallet (för kort eller lång förare) flyttas förarens sittposition framåt eller bakåt på sadeln.
- Bålvinkel: ökas stegvis från 15° upp till maximalt 70° tills armarna kan nå styret. Långa armar = mindre lutning.

## Sadelns form

Sadeln är 45 cm lång (x=-15 till x=30 från ramens bakvevaxel). Formen är fast:

- Sittpunkt vid x=25 (sadelns lägsta y-koordinat)
- Bakdel vid x=0: alltid 11 cm högre än sittpunkten
- Mjuk båge mellan x=0 och x=25 via cosinus-interpolation
- Sadelns bredd taperar från 12 cm bak till 8 cm fram
- Konkavitet (sadeldipp): 1.5 cm vid sittpunkten

Bakdelens högre position gör att sadeln kröker sig över bakvevaxeln och ger högre sittposition för långa förare som behöver mer benutrymme.

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

Detta är betydligt tyngre än en cykel (8–15 kg) och något tyngre än version 1.0 (34–51 kg) på grund av 3D-fackverket och styrmekaniken. Vikten ligger lågt (vevarmar och ben), vilket ger god stabilitet. För att hålla nere vikten är aluminium på benen ett intressant alternativ till stål — kostnaden är högre men kan motiveras av den dynamiska viktbesparingen.

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

Materialkostnaden ökar jämfört med version 1.0 främst på grund av dubbla antalet benstänger (92 mot tidigare 44) och tillkomsten av styrmekanismens specialkomponenter.

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

# Öppen källkod och spridning

## Designfilosofi

Projektet följer en lång tradition av öppen delning inom Jansen-relaterade konstruktioner. Theo Jansen själv har valt att inte patentera sin mekanism, och de pedaldrivna varianterna som följt har också varit publika makerprojekt. Springcykeln fortsätter i samma anda.

## Licens

Föreslagna licenser för olika typer av material:

- Källkod (Python, HTML, JavaScript): MIT License
- Designfiler (STL, JSON, ritningar): CC BY-SA 4.0
- Dokumentation (whitepaper, instruktioner): CC BY-SA 4.0

Detta tillåter andra att bygga, modifiera och även sälja sina egna versioner, förutsatt att de hänvisar till ursprungsverket och bidrar tillbaka under samma villkor.

## Distribuerade filer

Projektet består av följande huvudfiler, organiserade i tre lager:

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
| js/setup.js | Scen, kamera, ljus, mark, OrbitControls |
| js/helpers.js | Gemensamma mesh-primitiver |
| js/frame.js | Ramnoder och dynamisk sadelstång |
| js/saddle.js | Sadelns 3D-form och topp-funktion |
| js/driveline.js | Axlar, drev, kedjor, pedalvevar |
| js/legs.js | Jansen-kinematik och 3D-fackverket |
| js/handlebar.js | Styret |
| js/mannequin.js | Artikulerad förar-figur |
| js/rider.js | Placering, IK-mål, automatisk sadelhöjd |
| js/steering.js | Triangelmekanism för per-ben B-leder |
| js/steering_render.js | Visualisering av teleskop och stödstänger |
| js/animation.js | Animationsloop |
| js/ui.js | DOM-events och slider-bindning |
| js/video.js | Manuskriptbaserad MediaRecorder-inspelning |

Arkitekturens grundprincip är att numeriska värden (mått, dimensioner, konstanter) hör hemma i Python-lagret och förmedlas via JSON till JS, medan visuell form, IK-algoritmer och animation lever i JS. Detta ger en enda sanning för varje siffra och underlättar parallell utveckling.

# Framtida arbete

Aspekter som ännu inte är fullständigt utvecklade eller verifierade:

- Styrmekanismen är konceptuellt löst och kinematiskt validerad, men inte fysiskt prototypbyggd eller dimensionerad för verkliga belastningar.
- Realistiska kedjor som lindar sig runt dreven (just nu förenklade tangenter i 3D-visualiseringen).
- Animation av styrning i 3D-modellen — kamrotation, teleskopförlängning, lutningskompensation och resulterande steglängdsasymmetri.
- Materialval och dimensionering med hänsyn till verklig last och utmattning.
- Säkerhetsanalys: vad händer vid kedjebrott, plötslig stopp, kullning?
- Fysisk prototyp i mindre skala (1:5) för validering av kinematik och styrning före full byggnad.
- Inbromsningsmekanism (bromsskivor på en av vevaxlarna?).
- Praktisk testning av lutningsstyrning — hur intuitiv är den för en cyklist som inte är van vid att en sväng kräver aktivt lutande?

# Avslutning

Springcykeln är ett konstprojekt vid skärningen mellan ergonomi, mekanik och konstnärligt uttryck. Den är inte avsedd som ett praktiskt transportmedel — bilen, cykeln och tunnelbanan är alla effektivare. Vad Springcykeln däremot ger är en visuell och kinestetisk upplevelse av Jansens mekanism i mänsklig skala, driven av förarens egen kraft.

Genom att hålla designen öppen hoppas vi att andra kan bygga vidare, förbättra och anpassa konstruktionen till sina egna ändamål. Det är vad Theo Jansen själv gjort möjligt, och det är så hela traditionen av ridbara gångmaskiner har växt.

*— Slut på dokumentet —*
