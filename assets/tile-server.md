Der Tile-Server liefert die Einheiten des Marktstammdatenregisters als **Mapbox Vector Tiles (MVT)** – live aus der
PostGIS-Datenbank, ein Layer je Energieträger. Eine Kachel enthält nur die Punkte; die Hintergrundkarte kommt vom
Client (OpenStreetMap, basemap.de, …). Als Client funktionieren MapLibre, OpenLayers, Leaflet (mit Plugin) und QGIS.

Der öffentliche Server läuft unter **{{TILES_URL}}** – ohne Schlüssel, CORS für alle Origins offen.

### Adressen

| Adresse                       | Inhalt                                           |
|-------------------------------|--------------------------------------------------|
| `GET /catalog`                | alle Layer                                       |
| `GET /tiles.wind`             | TileJSON eines Layers (Kachel-URL, Beschreibung) |
| `GET /tiles.wind/{z}/{x}/{y}` | die Kachel                                       |
| `GET /health`                 | Healthcheck, `200 OK`                            |

Die Kachel-URL hat keine Endung; `…/{z}/{x}/{y}.pbf` leitet mit `301` auf die endungslose URL um, ebenso ein
`/tiles/`-Präfix. Nicht öffentlich sind `DELETE /cache/{source_id}` (Cache leeren) und `/_/metrics` (Prometheus);
beide antworten mit `403`.

Eine Kachel ohne Einheiten antwortet mit `204 No Content` – das ist kein Fehler. Koordinaten außerhalb der Zoomstufe
(`x` oder `y` ≥ 2^z) ergeben ebenfalls `204`.

### Layer und Zoomstufen

Ein Layer je Energieträger, jeweils als Quelle `tiles.<layer>`. Alle Layer liefern Zoom 0–14; darüber antwortet
Martin weiterhin, die Kacheln kommen dann aber ungecacht aus der Datenbank (`cache.maxzoom: 14`).

| Layer                    | Inhalt                                               | Zoom | Bündelung                                            |
|--------------------------|------------------------------------------------------|------|------------------------------------------------------|
| `tiles.wind`             | Windenergieanlagen                                   | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.solar`            | Solaranlagen                                         | 0–14 | z0–9 je Rasterzelle (`anzahl`, `kw`), ab z10 einzeln |
| `tiles.biomasse`         | Biomasseanlagen                                      | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.wasser`           | Wasserkraftanlagen                                   | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.geothermie`       | Geothermie-, Grubengas- und Druckentspannungsanlagen | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.stromspeicher`    | Stromspeicher                                        | 0–14 | z0–9 je Rasterzelle (`anzahl`, `kw`), ab z10 einzeln |
| `tiles.kernkraft`        | Kernkraftwerke                                       | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.verbrennung`      | Verbrennungsanlagen                                  | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.gaserzeuger`      | Gaserzeuger                                          | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.gasspeicher`      | Gasspeicher                                          | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.gasverbraucher`   | Gasverbraucher                                       | 0–14 | z0–6 je Rasterzelle (`anzahl`, `kw`), ab z7 einzeln  |
| `tiles.stromverbraucher` | Stromverbrauchseinheiten                             | 0–14 | z0–6 je Rasterzelle (`anzahl`), ab z7 einzeln        |

Unterhalb einer Zoomstufe bündelt jeder Layer seine Punkte je Rasterzelle (64 × 64 Zellen pro Kachel) zu einem
Feature mit `anzahl` und `kw`; darüber kommt jede Einheit einzeln. Die Grenze hängt an der Zahl der Einheiten: Solar
und Stromspeicher bündeln bis Zoom 10, die übrigen Layer unterhalb von Zoom 7. `tiles.stromverbraucher` hat im MaStR
keine Leistungsspalte, seine Zellen tragen nur `anzahl`.

Ohne Bündelung wäre eine z0-Kachel von `tiles.wind` 4,7 MB groß (43.000 Einheiten, gzip 1,5 MB); gebündelt sind es
rund 50–100 kB. Eine z5-Kachel mit allen Solaranlagen enthielte sonst hunderttausende Punkte.

Ab der Grenze kommen die Einzelpunkte mit allen Attributen. In dichten Regionen sind diese Kacheln deutlich größer als
die gebündelten: eine z7-Kachel von `tiles.wind` über Nordrhein-Westfalen liegt bei bis zu 600 kB (gzip 220 kB),
`tiles.verbrennung` bei bis zu 440 kB (gzip 190 kB). Wer die Kacheln selbst vorlädt, sollte das bei diesen Zoomstufen
einplanen.

