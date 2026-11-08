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

NUMERIC_DISPLAY_COLUMNS lists the displayed columns with numeric values. The
CSV files are read as text, so that values such as postcodes keep their
leading zeros; these columns are converted to numbers for display, so that
sorting and filters such as "> 3000" compare numerically. Names are matched
case-insensitively as well.

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

NUMERIC_DISPLAY_COLUMNS = [
    "Laengengrad",
    "Breitengrad",
    "UTM_zone",
    "UTM_ost",
    "UTM_nord",
    "Nabenhoehe",
    "Rotordurchmesser",
    "Bruttoleistung",
    "Nettonennleistung",
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


def to_display_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return the displayed part of a dataframe read as text.

    Selects the display columns, turns empty cells into missing values (the
    table sorts them last and sends them as null) and converts the numeric
    display columns to numbers. A numeric column is left as text if any of
    its values is not a number, so no value is hidden.
    """
    display_df = df[select_display_columns(df)]
    display_df = display_df.mask(display_df == "")
    numeric_names = {name.lower() for name in NUMERIC_DISPLAY_COLUMNS}
    for column in display_df.columns:
        if column.lower() in numeric_names:
            numbers = pd.to_numeric(display_df[column], errors="coerce")
            if numbers.count() == display_df[column].count():
                display_df[column] = numbers
    return display_df
