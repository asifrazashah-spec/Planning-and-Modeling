"""Example: Basic Transportation Planning Scenario"""

from src.network.builder import NetworkBuilder
from src.core.models import Zone
from src.core.enums import TransportMode, LinkType, NodeType
from src.demand.model import DemandModel
from src.assignment.user_equilibrium import UserEquilibriumAssignment
from src.analytics.performance import PerformanceAnalysis
from src.analytics.reporting import ReportGenerator


def create_simple_network():
    """Create a simple 3-zone network."""
    builder = NetworkBuilder(network_name="Simple Network")

    # Add zones
    builder.add_zone(1, "Downtown", 0, 0, 100, population=50000, employment=40000)
    builder.add_zone(2, "Midtown", 5, 5, 100, population=30000, employment=25000)
    builder.add_zone(3, "Suburbs", 10, 0, 100, population=20000, employment=5000)

    # Add nodes (centroids and intersections)
    builder.add_node(1, 0, 0, NodeType.CENTROID, zone_id=1)
    builder.add_node(2, 5, 5, NodeType.CENTROID, zone_id=2)
    builder.add_node(3, 10, 0, NodeType.CENTROID, zone_id=3)

    # Add links with different types
    builder.add_link(
        link_id=1,
        from_node_id=1,
        to_node_id=2,
        link_type=LinkType.ARTERIAL,
        length=5.0,
        modes=[TransportMode.CAR, TransportMode.BUS],
        capacity=1000,
        free_flow_time=15.0,
        lanes=2,
    )

    builder.add_link(
        link_id=2,
        from_node_id=2,
        to_node_id=3,
        link_type=LinkType.ARTERIAL,
        length=5.0,
        modes=[TransportMode.CAR, TransportMode.BUS],
        capacity=900,
        free_flow_time=15.0,
        lanes=2,
    )

    builder.add_link(
        link_id=3,
        from_node_id=1,
        to_node_id=3,
        link_type=LinkType.FREEWAY,
        length=10.0,
        modes=[TransportMode.CAR],
        capacity=2000,
        free_flow_time=12.0,
        lanes=4,
    )

    return builder.build()


def run_demand_model(network):
    """Run demand model on network."""
    demand = DemandModel(
        zones=network.zones,
        time_periods=["AM"],
        modes=[TransportMode.CAR, TransportMode.BUS],
    )

    # Define trip rates
    trip_rates = {
        "work": 0.3,
        "school": 0.1,
        "other": 0.2,
    }

    attraction_rates = {
        "work": 0.8,
        "school": 0.15,
        "other": 0.3,
    }

    # Get impedance matrix (travel times)
    impedance_matrix = network.get_connectivity_matrix()

    # Simple mode costs
    mode_costs = {
        "car": impedance_matrix.copy(),
        "bus": {k: v * 1.5 for k, v in impedance_matrix.items()},
    }

    # Run model
    od_trips = demand.run_full_model(trip_rates, attraction_rates, impedance_matrix, mode_costs)

    return od_trips


def run_assignment(network, od_trips):
    """Run network assignment."""
    # Extract car trips for assignment
    car_od_matrix = {}
    for key, od in od_trips.items():
        if od.mode == TransportMode.CAR:
            car_od_matrix[(od.origin.id, od.destination.id)] = od_trips[key].trips

    # Run UE assignment
    assignment = UserEquilibriumAssignment(network, car_od_matrix)
    result = assignment.solve(max_iterations=50)

    return result


def analyze_results(network, assignment):
    """Analyze and report results."""
    analysis = PerformanceAnalysis(network, assignment)
    metrics = analysis.get_performance_metrics()

    print("\n=== Transportation Planning Results ===\n")
    print(f"Total VMT: {metrics['vmt']:.0f}")
    print(f"Total VHT: {metrics['vht']:.0f}")
    print(f"Average Speed: {metrics['average_speed']:.2f} mph")
    print(f"Congestion Hours: {metrics['congestion_hours']:.0f}")
    print(f"Convergence Achieved: {metrics['convergence_achieved']}")

    # Generate report
    reporter = ReportGenerator()
    report_path = reporter.generate_summary_report("example_scenario", {"performance": metrics})
    print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    print("Transportation Planning Example")
    print("=" * 40)

    # Create network
    print("\n1. Creating network...")
    network = create_simple_network()
    print(f"   - Created network with {len(network.zones)} zones and {len(network.links)} links")

    # Run demand model
    print("\n2. Running demand model...")
    od_trips = run_demand_model(network)
    print(f"   - Generated OD matrix with {len(od_trips)} entries")

    # Run assignment
    print("\n3. Running network assignment...")
    assignment = run_assignment(network, od_trips)
    print(f"   - Completed in {assignment.iterations} iterations")
    print(f"   - Convergence gap: {assignment.convergence_gap:.6f}")

    # Analyze results
    print("\n4. Analyzing results...")
    analyze_results(network, assignment)

    print("\n" + "=" * 40)
    print("Example completed successfully!")
