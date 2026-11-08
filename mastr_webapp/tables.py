import json
import logging
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html, callback, Input, Output, dcc, no_update, State
from dash.dash_table import DataTable
from dash.dcc import Download
from dash.exceptions import PreventUpdate

from .strings import static_table_sources, static_table_states
from .table_columns import to_display_frame
from .util import *
from .util_web import MastrWebException, cached_file_size_mib, cached_read_csv, get_dataframe_version

logger = logging.getLogger(__name__)


def get_static_table(**props) -> DataTable:
    """Create the static table. Props override the defaults, so the callback
    can build a fully populated, fresh instance on every table switch (a fresh
    instance resets filter, sort and selection)."""
    defaults = dict(
        id="static-table",
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode="multi",
        column_selectable="single",
        row_selectable="multi",
        row_deletable=False,
        selected_columns=[],
        selected_rows=[],
        page_action="native",
        page_current=0,
        style_as_list_view=True,
        page_size=20,
        # style_table={'overflowX': 'auto', 'minWidth': '100%', 'maxWidth' : "100%"},
        style_table={"minWidth": "100%", "maxWidth": "100%"},
        fixed_columns={"headers": True},
        # fixed_rows={'headers': True},
        style_header={
            "backgroundColor": "rgb(210, 210, 210)",
            "color": "black",
            "fontWeight": "bold",
            "textAlign": "center",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(220, 220, 220)",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#00cc99",
                "border": "0 px solid white",
            },
        ],
        style_cell={
            "padding-right": "10px",
            "padding-left": "10px",
            "minWidth": "240px",
            "width": "240px",
            "maxWidth": "240px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        tooltip_delay=500,
        tooltip_duration=None,
        data=[],
        columns=[],
        tooltip_data=[],
        style_cell_conditional=[],
    )
    defaults.update(props)
    return DataTable(**defaults)


def text_width(text: str) -> int:
    """Estimated pixel width needed to show the text in a table cell.

    Calibrated against the real rendering (dash-table's default font stack
    resolves to DejaVu Sans on Linux, at the Bootstrap body size of 16px,
    bold): the widest headers need about 10.6px per character, plus 20px
    cell padding and a small margin.
    """
    return round(len(text) * 10.6) + 24


def column_width(name: str) -> int:
    """Estimated pixel width needed to show the full column header. Columns
    never shrink below the default width of 240px."""
    return max(240, text_width(name))


def static_table_url(source, state) -> str:
    """CSV URL of the table selected in the dropdowns.

    The values come from the client, so only the offered sources and states
    are accepted; anything else could make the server load an arbitrary
    (e.g. multi-GB) export.
    """
    if source not in static_table_sources or state not in static_table_states:
        raise PreventUpdate
    return get_download_url(EnergySources(source), state, DownloadFormats.CSV)


# update static table via dropdowns: a fresh table instance is created on every
# switch, so the filter row, sorting and selection start empty for the new table
@callback(
    Output("static-table-container", "children"),
    Output("stored-static-table", "data"),
    Input("dropdown-table-source", "value"),
    Input("state-table-dropdown", "value"),
)
def update_output(source, state):
    table_url = static_table_url(source, state)
    try:
        df, version = cached_read_csv(table_url)
    except MastrWebException as e:
        logger.error("Could not load table %s: %s", table_url, e)
        alert = dbc.Alert("Die Tabelle konnte nicht geladen werden. Bitte später erneut versuchen.", color="danger")
        # an empty table, so the download buttons have nothing to export
        return [alert, get_static_table()], None
    # only the configured columns are displayed; the full dataframe stays in
    # the cache and is used by the download buttons (all columns)
    display_df = to_display_frame(df)
    records = display_df.to_dict("records")
    columns = [{"name": i, "id": i, "deletable": False, "selectable": False} for i in display_df.columns]
    # widen columns whose header does not fit the default width of 240px
    widths = {name: column_width(name) for name in display_df.columns}
    # tooltips only for text that is probably cut off (with an ellipsis);
    # tooltips for all cells would more than double the response size
    tooltip_data = [
        {
            column: {"value": value, "type": "text"}
            for column, value in row.items()
            if isinstance(value, str) and text_width(value) > widths[column]
        }
        for row in records
    ]
    style_cell_conditional = [
        {
            "if": {"column_id": name},
            "minWidth": f"{width}px",
            "width": f"{width}px",
            "maxWidth": f"{width}px",
        }
        for name, width in widths.items()
    ]

    table = get_static_table(
        data=records,
        columns=columns,
        tooltip_data=tooltip_data,
        style_cell_conditional=style_cell_conditional,
    )
    # the version identifies the data the client sees, for the downloads
    return [table], {"url": table_url, "version": version}


