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

### Layer und Zoomstufen

Ein Layer je Energieträger, jeweils als Quelle `tiles.<layer>`. Alle Layer liefern Zoom 0–14; darüber antwortet
Martin weiterhin, die Kacheln kommen dann aber ungecacht aus der Datenbank (`cache.maxzoom: 14`).

| Layer                    | Inhalt                                               | Zoom | Bündelung                                            |
|--------------------------|------------------------------------------------------|------|------------------------------------------------------|
| `tiles.wind`             | Windenergieanlagen                                   | 0–14 | –                                                    |
| `tiles.solar`            | Solaranlagen                                         | 0–14 | z0–9 je Rasterzelle (`anzahl`, `kw`), ab z10 einzeln |
| `tiles.biomasse`         | Biomasseanlagen                                      | 0–14 | –                                                    |
| `tiles.wasser`           | Wasserkraftanlagen                                   | 0–14 | –                                                    |
| `tiles.geothermie`       | Geothermie-, Grubengas- und Druckentspannungsanlagen | 0–14 | –                                                    |
| `tiles.stromspeicher`    | Stromspeicher                                        | 0–14 | z0–9 je Rasterzelle (`anzahl`, `kw`), ab z10 einzeln |
| `tiles.kernkraft`        | Kernkraftwerke                                       | 0–14 | –                                                    |
| `tiles.verbrennung`      | Verbrennungsanlagen                                  | 0–14 | –                                                    |
| `tiles.gaserzeuger`      | Gaserzeuger                                          | 0–14 | –                                                    |
| `tiles.gasspeicher`      | Gasspeicher                                          | 0–14 | –                                                    |
| `tiles.gasverbraucher`   | Gasverbraucher                                       | 0–14 | –                                                    |
| `tiles.stromverbraucher` | Stromverbrauchseinheiten                             | 0–14 | –                                                    |

Solar und Stromspeicher haben Millionen Einheiten. Unterhalb von Zoom 10 bündelt die Funktion die Punkte deshalb je
Rasterzelle (64 × 64 Zellen pro Kachel) zu einem Feature mit `anzahl` und `kw`; ab Zoom 10 kommt jede Einheit einzeln.
Eine z5-Kachel enthielte sonst hunderttausende Punkte und würde mehrere Megabyte groß.

### Attribute

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
