"""
Route utilities for the Vehicle Routing Problem.
"""

import numpy as np

def sort_nodes_by_distance(df):
    """
    Sort node keys (column labels) by distance from the depot (first row).

    Args:
        df (pd.DataFrame): Distance matrix as a DataFrame.

    Returns:
        list: List of column labels sorted by distance from the depot.
    """
    depot_row = df.iloc[0, 1:]  # Skip first column (self-distance)
    sorted_keys = depot_row.sort_values().index.tolist()
    return sorted_keys

def distribute_nodes_to_vehicles(nodes, num_vehicles):
    """
    Distribute nodes evenly among vehicles.

    Args:
        nodes: List of node indices
        num_vehicles: Number of vehicles

    Returns:
        dict: Dictionary mapping vehicle indices to lists of node indices
    """
    # Create empty lists for each vehicle
    vehicle_nodes = {i: [] for i in range(num_vehicles)}

    # Sort nodes by distance from depot (assuming nodes are already sorted)
    sorted_nodes = nodes.copy()

    # Distribute nodes in a round-robin fashion
    for i, node in enumerate(sorted_nodes):
        vehicle_id = i % num_vehicles
        vehicle_nodes[vehicle_id].append(node)

    return vehicle_nodes