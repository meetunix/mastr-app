from datetime import datetime

import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, callback, Input, Output
from dash.dcc import Dropdown, Store

import mastr_webapp.tables as mastr_tables
from mastr_webapp.download import download_div
from mastr_webapp.impressum import impressum_div, _app_version
from mastr_webapp.strings import *
from mastr_webapp.util_web import shared_client as mastr_static
from mastr_webapp.welcome import welcome_modal

app = Dash(__name__, title="MaStR-App", external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)
server = app.server


dropdown_state = Dropdown(
    [static_table_states[s] for s in TABLE_SOURCE_ENTITY_URL],
    static_table_states[TABLE_SOURCE_ENTITY_URL.WIND_MV],
    id="state-table-dropdown",
    searchable=False,
    clearable=False,
    style={"fontSize": "1.15rem"},
)

div_static_table = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H3(
                            "Tabellen",
                            className="border-bottom pb-3 mb-3",
                        ),
                        html.P(
                            "Übersicht der Windenergieanlagen aus dem Marktstammdatenregister der Bundesnetzagentur.",
                            className="text-muted fs-5 mb-3",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Zeitstempel MaStR-Daten:",
                                    className="col-form-label",
                                    style={"width": "16em", "display": "inline-block"},
                                ),
                                html.Label("NA", id="label-dump-timestamp"),
                            ],
                            title="Datum an dem der MaStR-Datenauszug bei der Bundesnetzagentur erstellt wurde.",
                        ),
                        html.Div(
                            [
                                html.Label(
                                    "Zeitpunkt Import: ",
                                    className="col-form-label",
                                    style={"width": "16em", "display": "inline-block"},
                                ),
                                html.Label("NA", id="label-import-timestamp"),
                            ],
                            title="Zeitpunkt an dem die MaStR-Daten importiert wurden.",
                        ),
                    ]
                )
            ]
        ),
        dbc.Row(
            dbc.Col(
                dropdown_state,
                width="auto",
                style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="div-static-table",
                    children=[
                        dcc.Loading(
                            id="loading-table-1",
                            children=[mastr_tables.get_static_table()],
                            type="circle",
                            className="mb-5",
                        ),
                    ],
                )
            )
        ),
        dbc.Row(
            dbc.Col(
                html.Div(id="div-static-buttons", children=mastr_tables.get_static_table_download())
            )
        ),
        Store(id="stored-static-table"),
        Store(id="stored-selected-rows"),
    ],
    fluid=True,
)

# Update your layout: Add dcc.Location
app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        dbc.Navbar(
            dbc.Container(
                [
                    dbc.NavbarBrand("MaStR-App", href="/", className="me-5"),
                    dbc.Nav(
                        [
                            dbc.NavLink("Tabellen", href="/tabellen", id="nav-tabellen"),
                            dbc.NavLink("Downloads", href="/download", id="nav-download"),
                        ],
                        navbar=True,
                        className="me-auto",
                        style={"fontSize": "1.15rem"},
                    ),
                ],
                fluid=True,
            ),
            dark=False,
            color="light",
            className="mb-4",
        ),
        html.Div(id="page-content"),
        dcc.Store(id="welcome-shown", data=False, storage_type="local"),
        welcome_modal,
        html.Footer(
            dbc.Container(
                html.P(
                    [
                        f"MaStR-App v{_app_version() or '?'}",
                        " · ",
                        "Daten: Marktstammdatenregister der Bundesnetzagentur",
                        " · ",
                        html.A("Impressum", href="/impressum", className="text-decoration-none"),
                    ],
                    className="text-muted mb-0",
                ),
                fluid=True,
            ),
            className="border-top mt-5 py-3",
        ),
    ],
    fluid=True,
)

# URL PATH -> content mapping
PAGE_CONTENT = {
    "tab-1-static-table": div_static_table,
    "tab-3-downloads": download_div,
    "tab-10-impressum": impressum_div,
}

# URL PATH <-> TAB VALUE mapping
TAB_PATHS = {
    "/": "tab-1-static-table",
    "/static": "tab-1-static-table",
    "/tabellen": "tab-1-static-table",
    "/downloads": "tab-3-downloads",
    "/download": "tab-3-downloads",
    "/impressum": "tab-10-impressum",
}


@callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def render_page(pathname):
    tab = TAB_PATHS.get(pathname, "tab-1-static-table")
    return PAGE_CONTENT[tab]


@callback(
    Output("nav-tabellen", "active"),
    Output("nav-download", "active"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def set_active_nav(pathname):
    tab = TAB_PATHS.get(pathname, "tab-1-static-table")
    return (
        tab == "tab-1-static-table",
        tab == "tab-3-downloads",
    )

@callback(
    Output("label-dump-timestamp", "children"),
    Output("label-import-timestamp", "children"),
    Input("state-table-dropdown", "value"),
)
def dump_label_refresh(value):
    try:
        import_time = datetime.fromisoformat(mastr_static.query_get(IMPORT_TIMESTAMP_URL).strip())
        import_time = import_time.strftime("%d.%m.%Y %H:%M Uhr")
        dump_date = datetime.fromisoformat(mastr_static.query_get(DUMP_DATE_URL).strip())
        dump_date = dump_date.strftime("%d.%m.%Y")
    except Exception:
        import_time = "unbekannt"
        dump_date = "unbekannt"
    return dump_date, import_time


if __name__ == "__main__":
    app.run(debug=True)