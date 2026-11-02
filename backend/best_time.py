import json
import azure.functions as func

bp = func.Blueprint(http_auth_level=func.AuthLevel.ANONYMOUS)

# Mock average crowd % for each hour (24-hour clock).
# Store ids match the stores endpoint ("1" = Target, "2" = Best Buy, "3" = Walmart).
# Later this will be calculated from crowd history in Cosmos DB.
CROWD_HISTORY = {
    "1": {9: 25, 10: 35, 11: 50, 12: 70, 13: 82, 14: 75, 15: 60,
          16: 55, 17: 78, 18: 85, 19: 65, 20: 40, 21: 30},
    "2": {10: 20, 11: 30, 12: 55, 13: 65, 14: 70, 15: 60, 16: 50,
          17: 45, 18: 55, 19: 40, 20: 25},
    "3": {8: 30, 9: 35, 10: 45, 11: 55, 12: 65, 13: 60, 14: 50,
          15: 45, 16: 55, 17: 70, 18: 75, 19: 60, 20: 45, 21: 35, 22: 20},
}


def format_hour(hour):
    """Turn 13 into '1:00 PM'."""
    suffix = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    return f"{hour_12}:00 {suffix}"


def find_quietest_times(history, count=3):
    """Return the hours with the lowest average crowd."""
    sorted_hours = sorted(history.items(), key=lambda item: item[1])
    return [
        {"time": format_hour(hour), "avgOccupancyPercent": percent}
        for hour, percent in sorted_hours[:count]
    ]


@bp.route(route="best-time", methods=["GET"])
def best_time(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/best-time?id=1"""
    store_id = req.params.get("id")

    if not store_id:
        return func.HttpResponse(
            json.dumps({"error": "Please provide a store id, like ?id=1"}),
            status_code=400,
            mimetype="application/json",
        )

    history = CROWD_HISTORY.get(store_id)
    if history is None:
        return func.HttpResponse(
            json.dumps({"error": "No crowd history for this store"}),
            status_code=404,
            mimetype="application/json",
        )

    quietest = find_quietest_times(history)
    result = {
        "storeId": store_id,
        "bestTime": quietest[0]["time"],
        "quietestTimes": quietest,
    }
    return func.HttpResponse(json.dumps(result), mimetype="application/json")