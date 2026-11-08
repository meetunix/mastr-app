"""Units of the maps page and their EEG plants, read from the database of
mastr-tool.

The rows of the unit details have the same shape as the rows of the exports:
lowercase column names, the operator columns prefixed with "marktakteur_",
catalog IDs replaced by their text, booleans as ja/nein and all values as
text. So the field configuration in map_fields.py uses the column names of
the exports. The columns of the storage plant of a Stromspeicher are prefixed
with "speicher_", the EEG plant is returned separately.
"""

import pandas as pd
from psycopg import sql
from psycopg.rows import tuple_row

from .constants import EnergySources
from .database import as_export_text, ready_columns, run
from .map_fields import detail_columns, eeg_columns, name_column, title_suffix_column

# unit tables of mastr-tool (Einheiten in db/entities.py)
UNIT_TABLES = {
    EnergySources.WIND: "einheitenwind",
    EnergySources.SOLAR: "einheitensolar",
    EnergySources.BIOMASSE: "einheitenbiomasse",
    EnergySources.WASSER: "einheitenwasser",
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG: "einheitengeothermiegrubengasdruckentspannung",
    EnergySources.KERNKRAFT: "einheitenkernkraft",
    EnergySources.VERBRENNUNG: "einheitenverbrennung",
    EnergySources.STROMSPEICHER: "einheitenstromspeicher",
    EnergySources.GASERZEUGER: "einheitengaserzeuger",
    EnergySources.GASSPEICHER: "einheitengasspeicher",
    EnergySources.GASVERBRAUCHER: "einheitengasverbraucher",
}
# EEG plants (Einheiten.AnlagenEeg*), referred to by the EegMaStRNummer of a
# unit; the other energy sources have no EEG data
EEG_TABLES = {
    EnergySources.WIND: "anlageneegwind",
    EnergySources.SOLAR: "anlageneegsolar",
    EnergySources.BIOMASSE: "anlageneegbiomasse",
    EnergySources.WASSER: "anlageneegwasser",
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG: "anlageneeggeothermiegrubengasdruckentspannung",
    EnergySources.STROMSPEICHER: "anlageneegspeicher",
}
OPERATOR_TABLE = "marktakteure"
OPERATOR_PREFIX = "marktakteur_"
EEG_PREFIX = "eeg_"
# storage plant of a Stromspeicher unit (Einheiten.AnlagenStromSpeicher)
STORAGE_TABLE = "anlagenstromspeicher"
STORAGE_PREFIX = "speicher_"
CATALOG_TABLE = "katalogwerte"

# The columns used on the maps page that hold catalog IDs, as in
# db/entities.py of mastr-tool (udf=SelectUDFs.Katalog). A column with
# catalog IDs used in map_fields.py has to be listed here, otherwise the ID
# is shown instead of its text.
CATALOG_COLUMNS = {
    "acdckoppelung",
    "artdersolaranlage",
    "artderwasserkraftanlage",
    "artdeszuflusses",
    "batterietechnologie",
    "biomasseart",
    "einheitbetriebsstatus",
    "einheitsystemstatus",
    "einspeisungsart",
    "energietraeger",
    "hauptausrichtung",
    "hauptausrichtungneigungswinkel",
    "hauptbrennstoff",
    "hersteller",
    "netzbetreiberpruefungstatus",
    "nutzungsbereich",
    "speicherart",
    "technologie",
    EEG_PREFIX + "anlagebetriebsstatus",
}

# The catalog IDs of a state: the units refer to their own Bundesland catalog
# entries, the name also matches the ones of the operators, which is harmless
# here. The IDs are passed to the unit query as values: with a subquery
# instead, the planner can't estimate how many units a state has and reads
# e.g. all 6.6 million Solar units even for Bremen.
_STATE_IDS = "SELECT coalesce(array_agg(id), '{}') AS ids FROM katalogwerte WHERE wert = %s"
# units of the selected states (the unit table is "u")
_IN_STATE = sql.SQL("WHERE u.bundesland = ANY(%s)")
_IN_GERMANY = sql.SQL("WHERE true")
# The map query is answered from a partial covering index of mastr-tool
# (MapIndices in db/entities.py: key Bundesland, this coordinate condition,
# the map columns included) without reading the table, e.g. 2 GB for Solar.
# Keep the condition and the columns of fetch_map_units in sync with it.
_HAS_COORDINATES = sql.SQL(" AND u.breitengrad BETWEEN -90 AND 90 AND u.laengengrad BETWEEN -180 AND 180")


def has_eeg(source: EnergySources) -> bool:
    return source in EEG_TABLES


def _joined_tables(source: EnergySources) -> dict[str, tuple[str, str, str]]:
    """Tables joined to the unit table: column prefix -> (table, alias, join condition)."""
    tables = {OPERATOR_PREFIX: (OPERATOR_TABLE, "m", "m.mastrnummer = u.anlagenbetreibermastrnummer")}
    if has_eeg(source):
        tables[EEG_PREFIX] = (EEG_TABLES[source], "e", "e.eegmastrnummer = u.eegmastrnummer")
    if source is EnergySources.STROMSPEICHER:
        tables[STORAGE_PREFIX] = (STORAGE_TABLE, "s", "s.mastrnummer = u.spemastrnummer")
    return tables


