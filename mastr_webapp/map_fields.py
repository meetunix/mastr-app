"""Configuration of the unit details shown on the maps page.

When a unit is clicked on the map, its 24 most important fields are shown
next to the map, grouped into sections. MAP_DETAIL_SECTIONS defines them per
energy source: the sections in display order, each with its fields.

Configuration rules:
- A field shows one or more columns of a unit, read from the database of
  mastr-tool (see units.py). The column names are the ones of the exports
  (e.g. the CSV headers), matched case-insensitively: the columns of the unit
  tables, the operator columns prefixed with "Marktakteur_" and for the
  Stromspeicher the storage columns (AnlagenStromSpeicher) prefixed with
  "Speicher_". Columns with catalog IDs have to be listed in units.py
  (CATALOG_COLUMNS).
- The non-empty values of the columns are formatted and joined with the
  field's separator; a field without any value is shown as EMPTY_VALUE.
- Columns that do not exist in a table are treated as empty, so renaming or
  removing columns in mastr-tool does not break the details.
- The format function is applied to each value: dates and numbers are shown
  in German notation, numbers optionally with a unit. Values that can't be
  parsed are shown unchanged.

EEG_DETAIL_FIELDS defines the fields of the EEG plant of a unit, shown below
the 24 fields (see units.py). The columns are the ones of the EEG tables
(AnlagenEeg*); booleans are shown as ja/nein, as in the exports. EEG fields
whose columns don't exist in the EEG table of the energy source are left out
(e.g. AusschreibungZuschlag, which the tables of Wasser and Geothermie don't
have).
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date as _date
from functools import partial

from .constants import EnergySources

EMPTY_VALUE = "–"


def as_text(value: str) -> str:
    return value


def as_date(value: str) -> str:
    """'2019-02-23' or a timestamp such as '2026-10-14 07:06:11.88' -> '23.02.2019'."""
    try:
        return _date.fromisoformat(value[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return value


def as_number(value: str | float, unit: str = "") -> str:
    """'1234.500' -> '1.234,5' (German notation, at most three decimals), with an optional unit."""
    try:
        number = float(value)
    except ValueError:
        return value
    text = f"{number:,.3f}".rstrip("0").rstrip(".").translate(str.maketrans(",.", ".,"))
    return f"{text} {unit}" if unit else text


def as_integer(value: str) -> str:
    """'596647.37' -> '596647' (UTM coordinates, without thousands separators)."""
    try:
        return str(round(float(value)))
    except ValueError:
        return value


def as_list(value: str) -> str:
    """'SEE1;SEE2, SEE3' -> 'SEE1, SEE2, SEE3' (MaStR numbers of linked units)."""
    return ", ".join(part.strip() for part in re.split(r"[;,]", value) if part.strip())


as_kw = partial(as_number, unit="kW")
as_kwh = partial(as_number, unit="kWh")
as_meters = partial(as_number, unit="m")


@dataclass(frozen=True)
class Field:
    label: str
    columns: tuple[str, ...]
    format: Callable[[str], str] = as_text
    separator: str = " "

    def value(self, row: dict[str, str]) -> str:
        """Display value of the field for a row with lowercase column names."""
        values = [row.get(column.lower(), "").strip() for column in self.columns]
        text = self.separator.join(self.format(value) for value in values if value)
        return text or EMPTY_VALUE


# the name column differs between the power and the gas units
NAME_COLUMNS = {
    EnergySources.GASERZEUGER: "NameGaserzeugungseinheit",
    EnergySources.GASSPEICHER: "NameGasspeicher",
    EnergySources.GASVERBRAUCHER: "NameGasverbrauchsseinheit",
}
DEFAULT_NAME_COLUMN = "NameStromerzeugungseinheit"

# the title of a unit (map tooltip and details header) adds the value of this
# column in parentheses: "<name> (<wind farm>)"
TITLE_SUFFIX_COLUMNS = {
    EnergySources.WIND: "NameWindpark",
    EnergySources.SOLAR: "NameDesSolarparks",
}

# 5 fields (without the name)
_GENERAL = [
    Field("MaStR-Nr. der Einheit", ("EinheitMastrNummer",)),
    Field("Betriebsstatus", ("EinheitBetriebsstatus",)),
    Field("Inbetriebnahme", ("Inbetriebnahmedatum",), as_date),
    Field("Geplante Inbetriebnahme", ("GeplantesInbetriebnahmedatum",), as_date),
    Field("Endgültige Stilllegung", ("DatumEndgueltigeStilllegung",), as_date),
]

# 7 fields
_LOCATION = [
    Field("Straße", ("Strasse", "Hausnummer")),
    Field("PLZ / Ort", ("Postleitzahl", "Ort")),
    Field("Gemeinde", ("Gemeinde",)),
    Field("Landkreis", ("Landkreis",)),
    Field("Gemarkung / Flurstück", ("Gemarkung", "FlurFlurstuecknummern"), separator=", "),
    Field("Koordinaten (Breite, Länge)", ("Breitengrad", "Laengengrad"), separator=", "),
    Field("UTM (Zone / Ost / Nord)", ("UTM_zone", "UTM_ost", "UTM_nord"), as_integer, separator=" / "),
]

# 5 fields; personal names of natural persons are not part of the public data
_OPERATOR = [
    Field(
        "Betreiber",
        ("Marktakteur_Firmenname", "Marktakteur_MarktakteurVorname", "Marktakteur_MarktakteurNachname"),
    ),
    Field("MaStR-Nr. des Betreibers", ("AnlagenbetreiberMastrNummer",)),
    Field("Sitz des Betreibers", ("Marktakteur_Postleitzahl", "Marktakteur_Ort")),
    # the date is left unchanged by as_date: "Geprüft am 14.10.2026"
    Field("Netzbetreiberprüfung", ("NetzbetreiberpruefungStatus", "NetzbetreiberpruefungDatum"), as_date, " am "),
    Field("Letzte Aktualisierung", ("DatumLetzteAktualisierung",), as_date),
]

_NET_POWER = Field("Nettonennleistung", ("Nettonennleistung",), as_kw)
_GROSS_POWER = Field("Bruttoleistung", ("Bruttoleistung",), as_kw)
_TECHNOLOGY = Field("Technologie", ("Technologie",))
_FEED_IN = Field("Einspeisungsart", ("Einspeisungsart",))
_POWER_PLANT = Field("Kraftwerk", ("NameKraftwerk",))

# the gas units have fewer technical fields; registration data fills the rest
_GAS_REGISTER = [
    Field("Registrierung", ("Registrierungsdatum",), as_date),
    Field("MaStR-Nr. der Lokation", ("LokationMastrNummer",)),
    Field("Systemstatus", ("EinheitSystemstatus",)),
]

# Technical fields per energy source. The gas quantities are shown without
# a unit, the exports don't state it.
_TECHNICAL = {
    EnergySources.WIND: [
        _NET_POWER,
        Field("Hersteller", ("Hersteller",)),
        Field("Typenbezeichnung", ("Typenbezeichnung",)),
        Field("Nabenhöhe", ("Nabenhoehe",), as_meters),
        Field("Rotordurchmesser", ("Rotordurchmesser",), as_meters),
        Field("Windpark", ("NameWindpark",)),
    ],
    EnergySources.SOLAR: [
        _NET_POWER,
        _GROSS_POWER,
        Field("Art der Solaranlage", ("ArtDerSolaranlage",)),
        Field("Nutzungsbereich", ("Nutzungsbereich",)),
        Field("Hauptausrichtung", ("Hauptausrichtung", "HauptausrichtungNeigungswinkel"), separator=", "),
        Field("Solarpark", ("NameDesSolarparks",)),
    ],
    EnergySources.STROMSPEICHER: [
        _NET_POWER,
        Field("Nutzbare Speicherkapazität", ("Speicher_NutzbareSpeicherkapazitaet",), as_kwh),
        _TECHNOLOGY,
        Field("Batterietechnologie", ("Batterietechnologie",)),
        Field("AC/DC-Kopplung", ("AcDcKoppelung",)),
        _FEED_IN,
    ],
    EnergySources.BIOMASSE: [
        _NET_POWER,
        _GROSS_POWER,
        Field("Hauptbrennstoff", ("Hauptbrennstoff",)),
        Field("Biomasseart", ("Biomasseart",)),
        _TECHNOLOGY,
        _FEED_IN,
    ],
    EnergySources.WASSER: [
        _NET_POWER,
        _GROSS_POWER,
        _POWER_PLANT,
        Field("Art der Wasserkraftanlage", ("ArtDerWasserkraftanlage",)),
        Field("Art des Zuflusses", ("ArtDesZuflusses",)),
        _FEED_IN,
    ],
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG: [
        _NET_POWER,
        _GROSS_POWER,
        Field("Energieträger", ("Energietraeger",)),
        _TECHNOLOGY,
        _FEED_IN,
        Field("Fernsteuerbar (Netzbetreiber)", ("FernsteuerbarkeitNb",)),
    ],
    EnergySources.KERNKRAFT: [
        _NET_POWER,
        _GROSS_POWER,
        _POWER_PLANT,
        Field("Kraftwerksblock", ("NameKraftwerksblock",)),
        _TECHNOLOGY,
        Field("Anschluss an Höchst-/Hochspannung", ("AnschlussAnHoechstOderHochSpannung",)),
    ],
    EnergySources.VERBRENNUNG: [
        _NET_POWER,
        _GROSS_POWER,
        Field("Kraftwerk / Block", ("NameKraftwerk", "NameKraftwerksblock"), separator=" / "),
        Field("Hauptbrennstoff", ("Hauptbrennstoff",)),
        _TECHNOLOGY,
        _FEED_IN,
    ],
    EnergySources.GASERZEUGER: [
        Field("Erzeugungsleistung", ("Erzeugungsleistung",), as_number),
        _TECHNOLOGY,
        Field("MaStR-Nr. des Speichers", ("SpeicherMastrNummer",)),
    ],
    EnergySources.GASSPEICHER: [
        Field("Speicherart", ("Speicherart",)),
        Field("Max. nutzbares Arbeitsgasvolumen", ("MaximalNutzbaresArbeitsgasvolumen",), as_number),
        Field("Max. Einspeicherleistung", ("MaximaleEinspeicherleistung",), as_number),
        Field("Max. Ausspeicherleistung", ("MaximaleAusspeicherleistung",), as_number),
        Field("Durchschnittlicher Brennwert", ("DurchschnittlicherBrennwert",), as_number),
    ],
    EnergySources.GASVERBRAUCHER: [
        Field("Max. Gasbezugsleistung", ("MaximaleGasbezugsleistung",), as_number),
        Field("Dient der Stromerzeugung", ("EinheitDientDerStromerzeugung",)),
        Field("Verknüpfte Einheiten", ("VerknuepfteEinheitenMastrNummern",), as_list),
    ],
}

# filled up to 24 fields for the sources with few technical fields
_REGISTER = {
    EnergySources.GASERZEUGER: _GAS_REGISTER,
    EnergySources.GASSPEICHER: _GAS_REGISTER[:1],
    EnergySources.GASVERBRAUCHER: _GAS_REGISTER,
}


def name_column(source: EnergySources) -> str:
    return NAME_COLUMNS.get(source, DEFAULT_NAME_COLUMN)


def title_suffix_column(source: EnergySources) -> str:
    """The column added to the title, "" for sources without one."""
    return TITLE_SUFFIX_COLUMNS.get(source, "")


def unit_title(name: str, suffix: str, unit_id: str) -> str:
    """'<name> (<suffix>)'. Without a name the MaStR number is used; the
    suffix is left out if it is empty or the same as the name."""
    name, suffix = name.strip(), suffix.strip()
    title = name or unit_id
    return f"{title} ({suffix})" if suffix and suffix != name else title


def _sections(source: EnergySources) -> list[tuple[str, list[Field]]]:
    return [
        ("Allgemein", [Field("Name", (name_column(source),)), *_GENERAL]),
        ("Standort", _LOCATION),
        ("Technik", _TECHNICAL[source]),
        ("Betreiber & Register", [*_OPERATOR, *_REGISTER.get(source, [])]),
    ]


MAP_DETAIL_SECTIONS = {source: _sections(source) for source in _TECHNICAL}


# fields of the EEG plants, see units.py; as_date and as_kw leave "ja"/"nein"
# unchanged, e.g. "ja seit 01.07.2014"
_EEG_HEAD = [
    Field("EEG-MaStR-Nr.", ("EegMaStRNummer",)),
    Field("Anlagenschlüssel", ("AnlagenschluesselEeg",)),
    Field("EEG-Inbetriebnahme", ("EegInbetriebnahmedatum",), as_date),
    Field("Installierte Leistung", ("InstallierteLeistung",), as_kw),
    Field("Betriebsstatus", ("AnlageBetriebsstatus",)),
]
_EEG_TENDER = [
    Field("Zuschlag aus Ausschreibung", ("AusschreibungZuschlag",)),
    Field("Zuschlagsnummer", ("Zuschlagsnummer",)),
]
_EEG_TAIL = [
    Field("Verknüpfte Einheiten", ("VerknuepfteEinheitenMaStRNummern",), as_list),
    Field("Registrierung", ("Registrierungsdatum",), as_date),
    Field("Letzte Aktualisierung", ("DatumLetzteAktualisierung",), as_date),
]

EEG_DETAIL_FIELDS = {
    EnergySources.WIND: [
        *_EEG_HEAD,
        *_EEG_TENDER,
        Field("Prototypanlage", ("PrototypAnlage",)),
        Field("Pilotanlage", ("PilotAnlage",)),
        # percent as registered; a few operators entered fractions instead
        Field("Ertragsschätzung / Referenzertrag (%)", ("VerhaeltnisErtragsschaetzungReferenzertrag",), as_number),
        Field("Ertrag nach 5 Jahren / Referenzertrag (%)", ("VerhaeltnisReferenzertragErtrag5Jahre",), as_number),
        *_EEG_TAIL,
    ],
    EnergySources.BIOMASSE: [
        *_EEG_HEAD,
        *_EEG_TENDER,
        Field("Ausschließlich Biomasse", ("AusschliesslicheVerwendungBiomasse",)),
        Field(
            "Flexibilitätsprämie",
            ("BiogasInanspruchnahmeFlexiPraemie", "BiogasDatumInanspruchnahmeFlexiPraemie"),
            as_date,
            " seit ",
        ),
        Field("Leistungserhöhung", ("BiogasLeistungserhoehung", "BiogasUmfangLeistungserhoehung"), as_kw, " um "),
        Field("Höchstbemessungsleistung", ("BiogasHoechstbemessungsleistung",), as_kw),
        *_EEG_TAIL,
    ],
    EnergySources.WASSER: [
        *_EEG_HEAD,
        *_EEG_TENDER,
        Field("Ertüchtigungen (IDs)", ("ErtuechtigungIds",), as_list),
        *_EEG_TAIL,
    ],
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG: [*_EEG_HEAD, *_EEG_TENDER, *_EEG_TAIL],
    EnergySources.SOLAR: [
        *_EEG_HEAD,
        Field("Zahlung nach EEG in Anspruch genommen", ("InanspruchnahmeZahlungNachEeg",)),
        Field("Mieterstrom", ("MieterstromZugeordnet",)),
        *_EEG_TENDER,
        Field("Zugeordnete Gebotsmenge", ("ZugeordneteGebotsmenge",), as_kw),
        *_EEG_TAIL,
    ],
    EnergySources.STROMSPEICHER: [*_EEG_HEAD, *_EEG_TENDER, *_EEG_TAIL],
}


def eeg_columns(source: EnergySources) -> list[str]:
    """The (lowercase) columns of the configured EEG fields of the energy source."""
    return [column.lower() for field in EEG_DETAIL_FIELDS[source] for column in field.columns]


def eeg_values(row: dict[str, str], source: EnergySources) -> list[tuple[str, str]]:
    """The configured EEG fields of an EEG plant as (label, display value)
    pairs. The row (from fetch_unit) has the existing columns of the EEG
    table, also the empty ones; fields without any of their columns are left
    out."""
    lower_row = {column.lower(): value for column, value in row.items()}
    return [
        (field.label, field.value(lower_row))
        for field in EEG_DETAIL_FIELDS[source]
        if any(column.lower() in lower_row for column in field.columns)
    ]


def detail_columns(source: EnergySources) -> list[str]:
    """The (lowercase) columns of the configured fields of the energy source."""
    return [column.lower() for _, fields in MAP_DETAIL_SECTIONS[source] for field in fields for column in field.columns]


def detail_values(row: dict[str, str], source: EnergySources) -> list[tuple[str, list[tuple[str, str]]]]:
    """The configured sections of a unit with (label, display value) pairs.

    The row maps the column names to the (text) values of the unit.
    """
    lower_row = {column.lower(): value for column, value in row.items()}
    return [
        (title, [(field.label, field.value(lower_row)) for field in fields])
        for title, fields in MAP_DETAIL_SECTIONS[source]
    ]
