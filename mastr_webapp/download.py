import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

from .constants import (
    EnergySources,
    ENTITY_MAP,
    DownloadFormats,
    DEFAULT_ENTITY_VALUE,
    WIND_ENTITES,
    MASTR_STATIC_EXPORTS_URL,
    MASTR_STATIC_EXPORTS_PUBLIC_URL,
)
from .util import get_download_url, get_download_public_url
from .util_web import cached_file_size_mib

DB_DUMP_FILE = "mastr-latest.sql"

download_div = dbc.Container(
    id="div-download",
    fluid=True,
    children=[
        html.H3(
            "Downloads",
            className="border-bottom pb-3 mb-3",
        ),
        html.P(
            [
                "Derzeit stehen Downloads für die Energieträger Wind, Solar, Biomasse, Wasser, "
                "Geothermie/Grubengas/Druckentspannung, Stromspeicher, Kernkraft, Verbrennung, "
                "Gaserzeuger, Gasspeicher, Gasverbraucher und Stromverbraucher in verschiedenen Formaten bereit. "
                "Außerdem steht ein vollständiger Datenbankauszug zur Verfügung, der ",
                html.Strong("alle"),
                " Tabellen aus dem Marktstammdatenregister enthält.",
            ],
            className="text-muted fs-5 mb-3",
        ),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    [es.value for es in EnergySources],
                    value=EnergySources.WIND.value,
                    id="dropdown-download-source",
                    searchable=False,
                    clearable=False,
                    style={"fontSize": "1.15rem"},
                ),
                width="auto",
                style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    [{"label": v, "value": k} for k, v in WIND_ENTITES.items()],
                    value=DEFAULT_ENTITY_VALUE,
                    id="dropdown-download-entity",
                    searchable=False,
                    clearable=False,
                    style={"fontSize": "1.15rem"},
                ),
                width="auto",
                style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                dcc.Dropdown(
                    [{"label": fm.name, "value": fm.value} for fm in DownloadFormats],
                    value=DownloadFormats.CSV.value,
                    id="dropdown-download-format",
                    searchable=False,
                    clearable=False,
                    style={"fontSize": "1.15rem"},
                ),
                width="auto",
                style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.A(
                    dbc.Button(
                        "Download",
                        id="button-dynamic-download",
                        color="light",
                        className="w-100",
                    ),
                    id="link-dynamic-download",
                    className="w-100",
                ),
                width="auto",
                style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.A(
                    dbc.Button(
                        "Datenbank-Dump",
                        id="button-db-dump",
                        color="light",
                        className="w-100",
                        style={"fontSize": "0.9rem"},
                    ),
                    id="link-db-dump",
                    href=MASTR_STATIC_EXPORTS_PUBLIC_URL + DB_DUMP_FILE,
                    className="w-100",
                ),
                width="auto",
                style={"width": "380px", "paddingBottom": "10px", "paddingTop": "20px"},
            )
        ),
        dbc.Row(
            dbc.Col(
                html.P(
                    [
                        "Der Datenbank-Dump ist ein zstd-komprimiertes ",
                        html.Code("pg_dump"),
                        "-Archiv aller Tabellen aus dem Marktstammdatenregister. Zum Einspielen wird mindestens "
                        "PostgreSQL 16 benötigt: ",
                        html.Code("pg_restore -U mastr -d mastr --clean mastr-latest.sql"),
                        " — ein direktes Einlesen mit psql ist wegen des Binärformats nicht möglich.",
                    ],
                    className="text-muted small",
                ),
                width="auto",
                style={"maxWidth": "760px", "paddingBottom": "10px"},
            )
        ),
    ],
)


@callback(
    Output("button-db-dump", "children"),
    Input("url", "pathname"),
)
def set_db_dump_label(pathname):
    """Label of the static database dump button: file size if the dump
    exists, 'nicht verfügbar' until the first pipeline run created it."""
    file_size = cached_file_size_mib(MASTR_STATIC_EXPORTS_URL + DB_DUMP_FILE)
    if file_size is None:
        return "Datenbank-Dump (nicht verfügbar)"
    return f"Datenbank-Dump (SQL, zstd, {file_size:.2f} MiB)"


@callback(
    Output("dropdown-download-entity", "options"),
    Output("dropdown-download-entity", "value"),
    Input("dropdown-download-source", "value"),
)
def set_download_entity(value):
    entity = ENTITY_MAP[EnergySources(value)]
    options = [{"label": v, "value": k} for k, v in entity.items()]
    return options, DEFAULT_ENTITY_VALUE


@callback(
    Output("button-dynamic-download", "children"),
    Output("link-dynamic-download", "href"),
    Input("dropdown-download-source", "value"),
    Input("dropdown-download-entity", "value"),
    Input("dropdown-download-format", "value"),
)
def set_download_dynamic_button(source, entity_key, format):
    entities = ENTITY_MAP[EnergySources(source)]
    if None not in (source, entity_key, format) and entity_key in entities:
        url = get_download_url(EnergySources(source), entities[entity_key], DownloadFormats(format))
        public_url = get_download_public_url(EnergySources(source), entities[entity_key], DownloadFormats(format))
        file_size = cached_file_size_mib(url)
        if file_size is None:
            return f"{DownloadFormats(format).name} nicht verfügbar", public_url
        return f"{DownloadFormats(format).name} ({file_size:.2f} MiB)", public_url
    return "Keine Übereinstimmung", ""