def _select(
    source: EnergySources, columns: list[str], available: dict[str, set[str]], floats: frozenset[str] = frozenset()
) -> sql.Composed:
    """SELECT of the given columns (lowercase, columns of joined tables
    prefixed) of a unit, without WHERE clause; the unit table is "u". A table
    is joined if it is in available. Columns missing in the tables are left
    out; the columns in floats are returned as float."""
    joined = _joined_tables(source)
    fields, joins = [], []
    for column in dict.fromkeys(columns):
        prefix = next((prefix for prefix in joined if column.startswith(prefix)), "")
        table, alias, _ = joined[prefix] if prefix else (UNIT_TABLES[source], "u", "")
        name = column.removeprefix(prefix)
        if name not in available.get(table, ()):
            continue
        value = sql.Identifier(alias, name)
        if column in CATALOG_COLUMNS:
            catalog = sql.Identifier(f"k{len(joins)}")
            joins.append(
                sql.SQL("LEFT JOIN {} {} ON {}.id = {}").format(sql.Identifier(CATALOG_TABLE), catalog, catalog, value)
            )
            value = sql.SQL("{}.wert").format(catalog)
        elif column in floats:
            value = sql.SQL("{}::float8").format(value)
        fields.append(sql.SQL("{} AS {}").format(value, sql.Identifier(column)))
    table_joins = [
        sql.SQL("LEFT JOIN {} {} ON {}").format(sql.Identifier(table), sql.Identifier(alias), sql.SQL(condition))
        for table, alias, condition in joined.values()
        if table in available
    ]
    return sql.SQL("SELECT {} FROM {} u {} ").format(
        sql.SQL(", ").join(fields), sql.Identifier(UNIT_TABLES[source]), sql.SQL(" ").join([*table_joins, *joins])
    )


def _title_columns(source: EnergySources) -> list[str]:
    return [column.lower() for column in (name_column(source), title_suffix_column(source)) if column]


def fetch_map_units(source: EnergySources, state: str | None) -> tuple[pd.DataFrame, int]:
    """The units of the energy source in the state (None: all of Germany)
    that have coordinates, with the columns needed for the map (coordinates
    and power as float, text columns with "" for NULL), and the number of all
    units of the selection (also those without coordinates).
    Raises DatabaseUnavailable / DatabaseUpdating."""
    columns = [
        "einheitmastrnummer",
        "breitengrad",
        "laengengrad",
        "einheitbetriebsstatus",
        "nettonennleistung",
        *_title_columns(source),
    ]
    floats = frozenset({"breitengrad", "laengengrad", "nettonennleistung"})

    def work(connection):
        available = ready_columns(connection, [UNIT_TABLES[source], CATALOG_TABLE])
        if state is None:
            where, params = _IN_GERMANY, ()
        else:
            where, params = _IN_STATE, (connection.execute(_STATE_IDS, (state,)).fetchone()["ids"],)
        query = _select(source, columns, available, floats) + where + _HAS_COORDINATES
        count = sql.SQL("SELECT count(*) AS total FROM {} u ").format(sql.Identifier(UNIT_TABLES[source])) + where
        # both queries in one round trip
        with connection.pipeline():
            units = connection.cursor(row_factory=tuple_row).execute(query, params)
            total = connection.execute(count, params)
        return units.fetchall(), [description.name for description in units.description], total.fetchone()["total"]

    rows, names, total = run(work)
    df = pd.DataFrame(rows, columns=names)
    text = [name for name in names if name not in floats]
    df[text] = df[text].fillna("")
    return df, total


def fetch_unit(source: EnergySources, unit_id: str) -> tuple[dict[str, str], dict[str, str] | None] | None:
    """The unit with the given MaStR number with the columns of its details
    (see map_fields.py) and its EEG plant, all as text; None if the unit
    doesn't exist. The EEG plant is None if the energy source has no EEG
    data or the plant is not in the database. Raises DatabaseUnavailable /
    DatabaseUpdating."""
    columns = [*detail_columns(source), "eegmastrnummer", *_title_columns(source)]
    if has_eeg(source):
        columns += [EEG_PREFIX + column for column in eeg_columns(source)]
    tables = [UNIT_TABLES[source], CATALOG_TABLE, *(table for table, _, _ in _joined_tables(source).values())]

    def work(connection):
        available = ready_columns(connection, tables)
        query = _select(source, columns, available) + sql.SQL("WHERE u.einheitmastrnummer = %s")
        return connection.execute(query, (unit_id,)).fetchone()

    row = run(work)
    if row is None:
        return None
    values = {column: as_export_text(value) for column, value in row.items()}
    unit = {column: value for column, value in values.items() if not column.startswith(EEG_PREFIX)}
    eeg = {column.removeprefix(EEG_PREFIX): value for column, value in values.items() if column.startswith(EEG_PREFIX)}
    return unit, eeg if eeg.get("eegmastrnummer") else None
