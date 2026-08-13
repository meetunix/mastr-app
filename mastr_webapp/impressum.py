from dash import html, dcc, callback, Input, Output
from pathlib import Path

impressum_div = html.Div(id="div-impressum", children=[dcc.Markdown(id="md-impressum")])


@callback(Output("md-impressum", "children"), Input("url", "pathname"))
def refresh_impressum(pathname):
    try:
        impressum = Path("assets/impressum.md").read_text(encoding="utf-8")
    except Exception as e:
        print(e)
        impressum = "NA"
    return impressum
