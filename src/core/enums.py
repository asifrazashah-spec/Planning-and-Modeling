"""Enumerations for transportation modeling."""

from enum import Enum


class TransportMode(Enum):
    """Transportation modes."""

    CAR = "car"
    TAXI = "taxi"
    TRANSIT = "transit"
    BUS = "bus"
    METRO = "metro"
    BIKE = "bike"
    WALK = "walk"


class NodeType(Enum):
    """Node types in network."""

    REGULAR = "regular"
    ZONE_CENTROID = "zone_centroid"
    TRANSIT_STATION = "transit_station"
    PARKING = "parking"


class LinkType(Enum):
    """Link types."""

    FREEWAY = "freeway"
    ARTERIAL = "arterial"
    COLLECTOR = "collector"
    LOCAL = "local"
    TRANSIT = "transit"
    BIKE = "bike"


class Purpose(Enum):
    """Trip purposes."""

    WORK = "work"
    SCHOOL = "school"
    SHOPPING = "shopping"
    DINING = "dining"
    RECREATION = "recreation"
    OTHER = "other"