### Attribute

Gebündelte Features (unterhalb der Zoomgrenze) tragen nur `anzahl` und `kw`; die folgenden Attribute gelten für die
Einzelpunkte ab der Grenze.

Jedes Feature hat `mastr_nr`, `name`, `kw` (Nettonennleistung), `status` (Katalog-ID des Betriebsstatus) und – wo
vorhanden – `park` (Windpark, Solarpark, Kraftwerk). Dazu kommen für alle Layer `inbetriebnahme` und `stillgelegt_am`
(ISO-Datum als Text) und `betreiber` (Firmenname des Anlagenbetreibers, bei natürlichen Personen Vor- und Nachname).
In den Strom-Erzeugungs- und Speichertabellen zusätzlich `brutto_kw`, `fernsteuerbar_nb`, `fernsteuerbar_dv` und
`hochspannung`; die Gas- und Verbrauchertabellen kennen diese Spalten im MaStR nicht.

| Layer                    | zusätzliche Felder                                                                           |
|--------------------------|----------------------------------------------------------------------------------------------|
| `tiles.wind`             | `nabenhoehe`, `rotordurchmesser`, `hersteller`, `typ`, `offshore`, `buergerenergie`          |
| `tiles.solar`            | `art`, `module`, `ausrichtung`, `neigung`, `flaeche_ha`, `speicher_am_ort`, `buergerenergie` |
| `tiles.biomasse`         | `brennstoff`, `biomasseart`, `technologie`                                                   |
| `tiles.wasser`           | `art`                                                                                        |
| `tiles.geothermie`       | `technologie`                                                                                |
| `tiles.stromspeicher`    | `batterietechnologie`, `acdc`, `einsatzort`, `pumpspeicher`, `notstrom`, `wechselrichter`    |
| `tiles.kernkraft`        | `block`, `technologie`                                                                       |
| `tiles.verbrennung`      | `brennstoff`, `kombibetrieb`, `einsatzort`, `notstrom`, `block`                              |
| `tiles.gaserzeuger`      | `technologie`                                                                                |
| `tiles.gasspeicher`      | `speicherart`, `arbeitsgasvolumen`, `ausspeicherleistung`                                    |
| `tiles.gasverbraucher`   | `dient_der_stromerzeugung`                                                                   |
| `tiles.stromverbraucher` | `anzahl_groesser_50mw`                                                                       |

Katalogwerte (`status`, `art`, `brennstoff`, `hersteller`, `technologie`, …) bleiben IDs; den Text dazu enthält die
Tabelle `Katalogwerte` (siehe **Glossar**).

### QGIS

*Layer → Add Layer → Add Vector Tile Layer → New Generic Connection*, URL `{{TILES_URL}}/tiles.wind/{z}/{x}/{y}`,
Zoom 0–14, Style URL leer. Für die anderen Energieträger nur `tiles.wind` ersetzen.

### MapLibre GL JS

```js
map.addSource("mastr-wind", {
  type: "vector",
  tiles: ["{{TILES_URL}}/tiles.wind/{z}/{x}/{y}"],
  minzoom: 0,
  maxzoom: 14,
});
map.addLayer({ id: "mastr-wind", type: "circle", source: "mastr-wind", "source-layer": "wind" });
```

### OpenLayers

```js
new VectorTileLayer({
  source: new VectorTileSource({
    format: new MVT(),
    url: "{{TILES_URL}}/tiles.wind/{z}/{x}/{y}",
  }),
});
```

### Leaflet

Mit dem Plugin `Leaflet.VectorGrid`:

```js
L.vectorGrid.protobuf("{{TILES_URL}}/tiles.wind/{z}/{x}/{y}", {
  vectorTileLayerStyles: { wind: { color: "#18bc9c" } },
});
```

### curl

```bash
curl -s "{{TILES_URL}}/tiles.wind/10/541/342" -o tile.pbf
```

### Aktualität und Cache

Die Daten stammen aus dem zuletzt importierten Dump; den Zeitpunkt nennt die Seite **Tabellen**. Martin hält die
Kacheln 12 h im Cache, nach jedem Import leert mastr-tool den Cache, damit die Karte sofort die neuen Daten zeigt.
Ausgeliefert wird `Cache-Control: public, max-age=3600`.

Enthalten sind nur Einheiten mit Koordinaten – das MaStR veröffentlicht Koordinaten erst ab 30 kW Nettonennleistung.
