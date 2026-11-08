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

# energy sources offered on the maps page, in dropdown order; the map
# callbacks accept only these (and map_states)
map_sources = [
    EnergySources.WIND.value,
    EnergySources.SOLAR.value,
    EnergySources.BIOMASSE.value,
    EnergySources.WASSER.value,
    EnergySources.GEOTHERMIE_GRUBENGAS_DRUCKENTSPANNUNG.value,
    EnergySources.KERNKRAFT.value,
    EnergySources.VERBRENNUNG.value,
    EnergySources.STROMSPEICHER.value,
    EnergySources.GASERZEUGER.value,
    EnergySources.GASSPEICHER.value,
    EnergySources.GASVERBRAUCHER.value,
]

# the state selection of the maps page ends with all of Germany
MAP_GERMANY = "Alle (Deutschland)"
map_states = [*static_table_states, MAP_GERMANY]
# too many units for a map of all of Germany
map_sources_without_germany = {EnergySources.SOLAR.value, EnergySources.STROMSPEICHER.value}
