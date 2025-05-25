import mastr_webapp.styles as mastr_styles
import mastr_webapp.tables as mastr_tables
from dash import Dash, html, dcc, callback, Input, Output, State
from dash.dcc import Location
from dash.dcc import Dropdown, Tab, Tabs, Store
from mastr_webapp.util_web import RESTClient
from mastr_webapp.strings import *
from mastr_webapp.impressum import impressum_div
from mastr_webapp.download import download_div

from datetime import datetime

# app = Dash(__name__, suppress_callback_exceptions=True)
app = Dash(__name__)
server = app.server
mastr_static = RESTClient()


class MastrMainTab(Tab):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.style = mastr_styles.main_tab_style
        self.selected_style = mastr_styles.main_tab_selected_style


dropdown_state = Dropdown(
    [static_table_states[s] for s in TABLE_SOURCE_ENTITY_URL],
    static_table_states[TABLE_SOURCE_ENTITY_URL.WIND_MV],
    id="state-table-dropdown",
)

div_static_table = html.Div(
    children=[
        html.Div(
            children=[
                html.H3(children="Übersicht Windenergieanlagen - Marktstammdatenregister der Bundesnetzagentur."),
                html.Div(
                    [
                        html.Label(
                            "Zeitstempel MaStR-Daten:",
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
                            style={"width": "16em", "display": "inline-block"},
                        ),
                        html.Label("NA", id="label-import-timestamp"),
                    ],
                    title="Zeitpunkt an dem die MaStR-Daten importiert wurden.",
                ),
            ]
        ),
        html.Div(
            children=dropdown_state,
            style={
                "width": "20%",
                "minWidth": "120px",
                "paddingBottom": "10px",
                "paddingTop": "10px",
            },
        ),
        html.Div(
            id="div-static-table",
            children=[
                dcc.Loading(
                    id="loading-table-1",
                    children=[mastr_tables.get_static_table()],
                    type="circle",
                ),
            ],
        ),
        html.Div(id="div-static-buttons", children=mastr_tables.get_static_table_download()),
        Store(id="stored-static-table"),
        Store(id="stored-selected-rows"),
    ]
)

# Update your layout: Add dcc.Location
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),   # add this!
        Tabs(
            id="mastr-main-tabs",
            value="tab-1-static-table",  # default value
            children=[
                MastrMainTab(
                    label="Tabellen",
                    value="tab-1-static-table",
                    children=div_static_table,
                ),
                MastrMainTab(
                    label="Dynamische Abfrage",
                    value="tab-2-dynamic-query",
                    children="NYI - coming soon",
                ),
                MastrMainTab(label="Downloads", value="tab-3-downloads", children=download_div),
                MastrMainTab(label="Impressum", value="tab-10-impressum", children=impressum_div),
            ],
            style=mastr_styles.main_tabs_style,
        ),
        html.Div(id="tabs-content-example-graph"),
    ]
)

# URL PATH <-> TAB VALUE mapping
TAB_PATHS = {
    "/": "tab-1-static-table",
    "/static": "tab-1-static-table",
    "/query": "tab-2-dynamic-query",
    "/downloads": "tab-3-downloads",
    "/impressum": "tab-10-impressum",
}

# Callback to set the tab based on the incoming URL PATH
@callback(
    Output("mastr-main-tabs", "value"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def select_tab_from_url(pathname):
    return TAB_PATHS.get(pathname, "tab-1-static-table")

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