import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, clientside_callback

welcome_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Willkommen")),
        dbc.ModalBody(
            dcc.Markdown(
                """
Diese Webanwendung ermöglicht die Suche in und den Download von Daten des
**Marktstammdatenregisters** der Bundesnetzagentur in alternativen Formaten.

- **Tabellen** — Durchsuchen Sie Windenergieanlagen nach Bundesland.
- **Downloads** — Laden Sie Datenauszüge als CSV oder Parquet herunter.
- **Impressum** — Informationen zu Datenquelle, Lizenz und Haftung.

Die Daten stammen aus dem öffentlich zugänglichen
[Gesamtdatenauszug des Marktstammdatenregisters](https://www.marktstammdatenregister.de/MaStR/Datendownload).
Es handelt sich um ein privates Projekt ohne kommerzielle Ziele.
"""
            )
        ),
        dbc.ModalFooter(
            dbc.Button(
                "Schließen",
                id="welcome-close",
                className="ms-auto",
                color="light",
                n_clicks=0,
            )
        ),
    ],
    id="welcome-modal",
    is_open=False,
    centered=True,
    backdrop=True,
    keyboard=True,
)


clientside_callback(
    """
    function(pathname, closeClicks, shown) {
        const ctx = dash_clientside.callback_context;
        const triggered = ctx && ctx.triggered.length ? ctx.triggered[0].prop_id : "";
        if (triggered.includes("welcome-close")) {
            return [false, true];
        }
        if (!shown) {
            return [true, true];
        }
        return [false, true];
    }
    """,
    Output("welcome-modal", "is_open"),
    Output("welcome-shown", "data"),
    Input("url", "pathname"),
    Input("welcome-close", "n_clicks"),
    State("welcome-shown", "data"),
    prevent_initial_call=False,
)
