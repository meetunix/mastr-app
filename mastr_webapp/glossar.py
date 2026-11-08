from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

glossar_div = dbc.Container(
    id="div-glossar",
    fluid=True,
    children=[
        html.H3(
            "Glossar",
            className="border-bottom pb-3 mb-3",
        ),
        dcc.Markdown(id="md-glossar"),
    ],
)


@callback(Output("md-glossar", "children"), Input("url", "pathname"))
def refresh_glossar(pathname):
    try:
        return Path("assets/glossar.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(e)
        return "NA"
