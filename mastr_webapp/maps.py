import logging
import math

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, Input, Output, Patch, State, callback, dcc, html, no_update
from dash.exceptions import PreventUpdate

from . import database
from .constants import EnergySources
from .map_fields import as_kw, detail_values, eeg_values, name_column, title_suffix_column, unit_title
from .strings import MAP_GERMANY, map_sources, map_sources_without_germany, map_states
from .units import fetch_map_units, fetch_unit, has_eeg

logger = logging.getLogger(__name__)

# colors of the Flatly theme, in legend order
STATUS_COLORS = {
    "In Betrieb": "#18bc9c",
    "In Planung": "#3498db",
    "Vorübergehend stillgelegt": "#f39c12",
    "Endgültig stillgelegt": "#95a5a6",
}
OTHER_STATUS_COLOR = "#2c3e50"
SELECTED_COLOR = "#e74c3c"

GERMANY_CENTER = {"lat": 51.16, "lon": 10.45}
# approximate size of the map in pixels, to choose the initial zoom level
MAP_WIDTH_PX = 700
MAP_HEIGHT_PX = 600


def german_int(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def map_view(lat: pd.Series, lon: pd.Series) -> tuple[dict, float]:
    """Center and zoom level that show (nearly) all points.

    The outer 1% of the coordinates on each side is ignored, so a single
    misplaced unit (e.g. swapped coordinates) doesn't zoom out to Europe.
    """
    if lat.empty:
        return GERMANY_CENTER, 5
    lat_min, lat_max = lat.quantile([0.01, 0.99])
    lon_min, lon_max = lon.quantile([0.01, 0.99])
    center = {"lat": float(lat_min + lat_max) / 2, "lon": float(lon_min + lon_max) / 2}
    # web mercator: the world is 512px wide at zoom 0, and a degree of
    # latitude is 1/cos(latitude) times as high as a degree of longitude
    lon_span = max(lon_max - lon_min, 0.01)
    lat_span = max(lat_max - lat_min, 0.01) / math.cos(math.radians(center["lat"]))
    zoom = min(math.log2(MAP_WIDTH_PX * 360 / (512 * lon_span)), math.log2(MAP_HEIGHT_PX * 360 / (512 * lat_span)))
    return center, max(3.0, min(zoom - 0.3, 12.0))


def map_points(df: pd.DataFrame, source: EnergySources) -> pd.DataFrame:
    """The units of the map (see fetch_map_units): MaStR number, coordinates,
    status, title and net power as text ("" if unknown)."""

    def text(column: str) -> pd.Series:
        return df[column] if column in df.columns else pd.Series("", index=df.index, dtype=str)

    unit_ids = text("einheitmastrnummer")
    names, suffixes = text(name_column(source).lower()), text(title_suffix_column(source).lower())
    titles = [unit_title(*values) for values in zip(names, suffixes, unit_ids)]
    power = text("nettonennleistung")
    if "nettonennleistung" in df.columns:
        power = power.map(lambda value: "" if pd.isna(value) else as_kw(value))
    return pd.DataFrame(
        {
            "id": unit_ids,
            # float32 is precise to about 0.3 m and halves the coordinates in the figure
            "lat": df["breitengrad"].astype("float32"),
            "lon": df["laengengrad"].astype("float32"),
            "status": text("einheitbetriebsstatus"),
            "title": pd.Series(titles, index=df.index, dtype=str),
            "power": power,
        }
    )


def map_statuses(points: pd.DataFrame) -> list[str]:
    """The operating statuses of the points, in legend order: one trace each."""
    statuses = [s for s in STATUS_COLORS if s in set(points["status"])]
    return statuses + sorted(set(points["status"]) - set(STATUS_COLORS))


def map_figure(points: pd.DataFrame | None = None, revision: str = "") -> go.Figure:
    """OpenStreetMap with one trace per operating status (see map_statuses),
    shown and hidden with the legend of map_legend. The first trace marks
    the selected unit below its point; the click callback moves it."""
    figure = go.Figure(
        go.Scattermap(
            lat=[],
            lon=[],
            mode="markers",
            marker={"size": 22, "color": SELECTED_COLOR, "opacity": 0.7},
            hoverinfo="skip",
            showlegend=False,
        )
    )
    if points is None:
        points = pd.DataFrame(columns=["id", "lat", "lon", "status", "title", "power"])
    for status in map_statuses(points):
        group = points[points["status"] == status]
        label = status or "Ohne Status"
        has_power = bool(group["power"].ne("").any())
        figure.add_trace(
            go.Scattermap(
                lat=group["lat"],
                lon=group["lon"],
                customdata=group["id"],
                # The markup and the status are in the template, once per
                # trace: Dash escapes "<", ">" and "/" in the JSON (6 bytes
                # each), markup per point would double the size of the figure.
                hovertext=group["title"],
                text=group["power"] if has_power else None,
                hovertemplate=f"<b>%{{hovertext}}</b><br>{label}{'<br>%{text}' if has_power else ''}<extra></extra>",
                mode="markers",
                marker={"size": 9, "color": STATUS_COLORS.get(status, OTHER_STATUS_COLOR), "opacity": 0.85},
                name=label,
            )
        )
    center, zoom = map_view(points["lat"], points["lon"])
    figure.update_layout(
        map={"style": "open-street-map", "center": center, "zoom": zoom},
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        # the legend is HTML (map_legend): plotly can't align the numbers
        showlegend=False,
        # the view (zoom, pan) is kept while the selection marker moves and
        # reset for a new selection
        uirevision=revision,
    )
    return figure


def map_legend(points: pd.DataFrame, total: int) -> html.Table | None:
    """Legend over the map: a row per operating status (a click hides or
    shows its trace) and the counts of the selection, all numbers
    right-aligned in one column."""
    if points.empty:
        return None

    def row(marker, label: str, number: int, **props) -> html.Tr:
        return html.Tr(
            [html.Td(marker), html.Td(label), html.Td(german_int(number), className="map-legend-number")], **props
        )

    rows = [
        row(
            html.Span(
                className="map-legend-dot", style={"backgroundColor": STATUS_COLORS.get(status, OTHER_STATUS_COLOR)}
            ),
            status or "Ohne Status",
            int((points["status"] == status).sum()),
            # the trace of the status (after the selection marker)
            id={"type": "map-legend-status", "index": index},
            className="map-legend-status",
            title="Klicken zum Aus- oder Einblenden",
            n_clicks=0,
        )
        for index, status in enumerate(map_statuses(points), start=1)
    ]
    rows += [
        html.Tr(html.Td(colSpan=3), className="map-legend-separator"),
        row(None, "In der Datenbank", total),
        row(None, "Angezeigt", len(points)),
        row(None, "Ohne Koordinaten", total - len(points)),
    ]
    return html.Table(html.Tbody(rows), className="map-legend")


def details_placeholder() -> dbc.Card:
    return dbc.Card(
        dbc.CardBody(
            html.P(
                "Eine Einheit auf der Karte anklicken, um ihre wichtigsten Daten anzuzeigen.",
                className="text-muted mb-0",
            )
        )
    )


def eeg_section(
    row: dict[str, str], source: EnergySources, eeg: dict[str, str] | None
) -> tuple[str, list[tuple[str, str]] | str] | None:
    """The EEG section of a unit (both rows from fetch_unit): the configured
    fields of its EEG plant, or a message why there are none. None if there
    is no EEG data for the energy source."""
    if not has_eeg(source):
        return None
    title = "EEG-Anlage"
    eeg_number = row.get("eegmastrnummer", "").strip()
    if not eeg_number:
        return title, "Der Einheit ist keine EEG-Anlage zugeordnet."
    if eeg is None:
        return title, f"Zur EEG-Anlage {eeg_number} sind keine Daten vorhanden."
    return title, eeg_values(eeg, source)


def unit_details(
    row: dict[str, str], source: EnergySources, eeg: tuple[str, list[tuple[str, str]] | str] | None = None
) -> dbc.Card:
    """Card with the configured 24 fields of a unit (row with lowercase
    column names), grouped into sections, and the EEG section (see
    eeg_section) at the end. A section is a list of (label, value) pairs or
    a message."""
    sections = detail_values(row, source)
    (_, unit_id), (_, status) = sections[0][1][1:3]
    title = unit_title(
        row.get(name_column(source).lower(), ""), row.get(title_suffix_column(source).lower(), ""), unit_id
    )
    body = []
    for section, fields in [*sections, *([eeg] if eeg else [])]:
        body.append(html.H6(section, className="text-uppercase text-muted small mt-3 mb-1"))
        if isinstance(fields, str):
            body.append(html.P(fields, className="text-muted small mb-0"))
            continue
        body.append(
            dbc.Table(
                html.Tbody([html.Tr([html.Th(label), html.Td(value)]) for label, value in fields]),
                size="sm",
                className="unit-details-table mb-0",
            )
        )
    lat, lon = row.get("breitengrad", ""), row.get("laengengrad", "")
    links = [
        html.A(
            "Auf OpenStreetMap ansehen",
            href=f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}",
            target="_blank",
            rel="noopener noreferrer",
            className="me-3",
        ),
        html.A(
            "In OpenInfraMap ansehen",
            href=f"https://openinframap.org/#16/{lat}/{lon}",
            target="_blank",
            rel="noopener noreferrer",
        ),
    ]
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H5(title, className="mb-1"),
                    dbc.Badge(status, color=STATUS_COLORS.get(status, OTHER_STATUS_COLOR), className="me-2"),
                    html.Span(unit_id, className="text-muted small"),
                ]
            ),
            dbc.CardBody(body, className="pt-0"),
            dbc.CardFooter(links, className="small"),
        ]
    )