def get_static_table_download() -> dbc.Row:
    return dbc.Row(
        id="div-static-download-buttons",
        children=[
            dbc.Col(
                html.A(
                    dbc.Button(
                        "Datensatz als CSV (.csv)",
                        id="button-static-download-dataset",
                        color="light",
                    ),
                    id="link-static-download-dataset",
                ),
                width="auto",
                className="me-2",
            ),
            dbc.Col(
                html.A(
                    dbc.Button(
                        "Datensatz als Excel (.xlsx)",
                        id="button-static-download-excel",
                        color="light",
                    ),
                    id="link-static-download-excel",
                ),
                width="auto",
                className="me-2",
            ),
            dbc.Col(
                html.A(
                    dbc.Button(
                        "Datensatz als Parquet (.parq)",
                        id="button-static-download-parquet",
                        color="light",
                    ),
                    id="link-static-download-parquet",
                ),
                width="auto",
                className="me-2",
            ),
            dbc.Col(
                dcc.Loading(
                    id="loading-button-static-selected",
                    children=[
                        dbc.Button(
                            "Auswahl als CSV (0)",
                            id="button-static-selected",
                            color="light",
                        ),
                        Download(id="download-static-selected"),
                    ],
                    type="circle",
                    delay_show=300,
                    className="loading-button",
                    overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                ),
                width="auto",
                className="me-2",
            ),
            dbc.Col(
                dcc.Loading(
                    id="loading-button-static-filtered",
                    children=[
                        dbc.Button(
                            "Filterergebnis als CSV",
                            id="button-static-filtered",
                            color="light",
                        ),
                        Download(id="download-static-filtered"),
                    ],
                    type="circle",
                    delay_show=300,
                    className="loading-button",
                    overlay_style={"visibility": "visible", "filter": "blur(2px)"},
                ),
                width="auto",
                className="me-2",
            ),
            dbc.Col(
                dbc.Button(
                    "Auswahl aufheben",
                    id="button-static-erase",
                    color="light",
                ),
                width="auto",
                className="me-2",
            ),
        ],
    )


@callback(
    Output("link-static-download-dataset", "href"),
    Output("button-static-download-dataset", "children"),
    Output("link-static-download-excel", "href"),
    Output("button-static-download-excel", "children"),
    Output("link-static-download-parquet", "href"),
    Output("button-static-download-parquet", "children"),
    Input("dropdown-table-source", "value"),
    Input("state-table-dropdown", "value"),
)
def update_download_buttons(source, state):
    table_url = static_table_url(source, state)
    excel_url = replace_filetype_on_url(table_url, ".xlsx")
    parq_url = replace_filetype_on_url(table_url, ".parq")

    csv_pub, excel_pub, parq_pub = to_public_url(table_url), to_public_url(excel_url), to_public_url(parq_url)

    csv_size = cached_file_size_mib(table_url)
    excel_size = cached_file_size_mib(excel_url)
    parq_size = cached_file_size_mib(parq_url)

    csv_label = f"Datensatz als CSV (.csv, {csv_size:.2f} MiB)" if csv_size is not None else "Datensatz als CSV (.csv, nicht verfügbar)"
    excel_label = f"Datensatz als Excel (.xlsx, {excel_size:.2f} MiB)" if excel_size is not None else "Datensatz als Excel (.xlsx, nicht verfügbar)"
    parq_label = f"Datensatz als Parquet (.parq, {parq_size:.2f} MiB)" if parq_size is not None else "Datensatz als Parquet (.parq, nicht verfügbar)"

    return (
        csv_pub,
        csv_label,
        excel_pub,
        excel_label,
        parq_pub,
        parq_label,
    )


