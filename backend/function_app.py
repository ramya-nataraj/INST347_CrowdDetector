import json
import azure.functions as func
from best_time import bp as best_time_bp  # Daanial: import best-time endpoint

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
app.register_functions(best_time_bp)  # Daanial: register best-time endpoint

stores = [
    {"id": "1", "name": "Target", "location": "College Park, MD", "max_capacity": 300, "current_count": 246, "crowd_level": "large"},
    {"id": "2", "name": "Best Buy", "location": "Greenbelt, MD", "max_capacity": 200, "current_count": 60, "crowd_level": "small"},
    {"id": "3", "name": "Walmart", "location": "Laurel, MD", "max_capacity": 400, "current_count": 210, "crowd_level": "average"},
]

@app.route(route="stores")
def get_stores(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name")
    results = stores
    if name:
        results = [s for s in stores if name.lower() in s["name"].lower()]

    for s in results:
        s["occupancy_percent"] = round(s["current_count"] / s["max_capacity"] * 100)

    return func.HttpResponse(json.dumps(results), mimetype="application/json")