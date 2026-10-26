"""Configuration of the columns shown in the static data table.

TABLE_DISPLAY_COLUMNS defines which columns of the exported CSV files are
displayed in the web UI, in the given order. The names are the column names
of the mastr-tool exports (CSV header / Parquet column names).

Configuration rules:
- Column names are matched case-insensitively against the CSV headers (the
  headers are lowercased by PostgreSQL), and the actual CSV column names are
  displayed.
- Columns that do not exist in a CSV are skipped silently, so renaming or
  removing columns in mastr-tool does not break the table.
- Leave the list empty to display all columns of the CSV.

The download buttons below the table always provide all columns of the
underlying CSV, independent of this configuration.
"""

import pandas as pd

TABLE_DISPLAY_COLUMNS = [
    # identity & dates
    "NameStromerzeugungseinheit",
    "DatumLetzteAktualisierung",
    "Registrierungsdatum",
    "Inbetriebnahmedatum",
    "GeplantesInbetriebnahmedatum",
    "DatumEndgueltigeStilllegung",
    # status & verification
    "EinheitBetriebsstatus",
    "NetzbetreiberpruefungStatus",
    "NetzbetreiberpruefungDatum",
    # location
    "Bundesland",
    "Landkreis",
    "Gemeinde",
    "Postleitzahl",
    "Ort",
    "Strasse",
    "Hausnummer",
    "Laengengrad",
    "Breitengrad",
    "UTM_zone",
    "UTM_ost",
    "UTM_nord",
    # wind technique
    "Hersteller",
    "Typenbezeichnung",
    "Nabenhoehe",
    "Rotordurchmesser",
    "Bruttoleistung",
    "Nettonennleistung",
    "WindAnLandOderAufSee",
    "Seelage",
    "NameWindpark",
    "Kraftwerksnummer",
    "Nachtkennzeichnung",
    "Rotorblattenteisungssystem",
    # grid
    "AnschlussAnHoechstOderHochSpannung",
    "FernsteuerbarkeitNb",
    "FernsteuerbarkeitDv",
    "Einspeisungsart",
    # operator
    "Marktakteur_Firmenname",
    "Marktakteur_MarktakteurNachname",
    "Marktakteur_Ort",
    "Marktakteur_Bundesland",
    "Marktakteur_Land",
]


def select_display_columns(df: pd.DataFrame) -> list[str]:
    """Return the columns to display for the given dataframe, in configured order.

    Column names are matched case-insensitively (the CSV headers are
    lowercased by PostgreSQL); the actual dataframe column names are returned.
    Unknown names are skipped; an empty configuration shows all columns.
    """
    if not TABLE_DISPLAY_COLUMNS:
        return list(df.columns)
    actual_names = {name.lower(): name for name in df.columns}
    return [actual_names[name.lower()] for name in TABLE_DISPLAY_COLUMNS if name.lower() in actual_names]
