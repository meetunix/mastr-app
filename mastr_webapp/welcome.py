import dash_bootstrap_components as dbc
from dash import dcc, Input, Output, State, clientside_callback
from pathlib import Path

try:
    _welcome_text = Path("assets/welcome.md").read_text(encoding="utf-8")
except Exception as e:
    print(e)
    _welcome_text = "NA"

welcome_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle("Willkommen")),
        dbc.ModalBody(
            dcc.Markdown(_welcome_text)
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