# selected_rows are indices into the table data, i.e. into the dataframe;
# derived_virtual_selected_rows would be positions in the filtered and sorted
# view. The callback also fires for every new table instance (empty selection).
@callback(
    Output("button-static-selected", "children"),
    Output("stored-selected-rows", "data"),
    Input("static-table", "selected_rows"),
    prevent_initial_call=True,
)
def update_button_row_counter(rows):
    if rows is None:
        return no_update
    else:
        return f"Auswahl als CSV ({len(rows)})", json.dumps(rows)


def send_rows(stored_table, rows: list[int]):
    """CSV download of the given rows (all columns) of the table the client
    has loaded, and the message to show below the buttons (None on success)."""
    try:
        df = get_dataframe_version(stored_table["url"], stored_table["version"])
    except MastrWebException as e:
        logger.error("Could not load table %s for export: %s", stored_table["url"], e)
        return no_update, download_alert(
            "Der Export ist derzeit nicht möglich. Bitte später erneut versuchen.", "danger"
        )
    # None: the upstream data has changed since the client loaded the table
    if df is None or max(rows) >= len(df):
        return no_update, download_alert(
            "Die Daten dieser Tabelle wurden inzwischen aktualisiert. "
            "Bitte die Seite neu laden und die Auswahl erneut treffen.",
            "warning",
        )
    filename = f"mastr-tool-export-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    return dcc.send_data_frame(df.iloc[rows].to_csv, filename, index=False), None


def download_alert(message: str, color: str) -> dbc.Alert:
    return dbc.Alert(message, color=color, dismissable=True, duration=15000)


# a download message refers to the previous table, so it is removed on switch
@callback(
    Output("static-download-message", "children", allow_duplicate=True),
    Input("dropdown-table-source", "value"),
    Input("state-table-dropdown", "value"),
    prevent_initial_call=True,
)
def clear_download_message(source, state):
    return None


# download selected rows
@callback(
    Output("download-static-selected", "data"),
    Output("static-download-message", "children", allow_duplicate=True),
    Input("button-static-selected", "n_clicks"),
    State("stored-static-table", "data"),
    State("stored-selected-rows", "data"),
    prevent_initial_call=True,
)
def download_selected_rows(n_clicks, stored_table, stored_selected_rows):
    if stored_table is None or stored_selected_rows is None:
        return no_update
    rows = json.loads(stored_selected_rows)

    if len(rows) <= 0:
        return no_update

    rows = sorted(rows)

    return send_rows(stored_table, rows)


# download filtered rows
@callback(
    Output("download-static-filtered", "data"),
    Output("button-static-filtered", "n_clicks"),
    Output("static-download-message", "children", allow_duplicate=True),
    Input("button-static-filtered", "n_clicks"),
    State("static-table", "derived_virtual_indices"),
    State("stored-static-table", "data"),
    prevent_initial_call=True,
)
def download_filtered_rows(n_clicks, filtered_row_ids, stored_table):
    if n_clicks is None:
        return no_update

    if stored_table is None or filtered_row_ids is None:
        return no_update

    if len(filtered_row_ids) <= 0:
        return no_update

    filtered_rows = sorted(filtered_row_ids)

    download, message = send_rows(stored_table, filtered_rows)
    return download, None, message


# erase selected rows
@callback(
    Output("static-table", "selected_rows"),
    Input("button-static-erase", "n_clicks"),
    prevent_initial_call=True,
)
def erase_selected_rows(n_clicks):
    if n_clicks is None:
        return no_update
    else:
        return []
