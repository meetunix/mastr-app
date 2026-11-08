# mastr-app

Webanwendung zur Bereitstellung und Suche in den Daten des Marktstammdatenregisters und Download von Filterergebnissen
und Teildatensätzen (z.B. Alle Windkraftanlagen oder Verbrennungseinheiten Deutschlands oder Thüringens) in
alternativen Formaten (Parquet, CSV, Excel). Außerdem kann ein **vollständiger Datenbankauszug** des
Marktstammdatenregisters als PostgreSQL-Dump heruntergeladen werden.

Der Import, die Anreicherung und die Konvertierung der Daten geschieht im [mastr-tool](https://codeberg.org/nachtsieb/mastr-tool)-Projekt.

Der aktuelle Stand der Anwendung kann unter https://mastr.nachtsieb.de getestet werden.

## Download der konvertierten Formate

Die konvertierten Daten werden **täglich** aus dem Marktstammdatenregister erzeugt und stehen für den automatisierten
Download unter https://mastr-static.nachtsieb.de zur Verfügung.

Die Lizenzbestimmungen finden sich unter https://mastr.nachtsieb.de/impressum.

## Deployment mit Docker

```bash
MASTR_STATIC_PUBLIC_URL=https://mastr-static.example.com docker compose up -d --build
```

Die WebUI ist anschließend unter `http://127.0.0.1:8081` erreichbar. `MASTR_STATIC_PUBLIC_URL` (öffentliche URL
des mastr-tool-Exportservers) ist Pflicht, `MASTR_STATIC_URL` (interner Zugriff auf die Exporte) ist in der
`docker-compose.yaml` vorkonfiguriert.

Sobald die Anwendung antwortet, schreibt der Container einen Kasten mit Version und URLs ins Log
(`docker compose logs mastr-app`). Die von außen erreichbare URL kommt aus der optionalen Variable `MASTR_APP_URL`
(mehrere URLs durch Komma getrennt); ohne sie zeigt der Container `http://localhost:8081` (die Portfreigabe der
`docker-compose.yaml`). Das Helm-Chart leitet sie aus den Ingress-Hosts ab.

## Deployment auf Kubernetes mit Helm

Im Verzeichnis [`helm/mastr-app`](helm/mastr-app) liegt ein einfaches Helm-Chart für das Deployment auf einem
Kubernetes-Cluster. Es erzeugt ein Deployment, einen Service und optional einen Ingress.

### Minimalistische `values.yaml`

```yaml
image:
  repository: nachtsieb/mastr-app
  tag: latest

env:
  MASTR_STATIC_URL: http://mastr-mastr-tool-static.mastr.svc.cluster.local:8080 # mastr-tool backend - fast access inside cluster
  MASTR_STATIC_PUBLIC_URL: https://mastr-static.example.com

ingress:
  enabled: true
  hosts:
    - host: mastr-app.example.com
      paths:
        - path: /
          pathType: Prefix
```

### Installieren

```bash
helm install mastr-app ./helm/mastr-app -f values.yaml --create-namespace --namespace mastr
```

### Upgraden

```bash
helm upgrade mastr-app ./helm/mastr-app -f values.yaml --namespace mastr
```

Wird ein neues Image unter demselben Tag (z. B. `latest`) gepusht, reicht `helm upgrade` allein nicht aus, da der
Pod-Template unverändert bleibt. In diesem Fall zusätzlich einen Rollout anstoßen:

```bash
kubectl rollout restart deployment/mastr-app --namespace mastr
```

### Deinstallieren

```bash
helm uninstall mastr-app --namespace mastr
```

## Datenbankverbindung (Seite „Karten“)

Die Seite **Karten** liest alle ihre Daten – Standorte, Angaben zu den Einheiten und ihren Betreibern sowie die
Daten der EEG-Anlagen (Wind, Solar, Biomasse, Wasser, Geothermie/Grubengas/Druckentspannung, Stromspeicher) –
direkt aus der PostgreSQL-Datenbank von [mastr-tool](https://codeberg.org/nachtsieb/mastr-tool). Ohne
Datenbankverbindung zeigt die Seite nur einen Hinweis; die Seiten **Tabellen** und **Downloads** nutzen weiterhin
die Exporte und funktionieren auch ohne Datenbank.

Die Karte zeigt die Einheiten eines Energieträgers in einem Bundesland oder in ganz Deutschland, und zwar nur die
Einheiten mit Koordinaten (das MaStR veröffentlicht Koordinaten erst ab 30 kW Nettonennleistung); die Legende nennt die
Anzahl der Einheiten in der Datenbank, der angezeigten und der Einheiten ohne Koordinaten. Für Solar und Stromspeicher
ist ganz Deutschland wegen der Menge der Einheiten nicht auswählbar.

| Variable      | Bedeutung                                                          | Standard |
|---------------|--------------------------------------------------------------------|----------|
| `DB_HOST`     | Host der Datenbank; ohne diese Variable ist die Seite „Karten“ aus | –        |
| `DB_PORT`     | Port                                                               | `5432`   |
| `DB_NAME`     | Name der Datenbank                                                 | `mastr`  |
| `DB_USER`     | Benutzer                                                           | `mastr`  |
| `DB_PASSWORD` | Passwort                                                           | –        |

Die App liest ausschließlich (die Sitzung ist read-only) und öffnet pro Abfrage eine kurze Verbindung mit Timeouts, so
dass sie den Import von mastr-tool nicht blockiert. Empfohlen ist trotzdem eine eigene Rolle mit reinen Leserechten.
Da mastr-tool die Tabellen bei jedem Import neu anlegt, müssen die Leserechte auch für künftige Tabellen gelten
(`mastr` ist die Rolle, mit der mastr-tool importiert):

```sql
CREATE ROLE mastr_app LOGIN PASSWORD 'change-me';
GRANT CONNECT ON DATABASE mastr TO mastr_app;
GRANT USAGE ON SCHEMA public TO mastr_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mastr_app;
ALTER DEFAULT PRIVILEGES FOR ROLE mastr IN SCHEMA public GRANT SELECT ON TABLES TO mastr_app;
```

Die Kartenabfragen nutzen partielle Indizes, die mastr-tool beim Import anlegt (Einheiten mit Koordinaten je
Bundesland, `MapIndices` in `db/entities.py` von mastr-tool). Ohne sie funktioniert die Seite ebenfalls, liest bei Solar
und Stromspeicher aber die ganze Tabelle (bis zu 2 GB). Eine bestehende Datenbank erhält die Indizes beim nächsten
Import oder sofort mit `python import_mastr.py --schema --cache-dir <dir> <dir>` im mastr-tool-Container.

Während eines Imports baut mastr-tool alle Tabellen neu auf. Eine Tabelle gilt erst als vollständig, wenn mastr-tool
nach dem Laden aller Daten ihren Primärschlüssel angelegt hat; bis dahin zeigt die Seite „Karten“ den Hinweis, dass
die Datenbank gerade aktualisiert wird.

**Docker:** Die Variablen werden von der `docker-compose.yaml` durchgereicht, z. B.
`DB_HOST=db.example.com DB_USER=mastr_app DB_PASSWORD=change-me docker compose up -d --build`. In der
`docker-compose.yaml` von mastr-tool (Vollbetrieb inkl. WebUI) ist die Verbindung zur dortigen Datenbank bereits
eingetragen.

**Helm:** Host und ein Secret mit den Schlüsseln `username` und `password` angeben, z. B. das Secret des
mastr-tool-Charts im selben Namespace:

```yaml
database:
  host: mastr-mastr-tool-db.mastr.svc.cluster.local
  existingSecret: mastr-mastr-tool-db
```
