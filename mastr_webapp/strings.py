"""
String definitions for the frontend.
"""

from .constants import *

# energy sources offered on the tables page, in dropdown order; the table
# callbacks accept only these (and static_table_states) as input
static_table_sources = [
    EnergySources.WIND.value,
    EnergySources.BIOMASSE.value,
    EnergySources.WASSER.value,
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG.value,
    EnergySources.KERNKRAFT.value,
    EnergySources.VERBRENNUNG.value,
    EnergySources.GASERZEUGER.value,
    EnergySources.GASSPEICHER.value,
    EnergySources.GASVERBRAUCHER.value,
]

# display names of the states with table downloads, in dropdown order
static_table_states = [
    "Mecklenburg-Vorpommern",
    "Niedersachsen",
    "Baden-Württemberg",
    "Bayern",
    "Brandenburg",
    "Bremen",
    "Hamburg",
    "Nordrhein-Westfalen",
    "Sachsen",
    "Sachsen-Anhalt",
    "Schleswig-Holstein",
    "Berlin",
    "Hessen",
    "Rheinland-Pfalz",
    "Saarland",
    "Thüringen",
]
