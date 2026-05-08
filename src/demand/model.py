"""Demand modeling - 4-step model implementation."""

from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict

from src.core.models import Zone, ODPair
from src.core.enums import TransportMode, Purpose, TimePeriod
from src.core.utils import logit_probability, nested_logit_probability
from src.core.exceptions import DemandModelError

logger = logging.getLogger(__name__)


class DemandModel:
    """4-step travel demand model."""

    def __init__(
        self,
        zones: Dict[int, Zone],
        time_periods: List[str] = None,
        modes: List[TransportMode] = None,
        purposes: List[Purpose] = None,
    ):
        """Initialize demand model.

        Args:
            zones: dictionary of zones
            time_periods: list of time period names
            modes: list of transport modes
            purposes: list of trip purposes
        """
        self.zones = zones
        self.time_periods = time_periods or ["AM", "PM", "OFF"]
        self.modes = modes or [
            TransportMode.CAR,
            TransportMode.TRANSIT,
            TransportMode.WALK,
        ]
        self.purposes = purposes or [Purpose.WORK, Purpose.SCHOOL, Purpose.OTHER]

        # Calibration parameters
        self.trip_rate_parameters: Dict[str, float] = {}
        self.distribution_parameters: Dict[str, float] = {}
        self.mode_choice_parameters: Dict[str, float] = {}

    def trip_generation(
        self, trip_rates: Dict[str, float], attraction_rates: Dict[str, float]
    ) -> Dict[int, float]:
        """Step 1: Trip Generation.

        Args:
            trip_rates: rate of trips per capita by purpose
            attraction_rates: rate of attraction per capita by purpose

        Returns:
            productions and attractions by zone
        """
        productions = {}
        attractions = {}

        for zone_id, zone in self.zones.items():
            # Productions: based on population
            zone_productions = 0
            for purpose, rate in trip_rates.items():
                zone_productions += zone.population * rate

            productions[zone_id] = zone_productions

            # Attractions: based on employment and other activities
            zone_attractions = 0
            for purpose, rate in attraction_rates.items():
                if purpose == "work":
                    zone_attractions += zone.employment * rate
                elif purpose == "school":
                    zone_attractions += zone.school_enrollment * rate
                else:
                    zone_attractions += zone.population * rate

            attractions[zone_id] = zone_attractions

        logger.info(f"Generated trips: {sum(productions.values()):.0f}")
        return {"productions": productions, "attractions": attractions}

    def trip_distribution(
        self,
        productions: Dict[int, float],
        attractions: Dict[int, float],
        impedance_matrix: Dict[Tuple[int, int], float],
        decay_parameter: float = 0.05,
        iterations: int = 100,
    ) -> Dict[Tuple[int, int], float]:
        """Step 2: Trip Distribution (Gravity Model).

        Args:
            productions: trips produced by zone
            attractions: trips attracted to zone
            impedance_matrix: travel times between zones
            decay_parameter: friction decay factor
            iterations: balancing iterations

        Returns:
            OD matrix with distributed trips
        """
        # Initialize
        od_matrix = {}
        for orig, prod in productions.items():
            for dest, attr in attractions.items():
                if orig != dest:
                    time = impedance_matrix.get((orig, dest), 30)
                    friction = pow(time, -decay_parameter)
                    od_matrix[(orig, dest)] = friction
                else:
                    od_matrix[(orig, dest)] = 0

        # Furness balancing
        for iteration in range(iterations):
            # Balance productions
            for orig in productions:
                row_sum = sum(
                    od_matrix.get((orig, dest), 0) for dest in attractions
                )
                if row_sum > 0:
                    factor = productions[orig] / row_sum
                    for dest in attractions:
                        od_matrix[(orig, dest)] *= factor

            # Balance attractions
            for dest in attractions:
                col_sum = sum(
                    od_matrix.get((orig, dest), 0) for orig in productions
                )
                if col_sum > 0:
                    factor = attractions[dest] / col_sum
                    for orig in productions:
                        od_matrix[(orig, dest)] *= factor

        logger.info(f"Distributed OD pairs: {len(od_matrix)}")
        return od_matrix

    def modal_split(
        self,
        od_trips: Dict[Tuple[int, int], float],
        mode_utilities: Dict[TransportMode, Dict[Tuple[int, int], float]],
        nesting_structure: Optional[Dict] = None,
    ) -> Dict[Tuple[Tuple[int, int], TransportMode], float]:
        """Step 3: Modal Split (Logit Model).

        Args:
            od_trips: OD matrix
            mode_utilities: utilities by mode for each OD pair
            nesting_structure: nested logit structure

        Returns:
            OD matrix by mode
        """
        od_by_mode = {}

        for (orig, dest), trips in od_trips.items():
            if trips <= 0:
                continue

            # Get utilities for this OD pair
            utilities = {
                mode: mode_utilities.get(mode, {}).get((orig, dest), 0)
                for mode in self.modes
            }

            if not utilities or max(utilities.values()) == 0:
                # Default split if no utilities provided
                split = {mode: trips / len(self.modes) for mode in self.modes}
            else:
                utilities_list = list(utilities.values())
                split = {
                    mode: trips * logit_probability(utilities[mode], utilities_list)
                    for mode in self.modes
                }

            for mode, mode_trips in split.items():
                od_by_mode[((orig, dest), mode)] = mode_trips

        logger.info(f"Modal split complete: {len(od_by_mode)} mode pairs")
        return od_by_mode

    def time_of_day_adjustment(
        self,
        od_trips: Dict[Tuple[Tuple[int, int], TransportMode], float],
        tod_factors: Dict[str, float],
    ) -> Dict[Tuple[Tuple[int, int], TransportMode, str], float]:
        """Step 4: Time-of-Day Adjustment.

        Args:
            od_trips: OD trips by mode
            tod_factors: factors for each time period (should sum to 1.0)

        Returns:
            OD trips by mode and time period
        """
        if not tod_factors or sum(tod_factors.values()) == 0:
            tod_factors = {period: 1 / len(self.time_periods) for period in self.time_periods}

        od_final = {}
        for (orig_dest, mode), trips in od_trips.items():
            for period, factor in tod_factors.items():
                key = (orig_dest, mode, period)
                od_final[key] = trips * factor

        logger.info(f"Time-of-day adjustment complete")
        return od_final

    def run_full_model(
        self,
        trip_rates: Dict[str, float],
        attraction_rates: Dict[str, float],
        impedance_matrix: Dict[Tuple[int, int], float],
        mode_utilities: Optional[Dict[TransportMode, Dict[Tuple[int, int], float]]] = None,
        tod_factors: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """Run complete 4-step model."""
        logger.info("Starting 4-step demand model")

        # Step 1: Generation
        gen_result = self.trip_generation(trip_rates, attraction_rates)
        productions = gen_result["productions"]
        attractions = gen_result["attractions"]

        # Step 2: Distribution
        od_matrix = self.trip_distribution(productions, attractions, impedance_matrix)

        # Step 3: Modal split
        if mode_utilities is None:
            # Simple mode utilities based on impedance
            mode_utilities = {
                mode: impedance_matrix.copy() for mode in self.modes
            }

        od_by_mode = self.modal_split(od_matrix, mode_utilities)

        # Step 4: Time of day
        if tod_factors is None:
            tod_factors = {period: 1 / len(self.time_periods) for period in self.time_periods}

        od_final = self.time_of_day_adjustment(od_by_mode, tod_factors)

        logger.info(
            f"Model complete: {sum(od_final.values()):.0f} trips generated"
        )

        return od_final


class ModalChoiceModel:
    """Discrete choice model for mode selection."""

    def __init__(self, parameters: Optional[Dict] = None):
        """Initialize mode choice model.

        Parameters typically include:
        - cost_coeff: coefficient for cost (negative)
        - time_coeff: coefficient for time (negative)
        - mode_asc: alternative specific constants by mode
        """
        self.parameters = parameters or {
            "cost_coeff": -0.05,
            "time_coeff": -0.02,
            "walk_asc": 0.5,
            "bike_asc": 0.3,
            "transit_asc": 0,
            "car_asc": 0.2,
        }

    def calculate_utility(
        self,
        mode: TransportMode,
        travel_time: float,
        travel_cost: float,
        distance: float = 0,
    ) -> float:
        """Calculate utility for a mode."""
        asc = self.parameters.get(f"{mode.value}_asc", 0)
        cost_coeff = self.parameters.get("cost_coeff", -0.05)
        time_coeff = self.parameters.get("time_coeff", -0.02)

        utility = asc + cost_coeff * travel_cost + time_coeff * travel_time

        # Mode-specific adjustments
        if mode == TransportMode.WALK and distance > 1.5:
            utility -= 2  # Reduce utility for long walks
        elif mode == TransportMode.BIKE and distance > 5:
            utility -= 1

        return utility
