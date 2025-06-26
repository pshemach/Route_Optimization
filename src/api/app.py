# src/api/app.py
from flask import Flask, request, jsonify, send_from_directory
from src.controller.controller import VRPController, RouteMapManager
from src.routes.predefined_routes import PredefinedRouteManager
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../templates"))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
route_manager = PredefinedRouteManager()

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/api/routes', methods=['GET'])
def list_routes():
    return jsonify(route_manager.get_all_routes()), 200

@app.route('/api/routes', methods=['POST'])
def create_route():
    data = request.json
    if not data or 'route_name' not in data or 'shop_codes' not in data:
        return jsonify({"error": "route_name & shop_codes required"}), 400
    route_id = route_manager.create_route(
        data['route_name'], data['shop_codes'], data.get('description', "")
    )
    return jsonify({route_id: route_manager.get_route(route_id)}), 201

@app.route('/api/routes/<route_id>', methods=['PUT'])
def update_route(route_id):
    data = request.json
    route = route_manager.get_route(route_id)
    if not route:
        return jsonify({"error": "Route not found"}), 404
    updated = route_manager.save_route(route_id, {
        "name": data.get('route_name', route['name']),
        "shop_codes": data.get('shop_codes', route['shop_codes']),
        "description": data.get('description', route.get('description', "")),
        "created_at": route.get('created_at')
    })
    return jsonify(route_manager.get_route(route_id)), 200

@app.route('/api/routes/<route_id>', methods=['DELETE'])
def delete_route(route_id):
    if route_manager.delete_route(route_id):
        return jsonify({"message": "Route deleted"}), 200
    return jsonify({"error": "Route not found"}), 404

@app.route('/api/upload-solve', methods=['POST'])
def upload_and_solve():
    try:
        demand_file = request.files.get('demand_csv')
        matrix_path = request.form.get('matrix_path')
        gps_path = request.form.get('gps_path')
        today = request.form.get('today')
        num_v = int(request.form.get('num_vehicles'))
        max_visits = list(map(int, request.form.getlist('max_visits')))
        max_dist = list(map(int, request.form.getlist('max_distance')))
        pred_id = request.form.get('predefined_route_id') or None

        if not demand_file:
            return jsonify({"error": "Missing demand_csv"}), 400

        os.makedirs("uploads", exist_ok=True)
        dp = os.path.join("uploads", demand_file.filename)
        demand_file.save(dp)

        ctr = VRPController()
        ctr.load_inputs(dp, matrix_path, gps_path, 1000, 1, today, depot_code='0')
        ctr.configure_vehicles(num_v, max_visits, max_dist,
                               vehicle_routes={0: pred_id} if pred_id else {})
        visited, routes = ctr.solve_single_day()

        mgr = RouteMapManager(ctr.master_gps_df, ctr.demand_df, output_dir="frontend/maps")
        mgr.generate_and_save_maps(routes, 0)
        mgr.summarize_and_save(routes, 0)

        return jsonify({"status": "ok", "visited": list(visited), "routes": routes}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    os.makedirs("frontend/maps", exist_ok=True)
    app.run(host="0.0.0.0", port=5096, debug=True)
