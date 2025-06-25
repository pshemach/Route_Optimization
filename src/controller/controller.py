"""
Controller for solving the Vehicle Routing Problem using modular classes.
"""
import os
from src.data_model.vrp_data_model import VRPDataModel
from src.solver.vrp_solver import VRPSolver
from src.routes.predefined_routes import PredefinedRouteManager
from src.utils.data_utils import (get_demand_df, update_demand_dic, load_matrix_df, get_demand_matrix_df, load_df)
from src.utils.helper_utils import get_penalty_list
from src.utils.visualization import (load_route_cache,save_route_cache,visualize_routes_per_vehicle,print_route_summary,save_route_details_to_csv)

class VRPController:
    def __init__(self):
        self.route_manager = PredefinedRouteManager()
        self.data_model = None
        self.vehicle_routes = {}
        self.max_visits = []
        self.max_distance = []

    def load_inputs(self, demand_path, matrix_path, gps_path, base_penalty, total_days, today):
        # Load all input files
        self.demand_df = get_demand_df(today_path=demand_path)
        self.matrix_df = load_matrix_df(matrix_path)
        self.master_gps_df = load_df(path=gps_path)

        # Compute demand dictionary and penalty list
        self.demand_dict = update_demand_dic(self.demand_df)
        self.demand_mat_df = get_demand_matrix_df(self.matrix_df,self.demand_df, 0)
        self.penalty_list = get_penalty_list(self.demand_dict, base_penalty, total_days, today)

    def configure_vehicles(self, num_vehicles, max_visits, max_distance, vehicle_routes=None):
        self.max_visits = max_visits
        self.max_distance = max_distance
        self.vehicle_routes = {int(k): v for k, v in (vehicle_routes or {}).items()}

    def solve_single_day(self):
        used_vehicle_ids = set()
        visited_node_codes = set()
        route_dict = {}

        # === Handle Pre-defined Routes ===
        for vehicle_id, route_id in self.vehicle_routes.items():
            used_vehicle_ids.add(vehicle_id)
            route = self.route_manager.get_route(route_id)
            shop_codes = [code for code in route['shop_codes'] if code in self.demand_dict['key']]
            print(f'shop codes len:{len(shop_codes)}')
            
            if not shop_codes:
                continue
            
            model = VRPDataModel(
                full_matrix=self.matrix_df,
                nodes_to_visit=shop_codes,
                demand_dict=self.demand_dict,
                max_distance=[self.max_distance[vehicle_id]],
                max_visits=[self.max_visits[vehicle_id]],
                penalty_list=[1000] * len(shop_codes)  # Or specific penalties
            )
            data = model.get_data()
            solver = VRPSolver()
            visited, routes = solver.solve_day(data,1)
            print(routes)

            if 0 in routes:
                route_dict[vehicle_id] = routes[0]
                visited_node_codes.update(visited)

        # === Handle Remaining Nodes ===
        all_demand_codes = set(self.demand_dict['key'])
        remaining_codes = all_demand_codes - visited_node_codes

        available_vehicle_ids = [
            vid for vid in range(len(self.max_visits)) if vid not in used_vehicle_ids
        ]

        if remaining_codes and available_vehicle_ids:
            model = VRPDataModel(
                full_matrix=self.matrix_df,
                nodes_to_visit=list(remaining_codes),
                demand_dict=self.demand_dict,
                max_distance=[self.max_distance[i] for i in available_vehicle_ids],
                max_visits=[self.max_visits[i] for i in available_vehicle_ids],
                penalty_list=[self.penalty_list[i] for i in range(len(self.penalty_list)) if self.demand_dict['key'][i] in remaining_codes]
            )
            data = model.get_data()
            solver = VRPSolver()
            visited, routes = solver.solve_day(data,1)

            for i, vehicle_id in enumerate(available_vehicle_ids):
                if i in routes:
                    route_dict[vehicle_id] = routes[i]
                    visited_node_codes.update(visited)

        return visited_node_codes, route_dict
    
    
class RouteMapManager:
    def __init__(self, gps_df, demand_df, output_dir="output"):
        self.gps_df = gps_df
        self.demand_df = demand_df
        self.output_dir = output_dir
        self.use_distance = True
        os.makedirs(f"{output_dir}/maps", exist_ok=True)
        os.makedirs(f"{output_dir}/csv", exist_ok=True)
        load_route_cache()

    def generate_and_save_maps(self, route_dict, day):
        maps = visualize_routes_per_vehicle(
            master_df=self.gps_df,
            route_dict=route_dict,
            day=day,
            use_distance=self.use_distance
        )
        for vehicle_id, fmap in maps.items():
            fmap.save(f"{self.output_dir}/maps/day_{day + 1}_vehicle_{vehicle_id}.html")
        save_route_cache()
        return maps

    def summarize_and_save(self, route_dict, day):
        print_route_summary(route_dict, use_distance=self.use_distance)
        save_route_details_to_csv(
            demand_df=self.demand_df,
            route_dict=route_dict,
            day=day,
            use_distance=self.use_distance,
            file_path=f"{self.output_dir}/csv/day_{day + 1}_summary.csv"
        )