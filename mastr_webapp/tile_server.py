from pathlib import Path

import dash_bootstrap_components as dbc
from dash import Input, Output, callback, dcc, html

from .constants import MASTR_TILES_PUBLIC_URL

# the markdown is deployment independent, the URL of the tile server is not
TILES_URL_PLACEHOLDER = "{{TILES_URL}}"

tile_server_div = dbc.Container(
    id="div-tile-server",
    fluid=True,
    children=[
        html.H3(
            "Tile-Server",
            className="border-bottom pb-3 mb-3",
        ),
        dcc.Markdown(id="md-tile-server"),
    ],
)


@callback(Output("md-tile-server", "children"), Input("url", "pathname"))
def refresh_tile_server(pathname):
    try:
        markdown = Path("assets/tile-server.md").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(e)
        return "NA"
    return markdown.replace(TILES_URL_PLACEHOLDER, MASTR_TILES_PUBLIC_URL)
