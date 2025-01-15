from flask import Flask, render_template, request
import itertools
from googlemaps import Client as GoogleMapsClient
from datetime import datetime, timedelta

# Flaskアプリ設定
app = Flask(__name__)

# Google Maps APIキー
#API_KEY = "" ここは本来はapi key
gmaps = GoogleMapsClient(key=API_KEY)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 出発時刻、現在地、子供の情報を取得
        departure_time = request.form.get("departure_time")
        current_location = request.form.get("current_location")
        num_children = int(request.form.get("num_children"))
        
        # 子供情報を取得
        children_info = []
        for i in range(1, num_children + 1):
            name = request.form.get(f"child_name_{i}")
            address = request.form.get(f"child_address_{i}")
            time = request.form.get(f"child_time_{i}")
            children_info.append({"name": name, "address": address, "time": time})

        # 出発時刻を datetime オブジェクトに変換
        departure_time_obj = datetime.strptime(departure_time, "%H:%M")

        # 全順列を計算
        addresses = [child["address"] for child in children_info]
        routes = list(itertools.permutations(addresses))

        # 各経路の移動時間を取得
        route_details = []
        for route in routes:
            waypoints = [current_location] + list(route)
            distance, duration, times = calculate_route(waypoints, departure_time_obj)
            route_details.append({
                "route": " → ".join([f"子供{children_info[i]['name']}({route[i]})" for i in range(len(route))]),
                "distance": distance,
                "duration": duration,
                "times": times
            })

        # 結果をレンダリング
        return render_template("result.html", route_details=route_details)

    return render_template("index.html")

def calculate_route(waypoints, departure_time_obj):
    """
    Google Maps APIを使ってルートの距離と時間を計算。
    """
    try:
        response = gmaps.directions(waypoints[0], waypoints[-1], waypoints=waypoints[1:-1])
        legs = response[0]["legs"]
        total_distance = sum(leg["distance"]["value"] for leg in legs) / 1000  # 距離（km）
        total_duration = sum(leg["duration"]["value"] for leg in legs) / 60  # 時間（分）
        
        # 各地点への到着時刻を計算
        times = []
        current_time = departure_time_obj
        for i in range(len(waypoints)):
            if i > 0:  # 最初の出発地点は除く
                current_time += timedelta(minutes=legs[i-1]["duration"]["value"] / 60)
            times.append(current_time.strftime("%H:%M"))

        return f"{total_distance:.2f} km", f"{total_duration:.2f} min", times
    except Exception as e:
        return "Error", "Error", []

if __name__ == "__main__":
    app.run(debug=True)

