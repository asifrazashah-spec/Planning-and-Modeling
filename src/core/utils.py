"""Utility functions for transportation modeling."""

import math
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate haversine distance in kilometers.
    
    Args:
        lat1, lon1: origin coordinates
        lat2, lon2: destination coordinates
        
    Returns:
        distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate Euclidean distance."""
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def logit_probability(utility: float, utilities: List[float]) -> float:
    """Calculate logit probability for a choice.
    
    Args:
        utility: utility of choice
        utilities: utilities of all alternatives
        
    Returns:
        probability between 0 and 1
    """
    utilities = np.array(utilities)
    utilities = utilities - np.max(utilities)  # scale for numerical stability
    
    try:
        numerator = np.exp(utility - np.max(utilities))
        denominator = np.sum(np.exp(utilities - np.max(utilities)))
        return float(numerator / denominator)
    except (OverflowError, ZeroDivisionError):
        return 1.0 / len(utilities)


def nested_logit_probability(
    utility: float,
    alternatives: Dict[str, List[float]],
    nesting_parameter: float = 0.8,
) -> float:
    """Calculate nested logit probability.
    
    Args:
        utility: utility of choice
        alternatives: dict of nests with utilities
        nesting_parameter: scale parameter for nest
        
    Returns:
        probability between 0 and 1
    """
    # Calculate inclusive value for nest
    nest_utilities = []
    for nest, utils in alternatives.items():
        iv = nesting_parameter * np.log(np.sum(np.exp(np.array(utils) / nesting_parameter)))
        nest_utilities.append(iv)
    
    # Logit across nests
    nest_utilities = np.array(nest_utilities) - np.max(nest_utilities)
    return float(np.exp(utility - np.max(nest_utilities)) / np.sum(np.exp(nest_utilities)))


def gravity_function(
    distance: float,
    beta: float = 0.05,
    function_type: str = "exponential"
) -> float:
    """Gravity model friction function.
    
    Args:
        distance: travel time or distance
        beta: decay parameter
        function_type: 'exponential' or 'power'
        
    Returns:
        friction factor
    """
    if function_type == "exponential":
        return np.exp(-beta * distance)
    elif function_type == "power":
        return distance ** (-beta)
    else:
        return 1.0


def bpr_cost_function(
    free_flow_time: float,
    volume: float,
    capacity: float,
    alpha: float = 0.15,
    beta: float = 4.0,
) -> float:
    """BPR (Bureau of Public Roads) cost function.
    
    Args:
        free_flow_time: time at zero volume
        volume: current volume
        capacity: link capacity
        alpha: typically 0.15
        beta: typically 4
        
    Returns:
        actual travel time
    """
    if capacity <= 0:
        return free_flow_time
    
    volume_ratio = volume / capacity
    return free_flow_time * (1 + alpha * (volume_ratio ** beta))


def conical_cost_function(
    free_flow_time: float,
    volume: float,
    capacity: float,
) -> float:
    """Conical cost function (INDY model).
    
    Args:
        free_flow_time: time at zero volume
        volume: current volume
        capacity: link capacity
        
    Returns:
        actual travel time
    """
    if capacity <= 0:
        return free_flow_time
    
    volume_ratio = min(volume / capacity, 0.99)
    return free_flow_time * (1 + 3 * volume_ratio / (1 - volume_ratio))


def calculate_vmt(speed: float, flow: float, time_interval: float) -> float:
    """Calculate vehicle miles traveled.
    
    Args:
        speed: average speed in mph
        flow: vehicle flow in vph
        time_interval: time period in hours
        
    Returns:
        VMT
    """
    return speed * flow * time_interval


def calculate_vht(flow: float, travel_time: float, time_interval: float) -> float:
    """Calculate vehicle hours traveled.
    
    Args:
        flow: vehicle flow
        travel_time: average travel time in hours
        time_interval: time period in hours
        
    Returns:
        VHT
    """
    return flow * travel_time * time_interval


def calculate_person_delay(
    vht: float,
    flow: float,
    occupancy: float = 1.5,
) -> float:
    """Calculate person hours of delay.
    
    Args:
        vht: vehicle hours traveled
        flow: vehicle flow
        occupancy: average vehicle occupancy
        
    Returns:
        person hours of delay
    """
    return vht * occupancy


def four_step_model_validation(
    trips_generated: float,
    trips_distributed: float,
    trips_assigned: float,
    tolerance: float = 0.05,
) -> Dict[str, float]:
    """Validate 4-step model consistency.
    
    Args:
        trips_generated: trips from generation
        trips_distributed: trips from distribution
        trips_assigned: trips from assignment
        tolerance: acceptable difference
        
    Returns:
        dict with validation metrics
    """
    if trips_generated == 0:
        trips_generated = 1
    
    diff_gen_dist = abs(trips_distributed - trips_generated) / trips_generated
    diff_dist_assign = abs(trips_assigned - trips_distributed) / trips_distributed
    
    return {
        "generation_to_distribution": diff_gen_dist,
        "distribution_to_assignment": diff_dist_assign,
        "valid": diff_gen_dist < tolerance and diff_dist_assign < tolerance,
    }


def accessibility_index(
    impedance_matrix: np.ndarray,
    opportunities: Dict[int, float],
    decay_parameter: float = 0.05,
) -> Dict[int, float]:
    """Calculate accessibility index.
    
    Args:
        impedance_matrix: travel time/distance matrix
        opportunities: opportunities (jobs, schools) by zone
        decay_parameter: decay parameter
        
    Returns:
        accessibility by origin zone
    """
    accessibility = {}
    n = impedance_matrix.shape[0]
    
    for i in range(n):
        access = 0
        for j in range(n):
            time = impedance_matrix[i, j]
            if not np.isinf(time):
                access += opportunities.get(j, 0) * np.exp(-decay_parameter * time)
        accessibility[i] = access
    
    return accessibility


def mode_share_calculation(
    od_trips: Dict[Tuple[int, int, str], float],
) -> Dict[str, float]:
    """Calculate mode share from OD matrix.
    
    Args:
        od_trips: dict with (origin, destination, mode) tuples
        
    Returns:
        mode share (mode -> percentage)
    """
    mode_totals = {}
    total_trips = 0
    
    for (orig, dest, mode), trips in od_trips.items():
        mode_totals[mode] = mode_totals.get(mode, 0) + trips
        total_trips += trips
    
    if total_trips == 0:
        return {}
    
    return {mode: (trips / total_trips) * 100 for mode, trips in mode_totals.items()}


def equity_analysis(
    zone_population: Dict[int, float],
    zone_accessibility: Dict[int, float],
) -> Dict[str, float]:
    """Analyze transportation equity.
    
    Args:
        zone_population: population by zone
        zone_accessibility: accessibility by zone
        
    Returns:
        equity metrics
    """
    if not zone_population:
        return {}
    
    zones = list(zone_population.keys())
    populations = np.array([zone_population.get(z, 0) for z in zones])
    accessibilities = np.array([zone_accessibility.get(z, 0) for z in zones])
    
    # Weighted average
    if np.sum(populations) > 0:
        avg_accessibility = np.sum(populations * accessibilities) / np.sum(populations)
    else:
        avg_accessibility = 0
    
    # Gini coefficient
    sorted_access = np.sort(accessibilities)
    n = len(sorted_access)
    gini = (2 * np.sum(np.arange(1, n+1) * sorted_access)) / (n * np.sum(sorted_access)) - (n + 1) / n
    
    return {
        "average_accessibility": float(avg_accessibility),
        "gini_coefficient": float(gini),
        "min_accessibility": float(np.min(accessibilities)),
        "max_accessibility": float(np.max(accessibilities)),
    }


def normalize_array(arr: np.ndarray) -> np.ndarray:
    """Normalize array to 0-1 range."""
    min_val = np.min(arr)
    max_val = np.max(arr)
    if max_val == min_val:
        return np.zeros_like(arr)
    return (arr - min_val) / (max_val - min_val)
