# Release a new version


0. Merge changes into main
1. Update the version Number in pyproject.toml
2. Update the Helm Chart version in helm/mastr-app/Chart.yaml
3. `uv lock -U`
3. Tag the commit
4. Push the changes