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
