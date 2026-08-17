# mastr-app

**in development**

Webanwendung zur Bereitstellung und Suche in den Daten des Marktstammdatenregisters und Download von Filterergebnissen
und Teildatensätzen (z.B. Alle Windkraftanlagen Deutschlands oder Thüringens) in alternativen Formaten (Parquet, CSV,
Excel).

Der Import, die Anreicherung und die Konvertierung der Daten geschieht im [mastr-tool](https://codeberg.org/nachtsieb/mastr-tool)-Projekt.

Der aktuelle Stand der Anwendung kann unter https://mastr.nachtsieb.de getestet werden.

## Download der konvertierten Formate

Die konvertierten Daten werden täglich aus dem Marktstammdatenregister erzeugt und stehen für den automatisierten
Download unter https://mastr-static.nachtsieb.de zur Verfügung.

Die Lizenzbestimmungen finden sich unter https://mastr.nachtsieb.de/impressum.

## Deployment auf Kubernetes mit Helm

Im Verzeichnis [`helm/mastr-app`](helm/mastr-app) liegt ein einfaches Helm-Chart für das Deployment auf einem
Kubernetes-Cluster. Es erzeugt ein Deployment, einen Service und optional einen Ingress.

### Minimalistische `values.yaml`

```yaml
image:
  repository: nachtsieb/mastr-app
  tag: latest

env:
  MASTR_STATIC_URL: https://mastr-static.example.com
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
helm install mastr-app ./helm/mastr-app -f values.yaml
```

### Upgraden

```bash
helm upgrade mastr-app ./helm/mastr-app -f values.yaml
```

Wird ein neues Image unter demselben Tag (z. B. `latest`) gepusht, reicht `helm upgrade` allein nicht aus, da der
Pod-Template unverändert bleibt. In diesem Fall zusätzlich einen Rollout anstoßen:

```bash
kubectl rollout restart deployment/mastr-app
```

### Deinstallieren

```bash
helm uninstall mastr-app
```
