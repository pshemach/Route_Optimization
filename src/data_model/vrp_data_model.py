"""
Data model for the Vehicle Routing Problem.
Creates the data model for the solver based on the input data.
"""
import src.config as config

class VRPDataModel:
    def __init__(self, full_matrix, nodes_to_visit, demand_dict,
                 penalty_list=None, max_distance=None, max_visits=None):
        
        if max_distance is None:
            max_distance = config.MAX_DISTANCE_PER_VEHICLE
        if max_visits is None:
            max_visits = config.MAX_VISITS_PER_VEHICLE

        self.full_matrix = full_matrix  # A Pandas DataFrame with labeled rows/columns
        self.nodes_to_visit = nodes_to_visit  # List of keys/labels, e.g., [1005, 1017, ...]
        self.demand_dict = demand_dict  # Dict keyed by node labels
        self.penalty_list = penalty_list
        self.max_distance = max_distance
        self.max_visits = max_visits

        self.data = {}
        self._create_model()

    def _create_model(self):
        print("create_data_model called with:")
        print(f"max_distance: {self.max_distance}")
        print(f"max_visits: {self.max_visits}")
        print(f"Distance Matrix Shape: {self.full_matrix.shape}")
        print(f"Length of nodes_to_visit: {len(self.nodes_to_visit)}")

        # Get valid keys that are present in both index and columns
        valid_keys = set(self.full_matrix.index).intersection(self.full_matrix.columns)

        # Filter nodes_to_visit to only valid ones
        filtered_nodes = [node for node in self.nodes_to_visit if node in valid_keys]

        # Ensure depot (assumed to be the first row/column label)
        depot = self.full_matrix.index[0]
        all_nodes = [depot] + filtered_nodes

        # Build distance matrix using safe access
        self.data["distance_matrix"] = [
            [self.full_matrix.loc[from_node, to_node] for to_node in all_nodes]
            for from_node in all_nodes
        ]
        

        # Demands: depot = 0, others use demand_dict.get() fallback = 1
        self.data["demands"] = [0] + [self.demand_dict.get(node, 1) for node in filtered_nodes]

        self.data["node_mapping"] = all_nodes
        self.data["num_vehicles"] = len(self.max_distance)
        self.data["depot"] = 0
        self.data["max_distance_per_vehicle"] = self.max_distance
        self.data["max_visits_per_vehicle"] = self.max_visits

        if self.penalty_list is not None:
            self.data["penalties"] = [0] + [
                penalty for node, penalty in zip(self.nodes_to_visit, self.penalty_list)
                if node in filtered_nodes
            ]
        else:
            self.data["penalties"] = [0] + [1000] * len(filtered_nodes)


    def get_data(self):
        return self.data