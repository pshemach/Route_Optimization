"""
Data model for the Vehicle Routing Problem.
Creates the data model for the solver based on the input data.
"""
import src.config as config

class VRPDataModel:
    def __init__(self, full_matrix, nodes_to_visit, demand_dict,
                 penalty_list=None,max_distance=None, max_visits=None):
        
        if max_distance is None:
            max_distance = config.MAX_DISTANCE_PER_VEHICLE
        if max_visits is None:
            max_visits = config.MAX_VISITS_PER_VEHICLE

        self.full_matrix = full_matrix
        self.nodes_to_visit = nodes_to_visit
        self.demand_dict = demand_dict
        self.penalty_list = penalty_list
        self.max_distance = max_distance
        self.max_visits = max_visits
        

        self.data = {}
        self._create_model()

    def _create_model(self):
        print(f"create_data_model called with:")
        print(f"max_distance: {self.max_distance}")
        print(f"max_visits: {self.max_visits}")

        node_indices = [0] + [i for i, code in enumerate(self.full_matrix.index) if code in self.demand_dict['key']]
        nodes_to_use = [node_indices[0]] + [i for i in node_indices[1:] if i in self.nodes_to_visit]

        self.data["num_vehicles"] = len(self.max_distance)
        self.data["depot"] = 0

        self.data["distance_matrix"] = [[self.full_matrix.iloc[i][j] for j in nodes_to_use] for i in nodes_to_use]
        self.data["max_distance_per_vehicle"] = self.max_distance

        self.data["demands"] = [0] + [self.demand_dict.get(self.full_matrix.index[i], 1) for i in nodes_to_use[1:]]
        self.data["node_mapping"] = [self.full_matrix.index[i] for i in nodes_to_use]
        self.data["max_visits_per_vehicle"] = self.max_visits

        if self.penalty_list is not None:
            self.data["penalties"] = [0] + self.penalty_list
        else:
            self.data["penalties"] = [0] + [1000] * len(nodes_to_use[1:])

    def get_data(self):
        return self.data