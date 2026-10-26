import os
import sys
from enum import Enum


def get_env_var(env_key: str) -> str:
    env_value = os.getenv(env_key)
    if env_value is None:
        print(f"Error: Environment variable {env_key} is not set.", file=sys.stderr)
        sys.exit(1)
    return env_value


MASTR_STATIC_URL = get_env_var("MASTR_STATIC_URL")
MASTR_STATIC_PUBLIC_URL = get_env_var("MASTR_STATIC_PUBLIC_URL")
MASTR_STATIC_EXPORTS_URL = MASTR_STATIC_URL + "/export/"
MASTR_STATIC_EXPORTS_PUBLIC_URL = MASTR_STATIC_PUBLIC_URL + "/export/"
MASTR_SOURCE_URL = "https://www.marktstammdatenregister.de/MaStR/Datendownload"

__IMPORT_TIMESTAMP_PATH = "/import_timestamp"
__DUMP_DATE_PATH = "/dump_date"

IMPORT_TIMESTAMP_URL = MASTR_STATIC_EXPORTS_URL + __IMPORT_TIMESTAMP_PATH
DUMP_DATE_URL = MASTR_STATIC_EXPORTS_URL + __DUMP_DATE_PATH


# todo -> correct names
class EnergySources(Enum):
    WIND = "Wind-Einheiten"
    BIOMASSE = "Biomasse-Einheiten"
    SOLAR = "Solar-Einheiten"
    KERN = "Kernkraft-Einheiten"
    WASSER = "Wasser-Einheiten"
    VERBRENNUNG = "Verbrennung-Einheiten"


_states = {
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "BW": "Baden-Wuerttemberg",
    "BY": "Bayern",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "NW": "Nordrhein-westfalen",
    "SA": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "BE": "Berlin",
    "HE": "Hessen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "TH": "Thueringen",
}

_nation = {"DE": "Deutschland"}


class DownloadFormats(Enum):
    PARQUET = ".parq"
    CSV = ".csv"
    EXCEL = ".xlsx"


DEFAULT_ENTITY_VALUE = "DE"  # this entity is available for all energy sources

WIND_ENTITES = {}
WIND_ENTITES.update(_nation)
WIND_ENTITES.update(_states)

SOLAR_ENTITES = {}
SOLAR_ENTITES.update(_nation)
SOLAR_ENTITES.update(_states)

VERBRENNUNG_ENTITES = {}
VERBRENNUNG_ENTITES.update(_nation)
VERBRENNUNG_ENTITES.update(_states)

BIOMASSE_ENTITES = {}
BIOMASSE_ENTITES.update(_nation)
BIOMASSE_ENTITES.update(_states)

KERN_ENTITES = {}
KERN_ENTITES.update(_nation)

WASSER_ENTITES = {}
WASSER_ENTITES.update(_nation)
WASSER_ENTITES.update(_states)

ENTITY_MAP = {
    EnergySources.WIND: WIND_ENTITES,
    EnergySources.SOLAR: SOLAR_ENTITES,
    EnergySources.BIOMASSE: BIOMASSE_ENTITES,
    EnergySources.KERN: KERN_ENTITES,
    EnergySources.WASSER: WASSER_ENTITES,
    EnergySources.VERBRENNUNG: VERBRENNUNG_ENTITES,
}


if __name__ == "__main__":
    print(ENTITY_MAP[EnergySources.WIND])
