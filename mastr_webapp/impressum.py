import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output
from pathlib import Path
import tomllib

impressum_div = dbc.Container(
    id="div-impressum",
    fluid=True,
    children=[
        html.H3(
            "Impressum",
            className="border-bottom pb-3 mb-3",
        ),
        dcc.Markdown(id="md-impressum"),
    ],
)


def _app_version():
    try:
        with open("pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["version"]
    except Exception:
        return None


@callback(Output("md-impressum", "children"), Input("url", "pathname"))
def refresh_impressum(pathname):
    try:
        impressum = Path("assets/impressum.md").read_text(encoding="utf-8")
    except Exception as e:
        print(e)
        impressum = "NA"
    version = _app_version()
    if version:
        impressum += f"\n\n---\n\n**Version:** `{version}`\n"
    return impressum