def state_options(source: str) -> list[dict]:
    """The states and all of Germany, which is disabled for the energy
    sources with too many units."""
    too_many = source in map_sources_without_germany
    return [
        {"label": f"{state} – zu viele Einheiten", "value": state, "disabled": True}
        if state == MAP_GERMANY and too_many
        else {"label": state, "value": state}
        for state in map_states
    ]


dropdown_map_source = dcc.Dropdown(
    map_sources,
    EnergySources.WIND.value,
    id="dropdown-map-source",
    searchable=False,
    clearable=False,
    style={"fontSize": "1.15rem"},
)

dropdown_map_state = dcc.Dropdown(
    state_options(EnergySources.WIND.value),
    map_states[0],
    id="dropdown-map-state",
    searchable=False,
    clearable=False,
    style={"fontSize": "1.15rem"},
)

page_header = dbc.Row(
    dbc.Col(
        [
            html.H3("Karten", className="border-bottom pb-3 mb-3"),
            html.P(
                "Standorte der Anlagen aus dem Marktstammdatenregister der Bundesnetzagentur.",
                className="text-muted fs-5 mb-3",
            ),
        ]
    )
)

maps_layout = dbc.Container(
    [
        page_header,
        dbc.Row(
            [
                dbc.Col(
                    html.Label("Energieträger:", className="col-form-label fs-5"),
                    width="auto",
                    style={"paddingRight": "0"},
                ),
                dbc.Col(
                    dropdown_map_source,
                    width="auto",
                    style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px", "paddingLeft": "0.5rem"},
                ),
                dbc.Col(
                    html.Label("Bundesland:", className="col-form-label fs-5"),
                    width="auto",
                    style={"paddingRight": "0"},
                ),
                dbc.Col(
                    dropdown_map_state,
                    width="auto",
                    style={"width": "340px", "paddingBottom": "10px", "paddingTop": "10px", "paddingLeft": "0.5rem"},
                ),
            ],
            align="center",
        ),
        # database unavailable or being updated
        html.Div(id="map-message", className="mt-2"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Loading(
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="map-graph",
                                        figure=map_figure(),
                                        config={
                                            "scrollZoom": True,
                                            "displaylogo": False,
                                            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
                                        },
                                        style={"height": "75vh", "minHeight": "450px"},
                                    ),
                                    html.Div(id="map-legend"),
                                ],
                                className="map-container",
                            ),
                            type="circle",
                            # selecting a unit patches the figure quickly; no spinner for that
                            delay_show=300,
                        ),
                        html.Div(id="map-caption", className="text-muted small mt-2"),
                    ],
                    xs=12,
                    lg=7,
                    className="mb-3",
                ),
                dbc.Col(
                    html.Div(id="map-unit-details", children=details_placeholder(), className="map-unit-details"),
                    xs=12,
                    lg=5,
                ),
            ],
            className="mt-2",
        ),
    ],
    fluid=True,
)

