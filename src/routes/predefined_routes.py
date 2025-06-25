"""
Module for managing pre-defined routes.
Provides functionality to create, load, and save pre-defined routes.
"""

import os
import json
import pandas as pd

class PredefinedRouteManager:
    """
    Manages all pre-defined routes stored in a single JSON file.
    Routes are stored as a dictionary with stringified route IDs as keys.
    """

    def __init__(self, file_path="data/routes/all_routes.json"):
        self.file_path = file_path
        self.routes = {}
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        self._load_routes()

    def _load_routes(self):
        """
        Load all routes from a single JSON file.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.routes = json.load(f)
            except Exception as e:
                print(f"Error loading routes: {e}")
                self.routes = {}
        else:
            self.routes = {}

    def _save_routes(self):
        """
        Save all routes to a single JSON file.
        """
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.routes, f, indent=2)
        except Exception as e:
            print(f"Error saving routes: {e}")

    def get_all_routes(self):
        """
        Return all routes as a dictionary.
        """
        return self.routes

    def get_route(self, route_id):
        """
        Retrieve a specific route using its ID (int or str).
        """
        return self.routes.get(str(route_id))

    def save_route(self, route_id, route_data):
        """
        Add or update a route with the given route ID.
        """
        self.routes[str(route_id)] = route_data
        self._save_routes()

    def delete_route(self, route_id):
        """
        Remove a route by its ID.
        """
        route_id = str(route_id)
        if route_id in self.routes:
            del self.routes[route_id]
            self._save_routes()
            return True
        return False

    def create_route_from_codes(self, route_id, route_name, shop_codes, description=""):
        """
        Create and save a new route from shop codes.

        Args:
            route_id (int or str): Unique numeric ID for the route.
            route_name (str): Human-readable route name.
            shop_codes (list or str): List of shop codes or comma-separated string.
            description (str): Optional description for the route.

        Returns:
            str: The route ID (as string) used to store the route.
        """
        processed_codes = []

        if isinstance(shop_codes, str):
            codes_str = shop_codes.replace(',', '\n')
            codes = [code.strip() for code in codes_str.split('\n') if code.strip()]
            processed_codes.extend(codes)
        elif isinstance(shop_codes, list):
            for item in shop_codes:
                if isinstance(item, str) and ('\n' in item or '\r\n' in item):
                    item_str = item.replace(',', '\n')
                    codes = [code.strip() for code in item_str.split('\n') if code.strip()]
                    processed_codes.extend(codes)
                else:
                    processed_codes.append(str(item).strip())

        route_data = {
            "name": route_name,
            "description": description,
            "shop_codes": processed_codes,
            "created_at": pd.Timestamp.now().isoformat()
        }

        self.save_route(route_id, route_data)
        return str(route_id)
