"""
Controller module for the Vehicle Routing Problem.
Orchestrates the entire process of solving the VRP.
"""

import pandas as pd
from datetime import datetime
import os

from src.config import (
    DISTANCE_BASE_PENALTY,
    TOTAL_DAYS
)
from src.utils.data_utils import (
    load_matrix_df,
    load_df,
    get_demand_df,
    update_demand_dic
)
from src.utils.helper_utils import (
    get_penalty_list
)
from src.utils.route_utils import sort_nodes_by_distance
from src.utils.visualization import (
    visualize_routes_per_vehicle,
    print_route_summary,
    save_route_details_to_csv
)
from src.solver.vrp_solver import VRPSolver
from src.routes.predefined_routes import PredefinedRouteManager

class VRPController:
    """Controller class for the Vehicle Routing Problem."""

    def __init__(self):
        self.base_penalty = DISTANCE_BASE_PENALTY
        self.demand_df = None
        self.master_mat_df = None
        self.master_gps_df = None
        self.demand_dict = None
        self.penalty_list = None

        import src.config as config
        self.max_visits = config.MAX_VISITS_PER_VEHICLE
        self.max_distance = config.MAX_DISTANCE_PER_VEHICLE

        self.route_manager = PredefinedRouteManager()
        self.vehicle_routes = {}

    def load_data(self, demand_path, matrix_path, gps_path):
        self.demand_df = get_demand_df(today_path=demand_path)

        if self.demand_df['CODE'].dtype in ['float', 'int', 'int64']:
            self.demand_df['CODE'] = self.demand_df['CODE'].astype(int).astype(str)
            print('Converting CODE to string')

        self.master_mat_df = load_matrix_df(path=matrix_path)
        self.master_gps_df = load_df(path=gps_path)

        SMAK_KADAWATHA = (7.0038321, 79.9394804)
        smak_data = {
            "CODE": '0',
            "LOCATION": "SMAK",
            "ADDRESS": "Smak, Kadawatha, Western Province, Sri Lanka",
            "LATITUDE": SMAK_KADAWATHA[0],
            "LONGITUDE": SMAK_KADAWATHA[1]
        }

        if '0' in self.master_gps_df['CODE'].values:
            self.master_gps_df = self.master_gps_df[self.master_gps_df['CODE'] != '0']

        self.master_gps_df = pd.concat([
            pd.DataFrame([smak_data]),
            self.master_gps_df
        ], ignore_index=True)
        print("Added depot (SMAK_KADAWATHA) to GPS data")

        self.demand_dict = update_demand_dic(self.demand_df)
        today = datetime.now().strftime('%Y-%m-%d')
        self.penalty_list = get_penalty_list(self.demand_dict, self.base_penalty, TOTAL_DAYS, today)

        print(f"Loaded {len(self.demand_df)} demand records")
        print(f"Loaded {len(self.master_mat_df)} locations in distance/time matrix")
        print(f"Loaded {len(self.master_gps_df)} locations with GPS coordinates")

    def solve_single_day(self, day=0, max_nodes=None, save_visualization=False, output_folder=None):
        if self.demand_df is None or self.master_mat_df is None or self.master_gps_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        all_nodes = list(range(1, len(self.master_mat_df)))
        sorted_nodes = sort_nodes_by_distance(self.master_mat_df.values)

        nodes_to_visit = sorted(sorted_nodes[:max_nodes]) if max_nodes and max_nodes < len(sorted_nodes) else all_nodes

        used_vehicles = set()
        route_dict = {}
        visited_nodes = set()
        
        solver = VRPSolver(use_distance=self.use_distance)

        for vehicle_id, route_id in self.vehicle_routes.items():
            try:
                vehicle_id_int = int(vehicle_id)
                used_vehicles.add(vehicle_id_int)
                route_data = self.route_manager.get_route(route_id)

                shop_codes = [code for code in route_data.get('shop_codes', []) if code in self.demand_dict['key']]
                if not shop_codes:
                    continue

                sub_solver = solver.solve_day(
                    full_matrix=self.master_mat_df,
                    nodes_to_visit=shop_codes,
                    day=day,
                    demand_dict=self.demand_dict,
                    penalty_list=self.penalty_list,
                    max_distance=[self.max_distance[vehicle_id_int]],
                    max_visits=[self.max_visits[vehicle_id_int]]
                )

                sub_visited, sub_routes = sub_solver.solve()
                if 0 in sub_routes:
                    route_dict[vehicle_id_int] = sub_routes[0]
                    visited_nodes.update(sub_visited)
            except Exception as e:
                print(f"VRP failed for predefined route {route_id}: {e}")

        remaining_nodes = [n for n in nodes_to_visit if str(n) not in visited_nodes]
        available_vehicles = [i for i in range(len(self.max_visits)) if i not in used_vehicles]

        if remaining_nodes and available_vehicles:
            rem_solver = solver.solve_day(
                full_matrix=self.master_mat_df,
                nodes_to_visit=remaining_nodes,
                day=day,
                demand_dict=self.demand_dict,
                penalty_list=self.penalty_list,
                max_distance=[self.max_distance[i] for i in available_vehicles],
                max_visits=[self.max_visits[i] for i in available_vehicles]
            )
            rem_visited, rem_routes = rem_solver.solve()
            visited_nodes.update(rem_visited)
            for idx, veh_id in enumerate(available_vehicles):
                if idx in rem_routes:
                    route_dict[veh_id] = rem_routes[idx]

        if output_folder:
            os.makedirs(os.path.join(output_folder, 'summaries'), exist_ok=True)
            os.makedirs(os.path.join(output_folder, 'csv'), exist_ok=True)
            os.makedirs(os.path.join(output_folder, 'maps'), exist_ok=True)

            print_route_summary(route_dict, self.use_distance, file_path=os.path.join(output_folder, 'summaries', f"day_{day + 1}_summary.txt"))
            save_route_details_to_csv(route_dict, day, self.use_distance, file_path=os.path.join(output_folder, 'csv', f"day_{day + 1}_routes.csv"))

            if save_visualization:
                maps_dict = visualize_routes_per_vehicle(self.master_gps_df, route_dict, day, use_distance=self.use_distance)
                for vehicle_id, m in maps_dict.items():
                    m.save(os.path.join(output_folder, 'maps', f"day_{day + 1}_vehicle_{vehicle_id}_route.html"))
        else:
            self._create_output_directories()
            print_route_summary(route_dict, self.use_distance, file_path=f"output/summaries/day_{day + 1}_summary.txt")
            save_route_details_to_csv(route_dict, day, self.use_distance, file_path=f"output/csv/day_{day + 1}_routes.csv")

            if save_visualization:
                maps_dict = visualize_routes_per_vehicle(self.master_gps_df, route_dict, day, use_distance=self.use_distance)
                for vehicle_id, m in maps_dict.items():
                    m.save(f"output/maps/day_{day + 1}_vehicle_{vehicle_id}_route.html")

        return visited_nodes, route_dict

    def _create_output_directories(self):
        os.makedirs("output", exist_ok=True)
        os.makedirs("output/summaries", exist_ok=True)
        os.makedirs("output/csv", exist_ok=True)
        os.makedirs("output/maps", exist_ok=True)

    def get_po_node_indices(self):
        return set(str(code) for code in self.demand_dict['key'] if code in self.master_mat_df.index)

    def _save_unvisited_nodes_to_csv(self, unvisited, output_file=None):
        unvisited_codes = list(unvisited)
        if not unvisited_codes:
            print("No unvisited nodes to save for next day.")
            return

        unvisited_codes_set = set(str(code) for code in unvisited_codes)
        next_day_df = self.demand_df[self.demand_df['CODE'].astype(str).isin(unvisited_codes_set)].copy()

        if next_day_df.empty:
            next_day_df = pd.DataFrame({'CODE': unvisited_codes})

        if 'DEMAND' in next_day_df.columns:
            next_day_df.drop(columns=['DEMAND'], inplace=True)

        if output_file is None:
            os.makedirs("output/csv", exist_ok=True)
            output_file = "output/csv/next_day_demand.csv"

        next_day_df.to_csv(output_file, index=False)
        print(f"Saved {len(next_day_df)} unvisited nodes to {output_file} for next-day processing.")

    def update_vehicle_config(self, num_vehicles, max_visits, max_distance, vehicle_routes=None):
        if len(max_visits) != num_vehicles or len(max_distance) != num_vehicles:
            raise ValueError("Length of max_visits and max_distance must match num_vehicles")

        self.max_visits = max_visits.copy()
        self.max_distance = max_distance.copy()

        if vehicle_routes:
            normalized_routes = {}
            for vehicle_id, route_id in vehicle_routes.items():
                try:
                    vehicle_id_int = int(vehicle_id)
                    normalized_routes[vehicle_id_int] = route_id
                except (ValueError, TypeError):
                    print(f"Warning: Invalid vehicle ID {vehicle_id} in vehicle_routes. Skipping.")
            self.vehicle_routes = normalized_routes

        import src.config as config
        config.MAX_VISITS_PER_VEHICLE = self.max_visits
        config.MAX_DISTANCE_PER_VEHICLE = self.max_distance
        print('update_vehicle_config')

    def get_predefined_routes(self):
        return self.route_manager.get_all_routes()

    def assign_route_to_vehicle(self, vehicle_id, route_id):
        try:
            vehicle_id_int = int(vehicle_id)
            if route_id:
                self.vehicle_routes[vehicle_id_int] = route_id
            elif vehicle_id_int in self.vehicle_routes:
                del self.vehicle_routes[vehicle_id_int]
        except (ValueError, TypeError):
            print(f"Warning: Invalid vehicle ID {vehicle_id}. Cannot assign route.")

    def get_vehicle_route(self, vehicle_id):
        try:
            vehicle_id_int = int(vehicle_id)
            route_id = self.vehicle_routes.get(vehicle_id_int)
            return self.route_manager.get_route(route_id) if route_id else None
        except (ValueError, TypeError):
            print(f"Warning: Invalid vehicle ID {vehicle_id}. Cannot get route.")
            return None