# all data of the maps page comes from the database
no_database_layout = dbc.Container(
    [
        page_header,
        dbc.Alert(
            "Die Karten sind nicht verfügbar: Für diese Installation ist keine Verbindung zur Datenbank eingerichtet.",
            color="warning",
        ),
    ],
    fluid=True,
)

maps_div = maps_layout if database.is_configured() else no_database_layout


def database_alert(error: database.DatabaseUnavailable) -> dbc.Alert:
    if isinstance(error, database.DatabaseUpdating):
        return dbc.Alert(
            "Die Datenbank wird gerade aktualisiert. Bitte in einigen Minuten erneut versuchen.", color="warning"
        )
    return dbc.Alert("Die Datenbank ist derzeit nicht erreichbar. Bitte später erneut versuchen.", color="danger")


def check_selection(source, state) -> None:
    """The dropdown values come from the client; only the offered ones are accepted."""
    if source not in map_sources or state not in map_states:
        raise PreventUpdate
    if state == MAP_GERMANY and source in map_sources_without_germany:
        raise PreventUpdate


@callback(
    Output("dropdown-map-state", "options"),
    Output("dropdown-map-state", "value"),
    Input("dropdown-map-source", "value"),
    State("dropdown-map-state", "value"),
)
def update_state_options(source, state):
    """All of Germany is not offered for some energy sources; if it is
    selected, the first state is selected instead."""
    if state == MAP_GERMANY and source in map_sources_without_germany:
        state = map_states[0]
    return state_options(source), state


