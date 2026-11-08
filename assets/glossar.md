Dieses Glossar erklärt die wichtigsten Begriffe des **Marktstammdatenregisters (MaStR)**. Es zeigt vor allem, wie die
Objekte und Tabellen der MaStR-Datenbank zusammenhängen. Die Datenbank wird täglich aus dem
[Gesamtdatenexport](https://www.marktstammdatenregister.de/MaStR/Datendownload) der Bundesnetzagentur aufgebaut. Sie ist
die Grundlage aller Seiten dieser App und steht auf der Seite **Downloads** als Datenbank-Dump bereit.

Die Tabellen heißen wie die Dateien des Gesamtdatenexports (z. B. `EinheitenWind`). In PostgreSQL sind Tabellen- und
Spaltennamen kleingeschrieben (`einheitenwind`, `einheitmastrnummer`).

### Zusammenhänge im Überblick

Im Mittelpunkt stehen die **Einheiten**. Eine Einheit ist eine einzelne technische Einrichtung, die Strom oder Gas
erzeugt, speichert oder verbraucht, z. B. eine Windenergieanlage, eine Solaranlage auf einem Dach oder ein
Batteriespeicher. Jeder Energieträger hat eine eigene Einheiten-Tabelle. Alle anderen Objekte sind über
**MaStR-Nummern** mit den Einheiten verknüpft:

- **Wer betreibt die Einheit?** Jede Einheit hat einen **Anlagenbetreiber**, einen Marktakteur aus der Tabelle
  `Marktakteure`.
- **Zu welcher Anlage gehört sie?** Rechtliche und technische Zusammenfassungen von Einheiten sind eigene Objekte, die
  **Gruppierungsobjekte**: EEG-Anlage, KWK-Anlage, Strom- oder Gasspeicher und Genehmigung.
- **Wie ist sie ans Netz angeschlossen?** Einheiten, die gemeinsam an das Netz angeschlossen sind, bilden eine
  **technische Lokation**. Die Lokation hat einen oder mehrere **Netzanschlusspunkte**, und jeder Netzanschlusspunkt
  liegt im **Netz** eines **Netzbetreibers**.
- **Was bedeuten die Zahlen in vielen Spalten?** Spalten wie Bundesland, Betriebsstatus oder Energieträger enthalten nur
  die ID eines **Katalogwerts**. Den Text dazu enthält die Tabelle `Katalogwerte`.

```text
Einheit (Einheiten…: SEE…, SVE…, GEE…, GVE…)
 ├─ AnlagenbetreiberMastrNummer --> Anlagenbetreiber (Marktakteure: ABR…)
 ├─ EegMaStRNummer ---------------> EEG-Anlage (AnlagenEeg…: EEG…)
 ├─ KwkMaStRNummer ---------------> KWK-Anlage (AnlagenKwk: KWK…)
 ├─ SpeMastrNummer ---------------> Stromspeicher (AnlagenStromSpeicher: SSE…)
 ├─ SpeicherMaStRNummer ----------> Gasspeicher (AnlagenGasSpeicher: GSE…)
 ├─ GenMastrNummer ---------------> Genehmigung (EinheitenGenehmigung: SGE…)
 ├─ z. B. Bundesland -------------> Katalogwert (Katalogwerte) --> Katalogkategorie (Katalogkategorien)
 └─ LokationMaStRNummer ----------> technische Lokation (Lokationen: SEL…, SVL…, GEL…, GVL…)

technische Lokation (Lokationen: SEL…, SVL…, GEL…, GVL…)
 └─ NetzanschlusspunkteMaStRNummern --> Netzanschlusspunkt (Netzanschlusspunkte: SAN…, GAN…)
     ├─ NetzMaStRNummer --------------------------> Netz (Netze: SNE…, GNE…)
     ├─ NetzbetreiberMaStRNummer -----------------> Netzbetreiber (Marktakteure: SNB…, GNB…)
     └─ BilanzierungsgebietNetzanschlusspunktId --> Bilanzierungsgebiet (Bilanzierungsgebiete)

Netzbetreiber (Marktakteure: SNB…, GNB…)
 └─ Netz --> Netz (Netze: SNE…, GNE…)
```

Hinweise zu den Verknüpfungen:

- Eine Verknüpfung bedeutet nur, dass die MaStR-Nummern übereinstimmen. Die Datenbank legt keine Fremdschlüssel an.
  Ein Verweis kann leer sein oder ins Leere gehen. Einheiten **in Planung** haben z. B. meist noch keine Lokation, weil
  der Netzbetreiber sie erst beim Netzanschluss anlegt.
- Die Gruppierungsobjekte, Lokationen und Genehmigungen verweisen umgekehrt auch auf ihre Einheiten, und zwar in der
  Spalte `VerknuepfteEinheitenMaStRNummern` (kommagetrennte Liste).
- Bei Wind und Solar gehört zu jeder Einheit genau eine EEG-Anlage. Bei Biomasse fasst eine EEG-Anlage oft mehrere
  Einheiten zusammen (z. B. mehrere Motoren einer Biogasanlage).
- Die Einheiten-Tabellen haben dieselben Grundspalten:
  - MaStR-Nummer und Name
  - Standort: Adresse, Gemeindeschlüssel, Koordinaten
  - Betriebsstatus
  - Daten zu Registrierung, Inbetriebnahme und Stilllegung
  - Leistung und die Verweise oben

  Dazu kommen Spalten, die nur für den jeweiligen Energieträger gelten.

Weitere Verknüpfungen:

| Tabelle | Spalte | verweist auf |
|---|---|---|
| `AnlagenEegWasser` | `ErtuechtigungIds` | `Ertuechtigungen.Id` (Liste) |
| `EinheitenAenderungNetzbetreiberzuordnungen` | `EinheitMastrNummer`, `LokationMastrNummer`, `NetzanschlusspunktMastrNummer`, `NetzbetreiberMastrNummerAlt`, `NetzbetreiberMastrNummerNeu` | Einheit, Lokation, Netzanschlusspunkt, alter und neuer Netzbetreiber |
| `EinheitenGasverbraucher` | `VerknuepfteEinheitenMaStRNummern` | Stromerzeugungseinheiten, die mit dem Gas Strom erzeugen (Liste) |
| `EinheitenStromSpeicher` | `GemeinsamRegistrierteSolareinheitMastrNummer` | zusammen mit dem Speicher registrierte Solareinheit (`EinheitenSolar`) |
| `EinheitenVerbrennung` | `MastrNummernKombibetrieb` | Einheiten, die im Kombibetrieb zusammenarbeiten (Liste) |
| `Einheiten…` | `AltAnlagenbetreiberMastrNummer` | früherer Anlagenbetreiber (`Marktakteure`) |
| `Ertuechtigungen` | `EegMastrNummer` | `AnlagenEegWasser.EegMaStRNummer` |
| `GeloeschteUndDeaktivierteEinheiten` | `Einheittyp` | `Einheitentypen.Id` |
| `Katalogwerte` | `KatalogKategorieId` | `Katalogkategorien.Id` |
| `Lokationen`, `Netzanschlusspunkte` | `Lokationtyp` | `Lokationstypen.Id` |
| `Marktakteure` | `Marktfunktion` | `Marktfunktionen.Id` |
| `MarktakteureUndRollen` | `MarktakteurMastrNummer` | `Marktakteure.MastrNummer` |
| `Marktrollen` | `Marktfunktion` | `Marktfunktionen.Id` |
| `Netze` | `Bilanzierungsgebiete` | `Bilanzierungsgebiete.Yeic` (Liste) |

### MaStR-Nummern

Jedes Objekt im MaStR hat eine eindeutige **MaStR-Nummer**. Sie besteht aus einem Präfix aus drei Buchstaben, der
Versionsziffer 9, zehn zufälligen Ziffern und einer Prüfziffer, z. B. `SEE912345678901`. Am Präfix erkennt man, um
welche Art von Objekt es sich handelt.

| Präfix | Objekt | Tabelle |
|---|---|---|
| `EEG` | EEG-Anlage | `AnlagenEeg…` |
| `GAN` | Netzanschlusspunkt Gas | `Netzanschlusspunkte` |
| `GEE` | Gaserzeugungseinheit, auch die Einheiten der Gasspeicher | `EinheitenGasErzeuger`, `EinheitenGasSpeicher` |
| `GEL` | technische Gaserzeugungslokation | `Lokationen` |
| `GNE` | Gasnetz | `Netze` |
| `GSE` | Gasspeicher | `AnlagenGasSpeicher` |
| `GVE` | Gasverbrauchseinheit | `EinheitenGasverbraucher` |
| `GVL` | technische Gasverbrauchslokation | `Lokationen` |
| `KWK` | KWK-Anlage | `AnlagenKwk` |
| `SAN` | Netzanschlusspunkt Strom | `Netzanschlusspunkte` |
| `SEE` | Stromerzeugungseinheit, auch die Einheiten der Stromspeicher | `EinheitenWind`, `EinheitenSolar`, `EinheitenBiomasse`, `EinheitenWasser`, `EinheitenGeothermieGrubengasDruckentspannung`, `EinheitenKernkraft`, `EinheitenVerbrennung`, `EinheitenStromSpeicher` |
| `SEL` | technische Stromerzeugungslokation | `Lokationen` |
| `SGE` | Genehmigung | `EinheitenGenehmigung` |
| `SNE` | Stromnetz | `Netze` |
| `SSE` | Stromspeicher | `AnlagenStromSpeicher` |
| `SVE` | Stromverbrauchseinheit | `EinheitenStromVerbraucher` |
| `SVL` | technische Stromverbrauchslokation | `Lokationen` |

Die Marktakteure tragen als Präfix ihre Marktfunktion (siehe **Marktfunktion**):

| Präfix | Marktfunktion |
|---|---|
| `ABR` | Anlagenbetreiber |
| `ADM` | Bundesnetzagentur |
| `BVI` | Behörde, Verband, Institution |
| `GEM` | Akteur im Gasmarkt |
| `GNB` | Gasnetzbetreiber |
| `OMP` | Organisierter Marktplatz |
| `SEM` | Akteur im Strommarkt |
| `SNB` | Stromnetzbetreiber |
| `SOM` | Sonstiger Marktakteur |
| `SUP` | Supportpartner |

Die Marktrolle eines Marktakteurs wird mit zwei weiteren Buchstaben angehängt, z. B. `SNB912345678901AN` für einen
Stromnetzbetreiber in der Rolle Anschlussnetzbetreiber (siehe **Marktrolle**).

### Tabellen der Datenbank (A–Z)

#### AnlagenEegBiomasse

`anlageneegbiomasse` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Biomasse-Einheiten. Die Tabelle enthält alles, was für die Anlage im Sinne des EEG gilt:

- EEG-Inbetriebnahmedatum und installierte Leistung
- Zuschlag aus einer Ausschreibung
- Flexibilitätsprämie und Leistungserhöhung bei Biogas
- Höchstbemessungsleistung und Einsatz von Biomethan

Verknüpft über `EinheitenBiomasse.EegMaStRNummer`.

#### AnlagenEegGeothermieGrubengasDruckentspannung

`anlageneeggeothermiegrubengasdruckentspannung` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Einheiten aus Geothermie, Grubengas und Druckentspannung: EEG-Inbetriebnahmedatum, installierte
Leistung und Betriebsstatus. Verknüpft über `EinheitenGeothermieGrubengasDruckentspannung.EegMaStRNummer`.

#### AnlagenEegSolar

`anlageneegsolar` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Solareinheiten (genau eine je Einheit). Die Tabelle enthält:

- EEG-Inbetriebnahmedatum und installierte Leistung
- ob eine Zahlung nach dem EEG in Anspruch genommen wird
- Mieterstrom
- Zuschlag und zugeordnete Gebotsmenge
- Nummern aus den Vorgängerregistern Anlagenregister und PV-Meldeportal

Verknüpft über `EinheitenSolar.EegMaStRNummer`.

#### AnlagenEegSpeicher

`anlageneegspeicher` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Stromspeicher-Einheiten. Ein Speicher, der Strom aus erneuerbaren Energien zwischenspeichert, kann eine
EEG-Anlage sein. Die Tabelle enthält EEG-Inbetriebnahmedatum, EEG-Anlagenschlüssel und Zuschlag. Verknüpft über
`EinheitenStromSpeicher.EegMaStRNummer`.

#### AnlagenEegWasser

`anlageneegwasser` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Wasserkraft-Einheiten: EEG-Inbetriebnahmedatum, installierte Leistung, Betriebsstatus und die IDs der
**Ertüchtigungen** der Anlage (`ErtuechtigungIds`). Verknüpft über `EinheitenWasser.EegMaStRNummer`.

#### AnlagenEegWind

`anlageneegwind` · Schlüssel `EegMaStRNummer` (`EEG…`)

EEG-Anlagen der Windeinheiten (genau eine je Einheit). Die Tabelle enthält:

- EEG-Inbetriebnahmedatum und installierte Leistung
- Kennzeichen für Prototyp- und Pilotanlagen
- Zuschlag aus einer Ausschreibung
- Verhältnis von Ertrag zu **Referenzertrag**

Verknüpft über `EinheitenWind.EegMaStRNummer`.

#### AnlagenGasSpeicher

`anlagengasspeicher` · Schlüssel `MaStRNummer` (`GSE…`)

Gasspeicher als Gruppierungsobjekt, z. B. ein Kavernen-, Poren- oder Aquiferspeicher, mit Name, Registrierungsdatum und
Betriebsstatus. Auf einen Gasspeicher verweisen zwei Einheiten-Tabellen über `SpeicherMaStRNummer`:

- `EinheitenGasSpeicher`: die Speicherdaten wie Arbeitsgasvolumen sowie Ein- und Ausspeicherleistung
- `EinheitenGasErzeuger`: die Ausspeisung ins Netz

#### AnlagenKwk

`anlagenkwk` · Schlüssel `KwkMastrNummer` (`KWK…`)

KWK-Anlagen nach dem Kraft-Wärme-Kopplungsgesetz: elektrische KWK-Leistung, thermische Nutzleistung,
Inbetriebnahmedatum, Zuschlag und Betriebsstatus. Verknüpft über `KwkMaStRNummer` der Einheiten aus Verbrennung,
Biomasse sowie Geothermie, Grubengas und Druckentspannung.

#### AnlagenStromSpeicher

`anlagenstromspeicher` · Schlüssel `MaStRNummer` (`SSE…`)

Der Stromspeicher als Gruppierungsobjekt, der die Energie „aufbewahrt“: vor allem die **nutzbare Speicherkapazität** in
kWh. Die Leistung und die übrigen technischen Daten stehen in der zugehörigen Einheit (`EinheitenStromSpeicher`, Spalte
`SpeMastrNummer`). Zu einem Pumpspeicherkraftwerk können mehrere Einheiten gehören.

#### Bilanzierungsgebiete

`bilanzierungsgebiete` · Schlüssel `Id`

Bilanzierungsgebiete der aktiven Stromnetzbetreiber, jeweils mit Y-Code (`Yeic`, siehe **EIC**), Bezeichnung und
**Regelzone**. Verknüpft über `Netzanschlusspunkte.BilanzierungsgebietNetzanschlusspunktId`. Die Netze listen ihre
Bilanzierungsgebiete in `Netze.Bilanzierungsgebiete`.

#### EinheitenAenderungNetzbetreiberzuordnungen

`einheitenaenderungnetzbetreiberzuordnungen` · kein Schlüssel

Verlauf der Wechsel des Anschlussnetzbetreibers einer Einheit. Jede Zeile enthält:

- Einheit, Lokation und Netzanschlusspunkt
- alten und neuen Netzbetreiber
- Art der Änderung und Datum

Häufigste Art der Änderung ist die „Übertragung von Einheiten“ an einen anderen Netzbetreiber, z. B. nach einer
Netzübernahme. Seltener ist eine Standortänderung.

#### EinheitenBiomasse

`einheitenbiomasse` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Stromerzeugungseinheiten, die Biomasse verstromen, z. B. die Motoren einer Biogasanlage oder ein
Biomasseheizkraftwerk. Typische Spalten sind Hauptbrennstoff, Biomasseart und Technologie. Die Einheiten verweisen auf
eine EEG-Anlage und gegebenenfalls eine KWK-Anlage.

#### EinheitenGasErzeuger

`einheitengaserzeuger` · Schlüssel `EinheitMastrNummer` (`GEE…`)

Gaserzeugungseinheiten mit Technologie und Erzeugungsleistung, z. B.:

- Biomethan-Erzeugung
- Förderung von Erdgas
- Power-to-Gas
- LNG-Terminals

Auch die Ausspeisung eines Gasspeichers ins Netz ist als Gaserzeugungseinheit registriert; sie verweist über
`SpeicherMaStRNummer` auf den Gasspeicher.

#### EinheitenGasSpeicher

`einheitengasspeicher` · Schlüssel `EinheitMastrNummer` (`GEE…`)

Gasspeicher-Einheiten mit Speicherart (Kaverne, Porenspeicher, Aquifer), maximal nutzbarem Arbeitsgasvolumen und
maximaler Ein- und Ausspeicherleistung. Sie verweisen über `SpeicherMaStRNummer` auf den Gasspeicher
(`AnlagenGasSpeicher`).

#### EinheitenGasverbraucher

`einheitengasverbraucher` · Schlüssel `EinheitMastrNummer` (`GVE…`)

Gasverbrauchseinheiten, die Gas aus dem Fernleitungsnetz beziehen, mit maximaler Gasbezugsleistung. Dient das Gas der
Stromerzeugung (Gaskraftwerk), verweist die Einheit auf die zugehörigen Stromerzeugungseinheiten
(`VerknuepfteEinheitenMaStRNummern`).

#### EinheitenGenehmigung

`einheitengenehmigung` · Schlüssel `GenMastrNummer` (`SGE…`)

Genehmigungen für Bau oder Betrieb von Einheiten. Jede Zeile enthält:

- Art der Genehmigung, meist nach dem Bundes-Immissionsschutzgesetz (BImSchG), auch nach Baurecht oder
  Wasserhaushaltsgesetz
- Behörde und Aktenzeichen
- Frist bis zum Baubeginn
- Wasserrecht
- verknüpfte Einheiten

Eine Genehmigung kann für mehrere Einheiten gelten, z. B. für alle Anlagen eines Windparks.

#### EinheitenGeothermieGrubengasDruckentspannung

`einheitengeothermiegrubengasdruckentspannung` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Stromerzeugungseinheiten aus Geothermie, Grubengas und Druckentspannung. Druckentspannung bedeutet: Strom wird beim
Entspannen von Gas aus Hochdruckleitungen gewonnen. Die Einheiten verweisen auf EEG- und KWK-Anlage.

#### EinheitenKernkraft

`einheitenkernkraft` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Stromerzeugungseinheiten der Kernkraftwerke mit Kraftwerks- und Blockname. Die wenigen Einheiten in der Datenbank sind
seit dem Atomausstieg (April 2023) endgültig stillgelegt.

#### EinheitenSolar

`einheitensolar` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Solareinheiten, die mit Abstand größte Tabelle (mehrere Millionen Einheiten). Typische Spalten:

- Art der Solaranlage: Gebäude-, Freiflächen- oder steckerfertige Solaranlage (Balkonkraftwerk)
- Leistung und Anzahl der Module
- Ausrichtung und Neigung
- Nutzungsbereich des Gebäudes
- Name des Solarparks

Jede Einheit verweist auf ihre eigene EEG-Anlage. Für Einheiten bis 30 kW werden keine Koordinaten veröffentlicht
(siehe **Vertrauliche Daten**).

#### EinheitenStromSpeicher

`einheitenstromspeicher` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Die Einheiten der Stromspeicher, meist Batteriespeicher, aber auch Pump-, Druckluft- und Wasserstoffspeicher. Die
Einheit erzeugt aus der gespeicherten Energie wieder Strom. Typische Spalten:

- Technologie und Batterietechnologie
- AC- oder DC-Kopplung
- Wechselrichterleistung
- bei Pumpspeichern die Leistungsaufnahme im Pumpbetrieb

Die Einheit verweist auf den Speicher (`SpeMastrNummer`), auf die EEG-Anlage und gegebenenfalls auf die gemeinsam
registrierte Solareinheit.

#### EinheitenStromVerbraucher

`einheitenstromverbraucher` · Schlüssel `EinheitMastrNummer` (`SVE…`)

Große Stromverbraucher, die am Hoch- oder Höchstspannungsnetz angeschlossen sind (z. B. Industriebetriebe), mit Name und
Anzahl der Verbrauchseinheiten über 50 MW. Verbraucher an niedrigeren Spannungsebenen müssen sich in der Regel nicht
registrieren.

#### Einheitentypen

`einheitentypen` · Schlüssel `Id`

Systemkatalog der 13 Einheitentypen, z. B. Solareinheit, Windeinheit, Stromspeichereinheit, Gasverbrauchseinheit.
Verwendet in `GeloeschteUndDeaktivierteEinheiten.Einheittyp`.

#### EinheitenVerbrennung

`einheitenverbrennung` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Stromerzeugungseinheiten, die Brennstoffe verbrennen, z. B. Erdgas, Mineralöl, Kohle, Abfall oder Wasserstoff. Das
reicht vom Notstromaggregat bis zum Großkraftwerk. Typische Spalten:

- Kraftwerks- und Blockname
- Haupt- und weitere Brennstoffe
- Technologie
- Kombibetrieb
- Zuordnung zu Netzreserve, Kapazitätsreserve oder Sicherheitsbereitschaft

Die Einheiten verweisen gegebenenfalls auf eine KWK-Anlage.

#### EinheitenWasser

`einheitenwasser` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Stromerzeugungseinheiten aus Wasserkraft mit Kraftwerksname, Art der Wasserkraftanlage (z. B. Laufwasser,
Speicherwasser) und Art des Zuflusses. Pumpspeicher stehen dagegen bei den Stromspeichern. Die Einheiten verweisen auf
eine EEG-Anlage.

#### EinheitenWind

`einheitenwind` · Schlüssel `EinheitMastrNummer` (`SEE…`)

Windenergieanlagen an Land und auf See. Typische Spalten:

- Name des Windparks
- Hersteller und Typ
- Nabenhöhe und Rotordurchmesser
- Auflagen zur Abschaltung (Schall, Schattenwurf, Tierschutz, Eiswurf)
- Nachtkennzeichnung und Bürgerenergie
- auf See: Wassertiefe, Küstenentfernung und Gebiet nach dem Flächenentwicklungsplan

Jede Einheit verweist auf ihre eigene EEG-Anlage und meist auf eine Genehmigung.

#### Ertuechtigungen

`ertuechtigungen` · Schlüssel `Id`

Ertüchtigungen von Wasserkraftanlagen nach dem EEG (z. B. Austausch von Turbinen, Erhöhung der Fallhöhe) mit Art,
Leistungserhöhung, Zulassungspflicht und Datum der Wiederinbetriebnahme. Verknüpft mit `AnlagenEegWasser` über die
EEG-Nummer.

#### GeloeschteUndDeaktivierteEinheiten

`geloeschteunddeaktivierteeinheiten` · Schlüssel `EinheitMastrNummer`

Einheiten, die gelöscht oder deaktiviert wurden, mit Einheitentyp, Status, Datum und Grund der Löschung. Häufige Gründe
sind doppelte Registrierungen, versehentliche Registrierungen und Einheiten, die nie in Betrieb gehen. Diese Einheiten
fehlen in den übrigen Einheiten-Tabellen.

#### GeloeschteUndDeaktivierteMarktakteure

`geloeschteunddeaktiviertemarktakteure` · Schlüssel `MarktakteurMastrNummer`

Gelöschte und deaktivierte Marktakteure mit Status, Datum und Grund, z. B. Tätigkeitsende oder fehlerhafte
Registrierung.

#### Katalogkategorien

`katalogkategorien` · Schlüssel `Id`

Die Kategorien der Katalogwerte, z. B. Energieträger, Betriebsstatus, Bundesland, Spannungsebene, Hersteller.

#### Katalogwerte

`katalogwerte` · Schlüssel `Id`

Alle Werte der Kataloge mit ihrem Text (`Wert`) und ihrer Kategorie (`KatalogKategorieId`). Fast jede Spalte mit
festen Auswahlwerten enthält die `Id` eines Katalogwerts. Die Datenbank-Funktion `katalog(id)` liefert den Text dazu,
`katalog_list(ids)` die Texte einer Liste von IDs.

#### Lokationen

`lokationen` · Schlüssel `MastrNummer` (`SEL…`, `SVL…`, `GEL…`, `GVL…`)

Technische Lokationen mit Name, Lokationstyp, verknüpften Einheiten und Netzanschlusspunkten. Die Lokation verbindet
die Einheiten mit dem Netz (siehe **Lokation**). Häufig gehören zwei Einheiten zu einer Lokation, z. B. eine
Solaranlage und ein Batteriespeicher im selben Haus.

#### Lokationstypen

`lokationstypen` · Schlüssel `Id`

Systemkatalog der vier Lokationstypen: Stromerzeugungs-, Stromverbrauchs-, Gaserzeugungs- und Gasverbrauchslokation.

#### Marktakteure

`marktakteure` · Schlüssel `MastrNummer` (`ABR…`, `SNB…`, …)

Personen und Organisationen, die eine **Marktfunktion** wahrnehmen. Die Tabelle enthält:

- Name oder Firmenname, Personenart und Rechtsform
- Adresse und Kontaktdaten
- Registergericht und Registernummer
- Tätigkeitsbeginn und Tätigkeitsende
- Hauptwirtschaftszweig
- bei Netzbetreibern das eigene **Netz** (`Netz`)

Die allermeisten Marktakteure sind Anlagenbetreiber und davon die meisten natürliche Personen. Deren Namen und
Adressen werden nicht veröffentlicht.

#### MarktakteureUndRollen

`marktakteureundrollen` · Schlüssel `MastrNummer` (MaStR-Nummer mit Rollen-Suffix)

Die **Marktrollen** der Marktakteure mit Marktpartner-ID, BNetzA-Betriebsnummer und Kontakt. Verknüpft über
`MarktakteurMastrNummer`. Bis Version 25.1 des Gesamtdatenexports hieß diese Tabelle „Marktrollen“.

#### Marktfunktionen

`marktfunktionen` · Schlüssel `Id`

Systemkatalog der zehn Marktfunktionen (siehe **Marktfunktion**). Verwendet in `Marktakteure.Marktfunktion` und
`Marktrollen.Marktfunktion`.

#### Marktrollen

`marktrollen` · Schlüssel `Id`

Systemkatalog der Marktrollen mit Marktfunktion und Sparte (Strom oder Gas), z. B. Übertragungsnetzbetreiber,
Messstellenbetreiber, Transportkunde.

#### Netzanschlusspunkte

`netzanschlusspunkte` · Schlüssel `NetzanschlusspunktMastrNummer` (`SAN…`, `GAN…`)

Die Punkte, an denen eine Lokation an ein Netz angeschlossen ist. Die Tabelle enthält:

- Spannungsebene
- Netzanschlusskapazität und maximale Ein- und Ausspeiseleistung
- Bilanzierungsgebiet und Regelzone
- Marktgebiet und Gasqualität
- Kennzeichen „noch in Planung“

Der Netzanschlusspunkt verweist auf Lokation, Netz und Netzbetreiber.

#### Netze

`netze` · Schlüssel `MastrNummer` (`SNE…`, `GNE…`)

Strom- und Gasnetze mit Sparte, Bezeichnung, Bundesland, Marktgebiet (Gas) und Bilanzierungsgebieten (Strom).
Weitere Angaben: ob Kunden angeschlossen sind und ob es ein geschlossenes Verteilernetz ist. Jedes Netz hat genau einen
Netzbetreiber, der in `Marktakteure.Netz` auf sein Netz verweist.

### Begriffe (A–Z)

**ACER-Code**: Registrierungsnummer eines Marktteilnehmers nach **REMIT**, vergeben bei der Registrierung bei der
Bundesnetzagentur für das europäische Register der EU-Agentur ACER. Spalte `AcerCode` der Marktakteure.

**Anlage**: Im MaStR die Zusammenfassung von Einheiten nach einem rechtlichen Anlagenbegriff, z. B. EEG-Anlage oder
KWK-Anlage. Siehe **Einheit** und **Gruppierungsobjekt**.

**Anlagenbetreiber**: Marktakteur (`ABR…`), der Einheiten betreibt und für deren Daten im MaStR verantwortlich ist.
Spalte `AnlagenbetreiberMastrNummer` der Einheiten. Ein Betreiberwechsel steht in `AltAnlagenbetreiberMastrNummer` und
`DatumDesBetreiberwechsels`.

**Anlagenregister**: Register der Bundesnetzagentur für EEG-Anlagen von 2014 bis Anfang 2019, abgelöst durch das MaStR.
Die frühere Anlagenkennziffer steht in `AnlagenkennzifferAnlagenregister` der EEG-Anlagen.

**Anlagenschlüssel (EEG)**: Kennziffer, die der Netzbetreiber zur Identifikation einer EEG-Anlage vergibt (Spalte
`AnlagenschluesselEeg`).

**Ausschreibung, Zuschlag**: Für größere Anlagen ermittelt die Bundesnetzagentur die Höhe der Förderung nach EEG oder
KWKG in Ausschreibungen. Wer einen Zuschlag erhalten hat, ist in `AusschreibungZuschlag` markiert und hat eine
`Zuschlagsnummer`. Bei Solar steht zusätzlich die bezuschlagte Gebotsmenge in `ZugeordneteGebotsmenge`.

**Betriebsstatus**: Zustand einer Einheit: *In Planung*, *In Betrieb*, *Vorübergehend stillgelegt* oder *Endgültig
stillgelegt* (Spalte `EinheitBetriebsstatus`). EEG-, KWK- und Speicheranlagen haben einen eigenen Betriebsstatus, der
sich aus ihren Einheiten ergibt (`AnlageBetriebsstatus`).

**Bilanzierungsgebiet**: Gebiet eines Stromnetzbetreibers, in dem Einspeisung und Entnahme für die Abrechnung der
Bilanzkreise zusammengefasst werden. Gekennzeichnet durch einen Y-Code (siehe **EIC**).

**Bruttoleistung**: Elektrische Leistung einer Einheit an den Generatorklemmen in kW. Bei Solaranlagen ist das die
Summe der Modulleistungen (kWp). Siehe auch **Nettonennleistung**.

**Bundesland**: Im MaStR gibt es zwei Bundesland-Kataloge mit gleichen Namen, aber unterschiedlichen IDs: einen für den
Standort von Einheiten (Kategorie „BundeslaenderEinheiten“) und einen für Marktakteure und Netze (Kategorie
„Bundesland“).

**Bürgerenergie**: Kennzeichen für Einheiten einer Bürgerenergiegesellschaft nach dem EEG. Das sind lokal verankerte
Gesellschaften, an denen vor allem Bürgerinnen und Bürger aus der Umgebung beteiligt sind. Für sie gelten im EEG
Sonderregeln, z. B. bei Ausschreibungen.

**Datenverantwortung**: Für Einheiten und Gruppierungsobjekte ist der Anlagenbetreiber verantwortlich. Für Lokationen
und Netzanschlusspunkte ist der Netzbetreiber verantwortlich, an dessen Netz die Lokation angeschlossen ist.

**Direktvermarktung**: Verkauf des Stroms einer Einheit über einen Direktvermarkter an der Börse statt fester
Einspeisevergütung. `FernsteuerbarkeitDv` gibt an, ob der Direktvermarkter die Einheit fernsteuern kann.

**EEG**: Erneuerbare-Energien-Gesetz, regelt Netzanschluss, Vergütung und Förderung von Strom aus erneuerbaren Energien.

**EEG-Anlage**: Anlage im Sinne des EEG. Im MaStR ist sie ein eigenes Objekt (`EEG…`) mit den Daten, die für die
Förderung nach EEG gelten, z. B. EEG-Inbetriebnahmedatum oder Zuschlag. Das Objekt existiert auch dann, wenn Anlage und
Einheit identisch sind, z. B. bei Wind und Solar. Tabellen `AnlagenEeg…`.

**EEG-Inbetriebnahmedatum**: Inbetriebnahmedatum der EEG-Anlage, maßgeblich für Vergütung und Förderdauer. Es kann vom
**Inbetriebnahmedatum** der Einheit abweichen, z. B. wenn Module oder Generatoren ersetzt wurden.

**EIC (Energy Identification Code)**: Europäischer Code zur Identifikation im Energiemarkt. Im MaStR kommen vor:

- W-Code einer Erzeugungseinheit (`Weic`)
- Y-Code eines Bilanzierungsgebiets (`Yeic`)

**Einheit**: Kleinste technische Einrichtung, die Strom oder Gas erzeugt, speichert oder verbraucht. Bei konventionellen
Kraftwerken ist das z. B. ein Generator, bei Wind eine einzelne Windenergieanlage. Solarmodule, die zur gleichen Zeit
vom gleichen Betreiber am gleichen Ort in Betrieb gehen, werden zusammen als eine Einheit registriert. Die Einheiten
stehen in den Tabellen `Einheiten…`.

**Einheitentyp**: Art einer Einheit, z. B. Windeinheit oder Gasverbrauchseinheit (Tabelle `Einheitentypen`).

**Einsatzverantwortlicher**: Marktakteur, der über den Einsatz einer Einheit entscheidet (z. B. für Redispatch).
Angegeben mit seiner **Marktpartner-ID**.

**Einspeisungsart**: *Volleinspeisung* (der gesamte Strom geht ins Netz) oder *Teileinspeisung* (ein Teil wird selbst
verbraucht).

**Energieträger**: Primärenergie, aus der eine Einheit Strom erzeugt, z. B. Wind, solare Strahlungsenergie, Biomasse,
Erdgas oder Braunkohle. Die Einheiten-Tabellen sind nach Energieträgern aufgeteilt. Die Spalte `Energietraeger`
präzisiert ihn, z. B. bei Verbrennung.

**Ertüchtigung**: Maßnahme, die Leistungsfähigkeit oder Effizienz einer Wasserkraftanlage verbessert (z. B. neue
Turbine). Für sie gelten im EEG besondere Regeln (Tabelle `Ertuechtigungen`).

**Fernsteuerbarkeit**: Ob Netzbetreiber (`FernsteuerbarkeitNb`) oder Direktvermarkter (`FernsteuerbarkeitDv`) die
Leistung einer Einheit aus der Ferne regeln können.

**Flächenentwicklungsplan**: Plan des Bundesamts für Seeschifffahrt und Hydrographie (BSH) für die Gebiete der
Offshore-Windparks in Nord- und Ostsee. Spalten `GebietNachDemFlaechenentwicklungsplan…` der Windeinheiten.

**Flexibilitätsprämie**: EEG-Prämie für bestehende Biogasanlagen, die zusätzliche Leistung für eine bedarfsgerechte
Stromerzeugung bereithalten (Spalten `Biogas…FlexiPraemie`).

**Flugwindenergieanlage**: Windenergieanlage, die in der Höhe fliegt, z. B. an einem Drachen oder Fluggerät, mit
Flughöhe und Flugradius.

**Gemeindeschlüssel**: Amtlicher Gemeindeschlüssel (AGS) der Gemeinde des Standorts, achtstellig.

**Genehmigung**: Behördliche Genehmigung für Bau oder Betrieb von Einheiten, z. B. nach Bundes-Immissionsschutzgesetz.
Sie ist ein eigenes Objekt (`SGE…`, Tabelle `EinheitenGenehmigung`), auf das die Einheiten über `GenMastrNummer`
verweisen.

**Gesamtdatenexport**: Täglicher Export aller öffentlichen Daten des MaStR durch die Bundesnetzagentur als ZIP-Archiv mit
XML-Dateien. Zu den Stichtagen 1.1., 1.4., 1.7. und 1.10. werden Quartalsexporte aufbewahrt. Er ist die Datenquelle
dieser App.

**Geschlossenes Verteilernetz**: Netz, das Energie innerhalb eines abgegrenzten Gebiets verteilt, z. B. eines
Industrie- oder Gewerbegebiets (§ 110 EnWG). Im MaStR wird es wie ein öffentliches Netz behandelt (`Netze`, Spalte
`GeschlossenesVerteilnetz`).

**Grenzkraftwerk**: Kraftwerk, das auch in ein ausländisches Netz einspeist. Die in Deutschland nutzbare Leistung steht
in `NettonennleistungDeutschland`.

**Gruppierungsobjekt**: Objekt, das mehrere Einheiten zusammenfasst. Es gibt fünf:

- EEG-Anlage
- KWK-Anlage
- Stromspeicher
- Gasspeicher
- Genehmigung

Die Einheiten verweisen darauf, das Gruppierungsobjekt listet umgekehrt seine Einheiten
(`VerknuepfteEinheitenMaStRNummern`).

**Höchstbemessungsleistung**: Für Biogasanlagen, die vor August 2014 in Betrieb gingen, die Leistung, bis zu der die
EEG-Vergütung gezahlt wird. Für darüber hinaus erzeugten Strom gibt es nur noch den Marktwert.

**Inbetriebnahmedatum**: Datum der ersten Inbetriebnahme einer Einheit. Ist eine Einheit umgezogen, steht das Datum am
aktuellen Standort in `InbetriebnahmedatumAmAktuellenStandort`. Für geplante Einheiten gibt es
`GeplantesInbetriebnahmedatum`.

**Katalog**: Liste fester Auswahlwerte, z. B. für Bundesland, Betriebsstatus oder Hersteller. Die Werte stehen in
`Katalogwerte`, ihre Kategorien in `Katalogkategorien`. **Systemkataloge** sind die eigenen Tabellen `Einheitentypen`,
`Lokationstypen`, `Marktfunktionen` und `Marktrollen`.

**Kombibetrieb**: Mehrere Verbrennungseinheiten arbeiten zusammen, z. B. Gas- und Dampfturbine eines GuD-Kraftwerks
(Spalten `AnlageIstImKombibetrieb` und `MastrNummernKombibetrieb`).

**Koordinaten**: Breiten- und Längengrad des Standorts einer Einheit. Sie fehlen bei kleinen Einheiten (siehe
**Vertrauliche Daten**) und oft bei Einheiten in Planung. mastr-tool ergänzt beim Import die **UTM-Koordinaten**.

**Kraftwerksnummer**: Nummer der Bundesnetzagentur für größere Kraftwerke (`BNA…`), wie in der Kraftwerksliste der
BNetzA.

**KWK-Anlage**: Anlage, die gleichzeitig Strom und nutzbare Wärme erzeugt (Kraft-Wärme-Kopplung), gefördert nach dem
KWKG. Sie ist ein eigenes Objekt (`KWK…`, Tabelle `AnlagenKwk`).

**Lokation (technische)**: Fasst alle Einheiten zusammen, die technisch miteinander verbunden und gemeinsam über einen
oder mehrere Netzanschlusspunkte an das Netz angeschlossen sind, unabhängig vom Energieträger. Es gibt sie für
Stromerzeugung (`SEL…`), Stromverbrauch (`SVL…`), Gaserzeugung (`GEL…`) und Gasverbrauch (`GVL…`). Sie wird auch für
eine einzelne Einheit angelegt. Die Lokation bildet nur die Technik ab; Verträge und Abrechnung sind Sache von Markt-
und Messlokation.

**Marktakteur**: Natürliche Person oder Organisation, die eine **Marktfunktion** wahrnimmt. Ein Unternehmen mit
mehreren Funktionen hat mehrere Marktakteure, z. B. ein Stadtwerk als Stromnetzbetreiber und als Akteur im Strommarkt.
Tabelle `Marktakteure`.

**Marktfunktion**: Übergeordnete Aufgabe eines Marktakteurs, z. B. Anlagenbetreiber, Stromnetzbetreiber,
Gasnetzbetreiber, Akteur im Strom- oder Gasmarkt. Sie bestimmt das Präfix der MaStR-Nummer (siehe **MaStR-Nummern**).

**Marktgebiet**: Gebiet des Gashandels. In Deutschland gibt es seit Oktober 2021 nur noch das Marktgebiet **Trading Hub
Europe (THE)**.

**Marktlokation, Messlokation**: Begriffe der Marktkommunikation für Abrechnung und Messung, z. B. Zählpunkt. Die
Messlokation des Netzanschlusspunkts steht in `Netzanschlusspunkte.Messlokation`. Meist stimmen technische Lokation,
Marktlokation und Messlokation überein.

**Marktpartner-ID (MP-ID)**: 13-stellige Nummer eines Marktteilnehmers in der Marktkommunikation der Energiewirtschaft
(BDEW- bzw. DVGW-Codenummer).

**Marktrolle**: Genauere Rolle innerhalb einer Marktfunktion, z. B. Anschluss- oder Übertragungsnetzbetreiber,
Messstellenbetreiber, Bilanzkreisverantwortlicher, Stromlieferant oder Transportkunde. Sie wird als Suffix aus zwei
Buchstaben an die MaStR-Nummer angehängt (Tabellen `MarktakteureUndRollen` und `Marktrollen`).

**MaStR (Marktstammdatenregister)**: Register der Bundesnetzagentur für alle Anlagen und Akteure des Strom- und
Gasmarkts in Deutschland, seit Januar 2019 online. Grundlage sind das Energiewirtschaftsgesetz und die **MaStRV**.

**MaStR-Nummer**: Eindeutige Nummer jedes Objekts im MaStR (siehe **MaStR-Nummern** oben).

**MaStRV**: Marktstammdatenregisterverordnung. Sie regelt, wer was registrieren muss und welche Daten veröffentlicht
werden.

**Mieterstrom**: Solarstrom, der an Mieter im selben Gebäude oder Quartier geliefert wird. Dafür gibt es den
Mieterstromzuschlag nach dem EEG (Spalten `Mieterstrom…` der Solar-EEG-Anlagen).

**Migrierte Einheiten**: Einheiten, die die Bundesnetzagentur vor dem Start des MaStR aus früheren Datenbeständen
übernommen hat (z. B. Anlagenregister, PV-Meldeportal). Siehe Spalte `NichtVorhandenInMigriertenEinheiten`.

**Nachtkennzeichnung**: Rote Warnleuchten von Windenergieanlagen für die Luftfahrt. Die bedarfsgesteuerte
Nachtkennzeichnung leuchtet nur, wenn sich ein Flugzeug nähert.

**Nettonennleistung**: Höchste elektrische Dauerleistung einer Einheit abzüglich des Eigenbedarfs in kW. Bei Solar- und
Batterieeinheiten ist sie der kleinere Wert aus Modulleistung und Wechselrichterleistung. Die Karten dieser App zeigen
die Nettonennleistung an.

**Netz**: Strom- oder Gasnetz (`SNE…`, `GNE…`, Tabelle `Netze`). Jeder Netzbetreiber hat genau ein Netz.

**Netzanschlusspunkt**: Stelle, an der eine Lokation an ein Netz angeschlossen ist (`SAN…`, `GAN…`, Tabelle
`Netzanschlusspunkte`). Er ist das Bindeglied zwischen Lokation, Netz und Netzbetreiber.

**Netzbetreiber**: Marktakteur, der ein Strom- (`SNB…`) oder Gasnetz (`GNB…`) betreibt. Wichtige Marktrollen sind:

- **Anschlussnetzbetreiber**: an dessen Netz eine Einheit angeschlossen ist
- **Übertragungsnetzbetreiber** (Strom): 50Hertz, Amprion, TenneT, TransnetBW
- **Fernleitungsnetzbetreiber** (Gas)

**Netzbetreiberprüfung**: Prüfung der Angaben einer Einheit durch den Netzbetreiber. Der Status (*Geprüft* oder *In
Prüfung*) steht in `NetzbetreiberpruefungStatus`.

**Netzreserve, Kapazitätsreserve, Sicherheitsbereitschaft**: Kraftwerke außerhalb des Strommarkts, die die
Übertragungsnetzbetreiber für die Versorgungssicherheit vorhalten (EnWG). Spalten `NetzreserveZugeordnet`,
`KapazitaetsreserveZugeordnet` und `SicherheitsbereitschaftAbDatum`.

**Nicht vorhanden (`_nv`)**: Bei manchen Pflichtfeldern kann der Betreiber angeben, dass es den Wert nicht gibt. Dann
gibt es eine Spalte mit dem Suffix `_nv` (z. B. `Hausnummer_nv`). Ist sie wahr, ist der Wert der eigentlichen Spalte zu
ignorieren.

**PV-Meldeportal**: Früheres Meldeportal der Bundesnetzagentur für Photovoltaikanlagen. Die dortige
Registrierungsnummer steht in `RegistrierungsnummerPvMeldeportal`.

**Referenzertrag**: Rechnerischer Ertrag einer Windenergieanlage desselben Typs an einem festgelegten
Referenzstandort. Das Verhältnis von Ertrag zu Referenzertrag beschreibt die Güte eines Windstandorts und bestimmt die
EEG-Vergütung mit (Spalten `Verhaeltnis…` der Wind-EEG-Anlagen).

**Regelzone**: Gebiet, in dem ein Übertragungsnetzbetreiber für das Gleichgewicht von Erzeugung und Verbrauch sorgt. In
Deutschland gibt es vier: 50Hertz, Amprion, TenneT und TransnetBW.

**REMIT**: EU-Verordnung über die Integrität und Transparenz des Energiegroßhandelsmarkts (Verordnung (EU)
Nr. 1227/2011). Sie verpflichtet die Teilnehmer am Energiegroßhandel zur Registrierung.

**Spannungsebene**: Ebene des Stromnetzes am Netzanschlusspunkt, von Höchst- über Hoch- und Mittel- bis
Niederspannung, einschließlich der Umspannebenen dazwischen.

**Speicher**: Ein Speicher besteht im MaStR aus zwei Objekten:

- **Einheit**: erzeugt aus der gespeicherten Energie Strom bzw. speist Gas aus (Leistungsdaten).
- **Speicher**: ein Gruppierungsobjekt, das die Energie aufbewahrt (Kapazität). Tabellen `AnlagenStromSpeicher` und
  `AnlagenGasSpeicher`.

**Steckerfertige Solaranlage**: Kleine Solaranlage, die per Stecker an den Hausstromkreis angeschlossen wird
(„Balkonkraftwerk“). Seit 2024 vereinfacht registrierbar und inzwischen ein großer Teil der Solareinheiten.

**Stilllegung**: Eine Einheit kann vorübergehend (`DatumBeginnVoruebergehendeStilllegung`, Wiederaufnahme in
`DatumWiederaufnahmeBetrieb`) oder endgültig (`DatumEndgueltigeStilllegung`) stillgelegt werden. Siehe
**Betriebsstatus**.

**Systemstatus**: Status des Datensatzes im Register: *Aktiviert*, *Deaktiviert* oder *Gelöscht*. Die Einheiten-Tabellen
enthalten nur aktivierte Einheiten, die übrigen stehen in `GeloeschteUndDeaktivierteEinheiten`.

**UTM-Koordinaten**: Zone, Ostwert und Nordwert im UTM-Koordinatensystem (Spalten `UTM_zone`, `UTM_ost`, `UTM_nord`).
Sie sind nicht Teil des MaStR: mastr-tool berechnet sie beim Import aus Breiten- und Längengrad.

**Vertrauliche Daten**: Nach § 15 MaStRV werden nicht alle Daten veröffentlicht. Es fehlen:

- Daten von Marktakteuren, die natürliche Personen sind (z. B. Name und Adresse)
- Straße, Hausnummer, Flurstück und Koordinaten von Erzeugungseinheiten mit höchstens 30 kW

Deshalb haben z. B. die meisten Solareinheiten keine Koordinaten und erscheinen nicht auf der Seite **Karten**.

### Quellen

- [Dokumentation des Gesamtdatenexports](https://www.marktstammdatenregister.de/MaStRHilfe/files/gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport/Dokumentation%20MaStR%20Gesamtdatenexport.pdf)
  (Bundesnetzagentur)
- [Struktur der Daten zu Marktakteuren, Einheiten und Gruppierungsobjekten](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Datenstruktur_(Marktakteure_Einheiten_und_Gruppierungsobjekte)_final.pdf)
  (Bundesnetzagentur)
- [MaStR-Nummernkonzept](https://www.marktstammdatenregister.de/MaStRHilfe/files/regHilfen/MaStR-Nummernkonzept.pdf)
  (Bundesnetzagentur)
- [Marktstammdatenregisterverordnung (MaStRV)](https://www.gesetze-im-internet.de/mastrv/)
- [Hilfe des Marktstammdatenregisters](https://www.marktstammdatenregister.de/MaStRHilfe/)
