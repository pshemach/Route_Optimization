"""
Data model for the Vehicle Routing Problem.
Creates the data model for the solver based on the input data.
"""

import src.config as config

class VRPDataModel:
    def __init__(self, full_matrix, nodes_to_visit, demand_dict,
                 penalty_list=None, max_distance=None, max_visits=None, depot_code='0'):
        
        if max_distance is None:
            max_distance = config.MAX_DISTANCE_PER_VEHICLE
        if max_visits is None:
            max_visits = config.MAX_VISITS_PER_VEHICLE

        self.full_matrix = full_matrix  # Pandas DataFrame with named rows/columns
        self.nodes_to_visit = nodes_to_visit  # e.g., [1005, 1017, ...]
        self.demand_dict = demand_dict  # Dict: {shop_code: demand}
        self.penalty_list = penalty_list
        self.max_distance = max_distance
        self.max_visits = max_visits
        self.depot_code = depot_code  # Custom depot code, e.g., 'SMAK'

        self.data = {}
        self._create_model()

    def _create_model(self):
        print("create_data_model called with:")
        print(f"Depot: {self.depot_code}")
        print(f"Max Distance: {self.max_distance}")
        print(f"Max Visits: {self.max_visits}")
        print(f"Distance Matrix Shape: {self.full_matrix.shape}")
        print(f"Nodes to Visit: {len(self.nodes_to_visit)}")

        # Validate that depot exists
        valid_keys = set(self.full_matrix.index).intersection(self.full_matrix.columns)
        assert self.depot_code in valid_keys, f"Depot '{self.depot_code}' not found in distance matrix."

        # Filter out invalid nodes and exclude depot from visit list
        filtered_nodes = [node for node in self.nodes_to_visit if node in valid_keys and node != self.depot_code]

        # Build node list (depot always at index 0)
        all_nodes = [self.depot_code] + filtered_nodes

        # Build distance matrix
        self.data["distance_matrix"] = [
            [self.full_matrix.loc[from_node, to_node] for to_node in all_nodes]
            for from_node in all_nodes
        ]

        # Build demand list
        self.data["demands"] = [0] + [self.demand_dict.get(node, 1) for node in filtered_nodes]

        # Set other model fields
        self.data["node_mapping"] = all_nodes
        self.data["num_vehicles"] = len(self.max_distance)
        self.data["depot"] = 0
        self.data["max_distance_per_vehicle"] = self.max_distance
        self.data["max_visits_per_vehicle"] = self.max_visits

        # Build penalty list (optional)
        if self.penalty_list is not None:
            filtered_penalties = [
                penalty for node, penalty in zip(self.nodes_to_visit, self.penalty_list)
                if node in filtered_nodes
            ]
            self.data["penalties"] = [0] + filtered_penalties
        else:
            self.data["penalties"] = [0] + [1000] * len(filtered_nodes)

    def get_data(self):
        return self.data