COORDINATES_HINT = "Das MaStR veröffentlicht Koordinaten erst ab 30 kW Nettonennleistung."


def map_caption(shown: int, total: int) -> str | None:
    """Note below the map; the counts are in the legend (not shown without units on the map)."""
    if total == 0:
        return "Für diese Auswahl sind keine Einheiten registriert."
    if shown == 0:
        return f"Keine der {german_int(total)} Einheiten hat Koordinaten. {COORDINATES_HINT}"
    if shown < total:
        return f"Einheiten ohne Koordinaten fehlen auf der Karte. {COORDINATES_HINT}"
    return None


# a new selection replaces the whole figure (the view starts fresh) and the
# details of the previous selection's unit
@callback(
    Output("map-graph", "figure"),
    Output("map-caption", "children"),
    Output("map-unit-details", "children"),
    Output("map-message", "children"),
    Output("map-legend", "children"),
    Input("dropdown-map-source", "value"),
    Input("dropdown-map-state", "value"),
)
def update_map(source, state):
    check_selection(source, state)
    try:
        df, total = fetch_map_units(EnergySources(source), None if state == MAP_GERMANY else state)
    except database.DatabaseUnavailable as e:
        logger.warning("Could not load the units of %s in %s: %s", source, state, e)
        return map_figure(), None, details_placeholder(), database_alert(e), None
    points = map_points(df, EnergySources(source))
    figure = map_figure(points, f"{source}|{state}")
    return figure, map_caption(len(points), total), details_placeholder(), None, map_legend(points, total)


# a click on a status in the legend hides or shows its units; the legend is
# rebuilt with every new selection, so the clicks start at 0 with every map
@callback(
    Output("map-graph", "figure", allow_duplicate=True),
    Output({"type": "map-legend-status", "index": ALL}, "className"),
    Input({"type": "map-legend-status", "index": ALL}, "n_clicks"),
    State({"type": "map-legend-status", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def toggle_statuses(clicks, ids):
    figure, classes = Patch(), []
    for n_clicks, legend_id in zip(clicks, ids):
        hidden = (n_clicks or 0) % 2 == 1
        figure["data"][legend_id["index"]]["visible"] = not hidden
        classes.append("map-legend-status map-legend-hidden" if hidden else "map-legend-status")
    return figure, classes


# the unit is looked up by its MaStR number, so the details are still found
# if the database has been updated since the map was loaded
@callback(
    Output("map-unit-details", "children", allow_duplicate=True),
    Output("map-graph", "figure", allow_duplicate=True),
    Input("map-graph", "clickData"),
    State("dropdown-map-source", "value"),
    State("dropdown-map-state", "value"),
    prevent_initial_call=True,
)
def show_unit_details(click_data, source, state):
    points = (click_data or {}).get("points") or []
    unit_id = points[0].get("customdata") if points else None
    if not isinstance(unit_id, str):
        raise PreventUpdate
    check_selection(source, state)
    source = EnergySources(source)
    try:
        unit = fetch_unit(source, unit_id)
    except database.DatabaseUnavailable as e:
        logger.warning("Could not load unit %s: %s", unit_id, e)
        return database_alert(e), no_update
    if unit is None:
        alert = dbc.Alert(
            "Die Einheit ist in den aktuellen Daten nicht mehr enthalten. Bitte die Seite neu laden.", color="warning"
        )
        return alert, no_update
    row, eeg = unit
    # moves the selection marker (the first trace) below the clicked point
    selection = Patch()
    selection["data"][0]["lat"] = [points[0].get("lat")]
    selection["data"][0]["lon"] = [points[0].get("lon")]
    return unit_details(row, source, eeg_section(row, source, eeg)), selection
