"""
Real Time Taxi Comparer - Taxi Fare Comparison App
Converted from React/TypeScript to Python (Flask)
Run with: pip install flask && python app.py
"""

from flask import Flask, render_template_string, jsonify, request
import socket
from datetime import datetime
import json
import math
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

app = Flask(__name__)

# ── Data ────────────────────────────────────────────────────────────────────

RIDE_DATA = [
    {"id": 1, "name": "Rapido",       "price": 158, "eta": "3 min", "vehicle": "Bike",    "surge": False, "savings": 82, "badge": "cheapest", "logo": "🏍️", "gradient": "yellow-orange"},
    {"id": 2, "name": "Namma Yatri",  "price": 175, "eta": "5 min", "vehicle": "Auto",    "surge": False, "savings": 65, "badge": None,        "logo": "🛺",  "gradient": "green-emerald"},
    {"id": 3, "name": "Ola",          "price": 210, "eta": "4 min", "vehicle": "Mini",    "surge": True,  "savings": None, "badge": "fastest", "logo": "🚗",  "gradient": "black-gray"},
    {"id": 4, "name": "Uber Go",      "price": 240, "eta": "6 min", "vehicle": "Sedan",   "surge": False, "savings": None, "badge": None,      "logo": "🚙",  "gradient": "gray-darkgray"},
    {"id": 5, "name": "BluSmart",     "price": 285, "eta": "8 min", "vehicle": "Electric","surge": False, "savings": None, "badge": "comfort", "logo": "⚡",  "gradient": "blue-cyan"},
    {"id": 6, "name": "Uber Premier", "price": 350, "eta": "7 min", "vehicle": "Premium", "surge": True,  "savings": None, "badge": None,      "logo": "🏆",  "gradient": "purple-pink"},
]

TREND_DATA = [
    {"time": "6AM",  "uber": 180, "ola": 165, "rapido": 140},
    {"time": "8AM",  "uber": 280, "ola": 250, "rapido": 180},
    {"time": "10AM", "uber": 200, "ola": 185, "rapido": 150},
    {"time": "12PM", "uber": 190, "ola": 175, "rapido": 145},
    {"time": "2PM",  "uber": 195, "ola": 180, "rapido": 148},
    {"time": "4PM",  "uber": 210, "ola": 195, "rapido": 160},
    {"time": "6PM",  "uber": 320, "ola": 290, "rapido": 220},
    {"time": "8PM",  "uber": 350, "ola": 310, "rapido": 240},
    {"time": "10PM", "uber": 280, "ola": 250, "rapido": 190},
]

FEATURES = [
    {"icon": "⚡", "title": "Live Fare Tracking",        "description": "Real-time price updates across all major ride services in your city",           "gradient": "yellow-orange"},
    {"icon": "🔔", "title": "Surge Alerts",              "description": "Get notified when surge pricing kicks in and when it's best to book",             "gradient": "red-pink"},
    {"icon": "🧠", "title": "Smart Recommendations",     "description": "AI-powered insights to help you choose the best ride for your needs",              "gradient": "purple-pink"},
    {"icon": "👆", "title": "One Tap Booking",           "description": "Seamlessly redirect to your preferred app with a single click",                   "gradient": "blue-cyan"},
    {"icon": "📊", "title": "Ride History Analytics",    "description": "Track your savings and ride patterns over time with detailed analytics",           "gradient": "green-emerald"},
    {"icon": "🔒", "title": "Privacy First",             "description": "We never store your location data or personal information",                        "gradient": "indigo-purple"},
]

TESTIMONIALS = [
    {"name": "Priya Sharma",    "role": "Daily Commuter",   "avatar": "👩‍💼", "rating": 5, "text": "I've saved over ₹2,000 this month alone! Real Time Taxi Comparer makes it so easy to find the cheapest ride every single time.", "gradient": "purple-pink"},
    {"name": "Rahul Verma",     "role": "Startup Founder",  "avatar": "👨‍💻", "rating": 5, "text": "As someone who takes 4-5 rides daily, this app is a game-changer. The AI recommendations are spot on.",            "gradient": "blue-cyan"},
    {"name": "Anjali Patel",    "role": "College Student",  "avatar": "👩‍🎓", "rating": 5, "text": "Being on a student budget, every rupee counts. Real Time Taxi Comparer helps me save money without compromising on convenience.","gradient": "green-emerald"},
    {"name": "Vikram Singh",    "role": "Sales Manager",    "avatar": "👨‍💼", "rating": 5, "text": "The surge alerts are incredible. I time my rides perfectly now and avoid paying extra during peak hours.",           "gradient": "orange-red"},
    {"name": "Sneha Reddy",     "role": "Freelancer",       "avatar": "👩‍🎨", "rating": 5, "text": "Love the clean interface and how fast it compares prices. No more switching between 5 different apps!",             "gradient": "indigo-purple"},
    {"name": "Arjun Malhotra",  "role": "Tech Lead",        "avatar": "👨‍🔬", "rating": 5, "text": "The analytics dashboard is fantastic. I can track my spending patterns and optimize my ride bookings.",            "gradient": "cyan-blue"},
]

PROVIDERS = [
    {"id": 1, "name": "Rapido", "vehicle": "Bike", "logo": "🏍️", "gradient": "yellow-orange", "base": 28, "per_km": 9, "per_min": 0.9, "min_fare": 55},
    {"id": 2, "name": "Namma Yatri", "vehicle": "Auto", "logo": "🛺", "gradient": "green-emerald", "base": 40, "per_km": 11, "per_min": 1.1, "min_fare": 70},
    {"id": 3, "name": "Ola", "vehicle": "Mini", "logo": "🚗", "gradient": "black-gray", "base": 52, "per_km": 14, "per_min": 1.3, "min_fare": 90},
    {"id": 4, "name": "Uber Go", "vehicle": "Sedan", "logo": "🚙", "gradient": "gray-darkgray", "base": 60, "per_km": 15, "per_min": 1.5, "min_fare": 105},
    {"id": 5, "name": "BluSmart", "vehicle": "Electric", "logo": "⚡", "gradient": "blue-cyan", "base": 68, "per_km": 16, "per_min": 1.6, "min_fare": 120},
    {"id": 6, "name": "Uber Premier", "vehicle": "Premium", "logo": "🏆", "gradient": "purple-pink", "base": 92, "per_km": 22, "per_min": 2.1, "min_fare": 165},
]


def fetch_json(url, params=None, headers=None, timeout=8):
    if params:
        query = urlencode(params)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query}"
    req_headers = {
        "User-Agent": "ComparifyTaxiApp/1.0 (contact: local-dev)",
        "Accept": "application/json",
    }
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers)
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_places(query):
    if len(query.strip()) < 2:
        return []
    try:
        data = fetch_json(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 5,
            },
        )
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
        return []

    results = []
    for place in data:
        parts = [p.strip() for p in place.get("display_name", "").split(",")]
        if not parts:
            continue
        results.append(
            {
                "place_id": str(place.get("place_id", "")),
                "description": place.get("display_name", ""),
                "main_text": parts[0],
                "secondary_text": ", ".join(parts[1:4]) if len(parts) > 1 else "",
                "lat": float(place.get("lat")),
                "lon": float(place.get("lon")),
            }
        )
    return results


def resolve_place(query):
    matches = search_places(query)
    return matches[0] if matches else None


def route_metrics(pickup, destination):
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{pickup['lon']},{pickup['lat']};{destination['lon']},{destination['lat']}"
    )
    try:
        data = fetch_json(url, params={"overview": "false"})
        route = data.get("routes", [])[0]
        meters = float(route["distance"])
        seconds = float(route["duration"])
        return {"distance_km": meters / 1000.0, "duration_min": seconds / 60.0}
    except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, TypeError, ValueError):
        return None


def surge_multiplier():
    hour = datetime.now().hour
    if 7 <= hour <= 10:
        return 1.25
    if 17 <= hour <= 21:
        return 1.35
    if 0 <= hour <= 5:
        return 1.15
    return 1.0


def estimate_rides(distance_km, duration_min, ride_type="any"):
    mult = surge_multiplier()
    rides = []
    for p in PROVIDERS:
        price = p["base"] + (distance_km * p["per_km"]) + (duration_min * p["per_min"])
        price = max(price, p["min_fare"])
        if p["vehicle"] in {"Premium"}:
            price *= 1.08
        if mult > 1 and p["vehicle"] in {"Mini", "Sedan", "Premium"}:
            price *= mult
        rides.append(
            {
                "id": p["id"],
                "name": p["name"],
                "vehicle": p["vehicle"],
                "logo": p["logo"],
                "gradient": p["gradient"],
                "price": int(round(price)),
                "eta": f"{max(2, int(math.ceil(duration_min / 5.5)))} min",
                "surge": mult > 1 and p["vehicle"] in {"Mini", "Sedan", "Premium"},
            }
        )

    if ride_type == "economy":
        rides = [r for r in rides if r["vehicle"] in {"Bike", "Auto", "Mini"}]
    elif ride_type == "premium":
        rides = [r for r in rides if r["vehicle"] in {"Sedan", "Electric", "Premium"}]

    rides.sort(key=lambda x: x["price"])
    if rides:
        cheapest = rides[0]["price"]
        fastest = min(rides, key=lambda x: int(x["eta"].split()[0]))["id"]
        for i, r in enumerate(rides):
            r["savings"] = max(0, r["price"] - cheapest) if i != 0 else 0
            r["badge"] = "cheapest" if i == 0 else ("fastest" if r["id"] == fastest else None)
    return rides

# ── API Routes ───────────────────────────────────────────────────────────────

@app.route("/api/places")
def places():
    query = request.args.get("q", "")
    return jsonify(search_places(query))

@app.route("/api/compare", methods=["POST"])
def compare():
    data = request.get_json() or {}
    pickup = data.get("pickup", "")
    destination = data.get("destination", "")
    ride_type = data.get("rideType", "any")
    if not pickup or not destination:
        return jsonify({"error": "Pickup and destination are required"}), 400

    pickup_place = resolve_place(pickup)
    destination_place = resolve_place(destination)
    if not pickup_place or not destination_place:
        return jsonify({"error": "Could not resolve one or both locations"}), 400

    metrics = route_metrics(pickup_place, destination_place)
    if not metrics:
        return jsonify({"error": "Could not calculate route right now"}), 502

    rides = estimate_rides(metrics["distance_km"], metrics["duration_min"], ride_type)
    return jsonify(
        {
            "rides": rides,
            "pickup": pickup_place["description"],
            "destination": destination_place["description"],
            "distance_km": round(metrics["distance_km"], 2),
            "duration_min": round(metrics["duration_min"], 1),
        }
    )

# ── Main HTML Template ───────────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Real Time Taxi Comparer – Find the Cheapest Ride</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    /* ── Reset & Base ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:       #070B14;
      --bg2:      #0F172A;
      --purple:   #7C3AED;
      --cyan:     #06B6D4;
      --green:    #22C55E;
      --pink:     #EC4899;
      --yellow:   #EAB308;
      --orange:   #F97316;
      --red:      #EF4444;
      --indigo:   #6366F1;
      --blue:     #3B82F6;
      --card:     rgba(255,255,255,0.05);
      --border:   rgba(255,255,255,0.10);
      --text-muted: #94A3B8;
    }
    html { scroll-behavior: smooth; }
    body {
      background: var(--bg);
      color: #fff;
      font-family: 'Segoe UI', system-ui, sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }
    a { color: inherit; text-decoration: none; }
    button { cursor: pointer; border: none; background: none; color: #fff; font-family: inherit; }

    /* ── Gradients helper classes ── */
    .grad-purple-cyan  { background: linear-gradient(135deg, var(--purple), var(--cyan)); }
    .grad-yellow-orange{ background: linear-gradient(135deg, var(--yellow), var(--orange)); }
    .grad-green-emerald{ background: linear-gradient(135deg, #16a34a, #10b981); }
    .grad-black-gray   { background: linear-gradient(135deg, #111, #374151); }
    .grad-gray-darkgray{ background: linear-gradient(135deg, #1f2937, #111827); }
    .grad-blue-cyan    { background: linear-gradient(135deg, var(--blue), var(--cyan)); }
    .grad-purple-pink  { background: linear-gradient(135deg, var(--purple), var(--pink)); }
    .grad-red-pink     { background: linear-gradient(135deg, var(--red), var(--pink)); }
    .grad-indigo-purple{ background: linear-gradient(135deg, var(--indigo), var(--purple)); }
    .grad-cyan-blue    { background: linear-gradient(135deg, var(--cyan), var(--blue)); }
    .grad-orange-red   { background: linear-gradient(135deg, var(--orange), var(--red)); }

    .text-grad {
      background: linear-gradient(90deg, var(--purple), var(--cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .text-grad-white {
      background: linear-gradient(180deg, #fff 0%, #fff 60%, #6b7280 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .text-grad-hero {
      background: linear-gradient(90deg, #fff, #e9d5ff, #a5f3fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    /* ── Card ── */
    .card {
      backdrop-filter: blur(20px);
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 1.5rem;
      transition: border-color 0.2s, transform 0.2s;
    }
    .card:hover { border-color: rgba(255,255,255,0.2); }

    /* ── Sections ── */
    section { padding: 6rem 1rem; }
    .container { max-width: 80rem; margin: 0 auto; }
    .section-header { text-align: center; margin-bottom: 4rem; }
    .section-header h2 { font-size: clamp(2.5rem, 5vw, 3.75rem); margin-bottom: 1rem; }
    .section-header p  { font-size: 1.125rem; color: var(--text-muted); }

    /* ── Badge pill ── */
    .pill {
      display: inline-flex; align-items: center; gap: 0.5rem;
      padding: 0.4rem 1rem; border-radius: 9999px;
      background: var(--card); border: 1px solid var(--border);
      font-size: 0.875rem; color: #cbd5e1;
      margin-bottom: 1.5rem;
    }

    /* ════════════════════════════════
       HERO
    ════════════════════════════════ */
    #hero {
      position: relative; min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      overflow: hidden; padding: 0 1rem;
    }
    #hero .orb {
      position: absolute; border-radius: 50%;
      filter: blur(128px); opacity: 0.2;
      animation: pulse 3s ease-in-out infinite;
    }
    #hero .orb1 { width: 24rem; height: 24rem; background: var(--purple); top: 25%; left: -8rem; }
    #hero .orb2 { width: 24rem; height: 24rem; background: var(--cyan);   top: 33%; right: -8rem; animation-delay: 1s; }
    @keyframes pulse { 0%,100%{opacity:0.2} 50%{opacity:0.3} }

    #hero .stars { position: absolute; inset: 0; opacity: 0.3; pointer-events: none; }
    #hero .star {
      position: absolute; width: 4px; height: 4px;
      background: var(--cyan); border-radius: 50%;
      animation: twinkle 3s ease-in-out infinite;
    }
    @keyframes twinkle { 0%,100%{opacity:0.2;transform:scale(1)} 50%{opacity:1;transform:scale(1.5)} }

    .hero-content { position: relative; z-index: 1; text-align: center; max-width: 60rem; }
    .hero-content h1 { font-size: clamp(3rem, 8vw, 5rem); font-weight: 800; line-height: 1.1; margin-bottom: 1.5rem; }
    .hero-content p  { font-size: clamp(1rem, 2.5vw, 1.5rem); color: #94A3B8; margin-bottom: 3rem; }

    .floating-card {
      position: absolute; display: none;
    }
    @media(min-width: 1024px){ .floating-card { display: block; } }
    .floating-card.left  { left: 0;   top: 30%; animation: float 3s ease-in-out infinite; }
    .floating-card.right { right: 0;  top: 40%; animation: float 3s ease-in-out infinite 0.5s; }
    @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
    .floating-card .card { padding: 1rem; }
    .floating-card .row  { display: flex; align-items: center; gap: 0.75rem; }
    .floating-card .icon-circle {
      width: 2.5rem; height: 2.5rem; border-radius: 50%;
      display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
    }

    .dot-row { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-top: 5rem; }
    .dot-row span {
      width: 8px; height: 8px; border-radius: 50%; background: var(--cyan);
      animation: dotPulse 1.5s ease-in-out infinite;
    }
    @keyframes dotPulse { 0%,100%{opacity:0.3} 50%{opacity:1} }

    /* ════════════════════════════════
       SEARCH
    ════════════════════════════════ */
    #search .grid { display: grid; gap: 3rem; align-items: center; }
    @media(min-width:1024px){ #search .grid { grid-template-columns: 1fr 1fr; } }

    .search-form { padding: 2rem; }
    .search-form h2 { font-size: 2rem; margin-bottom: 2rem; }

    .input-group { margin-bottom: 1.5rem; }
    .input-group label { display: block; font-size: 0.875rem; color: var(--text-muted); margin-bottom: 0.5rem; }
    .input-wrap { position: relative; }
    .input-wrap .icon { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); font-size: 1.1rem; pointer-events: none; }
    .input-wrap input {
      width: 100%; padding: 1rem 1rem 1rem 3rem;
      background: var(--card); border: 1px solid var(--border);
      border-radius: 1rem; color: #fff; font-size: 1rem; outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .input-wrap input::placeholder { color: #4B5563; }
    .input-wrap input:focus { border-color: var(--purple); box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }

    /* Autocomplete */
    .suggestions {
      position: absolute; z-index: 50; width: 100%; margin-top: 0.5rem;
      background: rgba(15,23,42,0.97); border: 1px solid var(--border);
      border-radius: 1rem; overflow: hidden; max-height: 18rem; overflow-y: auto;
      display: none;
    }
    .suggestions.open { display: block; }
    .suggestion-item {
      display: flex; align-items: flex-start; gap: 0.75rem;
      padding: 0.75rem 1rem; border-bottom: 1px solid rgba(255,255,255,0.05);
      cursor: pointer; transition: background 0.15s;
    }
    .suggestion-item:hover { background: rgba(255,255,255,0.08); }
    .suggestion-item:last-child { border-bottom: none; }
    .suggestion-item .si-icon { margin-top: 2px; font-size: 0.9rem; }
    .suggestion-item .si-main { font-size: 0.875rem; font-weight: 600; }
    .suggestion-item .si-sub  { font-size: 0.75rem; color: var(--text-muted); }

    /* Ride type buttons */
    .ride-types { display: grid; grid-template-columns: repeat(3,1fr); gap: 0.75rem; }
    .ride-type-btn {
      padding: 0.75rem 0.5rem; border-radius: 0.75rem;
      background: var(--card); border: 1px solid var(--border);
      font-size: 0.875rem; text-align: center;
      transition: all 0.2s; cursor: pointer; color: #fff;
    }
    .ride-type-btn .rt-icon { font-size: 1.2rem; margin-bottom: 0.25rem; }
    .ride-type-btn.active {
      background: linear-gradient(135deg, var(--purple), var(--cyan));
      border-color: transparent;
      box-shadow: 0 4px 20px rgba(124,58,237,0.4);
    }

    .compare-btn {
      width: 100%; margin-top: 1.5rem; padding: 1rem;
      border-radius: 1rem; font-size: 1rem; font-weight: 600;
      background: linear-gradient(90deg, var(--purple), var(--cyan));
      box-shadow: 0 4px 20px rgba(124,58,237,0.35);
      transition: transform 0.15s, box-shadow 0.15s;
      color: #fff;
    }
    .compare-btn:hover { transform: scale(1.02); box-shadow: 0 6px 28px rgba(124,58,237,0.55); }
    .compare-btn:active { transform: scale(0.98); }

    /* Map placeholder */
    .map-placeholder {
      height: 31rem; border-radius: 2rem; overflow: hidden;
      display: flex; align-items: center; justify-content: center;
      position: relative;
    }
    .map-placeholder .grid-bg {
      position: absolute; inset: 0; opacity: 0.07;
      background-image:
        linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px);
      background-size: 50px 50px;
    }
    .map-pin-anim {
      width: 6rem; height: 6rem; border-radius: 50%;
      background: linear-gradient(135deg, var(--purple), var(--cyan));
      display: flex; align-items: center; justify-content: center;
      font-size: 3rem; position: relative; z-index: 1;
      animation: mapPulse 2s ease-in-out infinite;
    }
    @keyframes mapPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.1)} }

    /* ════════════════════════════════
       RESULTS
    ════════════════════════════════ */
    #results { background: linear-gradient(to bottom, transparent, rgba(15,23,42,0.5)); }

    .results-grid { display: grid; gap: 1.5rem; }
    @media(min-width:768px)  { .results-grid { grid-template-columns: 1fr 1fr; } }
    @media(min-width:1024px) { .results-grid { grid-template-columns: repeat(3,1fr); } }

    .ride-card { position: relative; }
    .ride-card-inner {
      padding: 1.5rem; height: 100%; position: relative; overflow: hidden;
    }
    .ride-card:hover .ride-card-inner { border-color: rgba(255,255,255,0.2); }
    .ride-card:hover { transform: translateY(-8px) scale(1.01); }

    .ride-badge {
      position: absolute; top: -0.75rem; right: -0.75rem;
      padding: 0.3rem 0.8rem; border-radius: 9999px;
      font-size: 0.7rem; font-weight: 700; text-transform: capitalize;
      display: flex; align-items: center; gap: 0.25rem;
    }
    .surge-badge {
      position: absolute; top: 1rem; right: 1rem;
      padding: 0.25rem 0.5rem; border-radius: 0.5rem;
      background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.4);
      font-size: 0.7rem; color: #f87171;
      animation: surgeBlink 1.5s ease-in-out infinite;
    }
    @keyframes surgeBlink { 0%,100%{opacity:0.5} 50%{opacity:1} }

    .ride-logo-box {
      width: 4rem; height: 4rem; border-radius: 1rem;
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem; margin-bottom: 1rem;
    }
    .ride-name  { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.25rem; }
    .ride-type  { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1rem; }
    .ride-price { font-size: 2.5rem; font-weight: 700; }
    .ride-savings { font-size: 0.875rem; color: #4ade80; margin-left: 0.5rem; }
    .ride-eta { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem; }

    .book-btn {
      width: 100%; margin-top: 1rem; padding: 0.75rem;
      border-radius: 0.75rem; font-weight: 600;
      transition: opacity 0.15s, transform 0.1s;
      color: #fff; opacity: 0.9;
    }
    .book-btn:hover { opacity: 1; transform: scale(1.03); }

    /* ════════════════════════════════
       AI RECOMMENDATION
    ════════════════════════════════ */
    #ai { }
    .ai-card { max-width: 52rem; margin: 0 auto; padding: 3rem; position: relative; }

    .ai-badge-row { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
    .ai-spin {
      width: 3rem; height: 3rem; border-radius: 50%;
      background: linear-gradient(135deg, var(--purple), var(--cyan));
      display: flex; align-items: center; justify-content: center;
      font-size: 1.4rem; animation: spin 3s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .ai-badge-text h3 { font-size: 0.875rem; color: var(--text-muted); }
    .ai-badge-text p  { font-size: 0.75rem;  color: #4B5563; }

    .ai-rec { display: flex; align-items: flex-start; gap: 1rem; padding: 1rem; border-radius: 1rem; margin-bottom: 1rem; }
    .ai-rec-icon { width: 2.5rem; height: 2.5rem; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; flex-shrink: 0; }
    .ai-rec h4 { font-size: 1.1rem; margin-bottom: 0.25rem; }
    .ai-rec p  { font-size: 0.9rem; color: var(--text-muted); }
    .ai-rec.green  { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.2);  }
    .ai-rec.blue   { background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2); }
    .ai-rec.purple { background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.2); }

    .ai-stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid var(--border); text-align: center; }
    .ai-stats .stat-val { font-size: 2rem; font-weight: 700; }
    .ai-stats .stat-lbl { font-size: 0.75rem; color: var(--text-muted); }

    /* ════════════════════════════════
       PRICE TREND
    ════════════════════════════════ */
    #trend { }
    .trend-card { padding: 2rem; }
    .trend-header { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; margin-bottom: 2rem; gap: 1rem; }
    .trend-header h3 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .trend-header p  { font-size: 0.875rem; color: var(--text-muted); }
    .legend { display: flex; gap: 1.5rem; }
    .legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--text-muted); }
    .legend-dot { width: 0.75rem; height: 0.75rem; border-radius: 50%; }
    .chart-wrap { height: 25rem; }

    .peak-grid { display: grid; gap: 1rem; margin-top: 2rem; }
    @media(min-width:768px){ .peak-grid { grid-template-columns: repeat(3,1fr); } }
    .peak-card { padding: 1rem; border-radius: 1rem; }
    .peak-card.red    { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.2);  }
    .peak-card.green  { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.2);  }
    .peak-card.yellow { background: rgba(234,179,8,0.08);  border: 1px solid rgba(234,179,8,0.2);  }
    .peak-card h4  { font-size: 0.875rem; margin-bottom: 0.25rem; }
    .peak-card .pv { font-size: 1rem; font-weight: 600; }
    .peak-card p   { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

    /* ════════════════════════════════
       FEATURES
    ════════════════════════════════ */
    #features { background: linear-gradient(to bottom, transparent, rgba(15,23,42,0.5)); }

    .features-grid { display: grid; gap: 1.5rem; }
    @media(min-width:768px)  { .features-grid { grid-template-columns: 1fr 1fr; } }
    @media(min-width:1024px) { .features-grid { grid-template-columns: repeat(3,1fr); } }

    .feature-card { padding: 2rem; height: 100%; }
    .feature-icon {
      width: 4rem; height: 4rem; border-radius: 1rem;
      display: flex; align-items: center; justify-content: center;
      font-size: 2rem; margin-bottom: 1.5rem;
    }
    .feature-card h3 { font-size: 1.25rem; margin-bottom: 0.75rem; }
    .feature-card p  { color: var(--text-muted); line-height: 1.6; font-size: 0.95rem; }

    /* ════════════════════════════════
       APP SHOWCASE (3 phones)
    ════════════════════════════════ */
    #showcase .phones-grid { display: grid; gap: 2rem; align-items: start; justify-items: center; }
    @media(min-width:1024px){ #showcase .phones-grid { grid-template-columns: repeat(3,1fr); } }

    .phone {
      position: relative; width: 16rem; height: 32.5rem;
      background: linear-gradient(135deg, #1f2937, #000);
      border-radius: 3rem; padding: 0.75rem;
      box-shadow: 0 25px 60px rgba(0,0,0,0.6);
      border: 4px solid #374151;
    }
    .phone.center { transform: scale(1.05); z-index: 10; }
    .phone .notch {
      position: absolute; top: 0; left: 50%; transform: translateX(-50%);
      width: 8rem; height: 1.5rem; background: #000; border-radius: 0 0 1rem 1rem; z-index: 2;
    }
    .phone-screen {
      width: 100%; height: 100%;
      background: linear-gradient(180deg, var(--bg) 0%, var(--bg2) 100%);
      border-radius: 2.5rem; overflow: hidden; padding: 1.5rem;
    }
    .phone-screen h3 { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem; }
    .phone-input { padding: 0.75rem; background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
    .phone-input .dot { width: 8px; height: 8px; border-radius: 50%; }
    .phone-bar { height: 8px; border-radius: 4px; background: #374151; }
    .phone-btn { height: 2.5rem; border-radius: 0.75rem; margin-top: 1.5rem; }
    .phone-ride { padding: 0.75rem; background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.75rem; position: relative; }
    .phone-ride .ph-icon { width: 2rem; height: 2rem; border-radius: 0.5rem; flex-shrink: 0; }
    .phone-ride .ph-price { width: 3rem; height: 0.75rem; background: #374151; border-radius: 0.25rem; margin-left: auto; }
    .phone-bar-sm { height: 6px; border-radius: 3px; background: #1f2937; }
    .phone-stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; }
    .phone-stat { padding: 0.5rem; background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; }
    .phone-chart { padding: 1rem; background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; }
    .phone-bars { display: flex; align-items: flex-end; justify-content: space-between; height: 4rem; gap: 0.2rem; }
    .phone-bar-item { flex: 1; border-radius: 2px 2px 0 0; background: linear-gradient(to top, var(--purple), var(--cyan)); }
    .phone-label { text-align: center; font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem; }

    .phone-glow { position: absolute; inset: 0; border-radius: 3rem; pointer-events: none; }

    /* ════════════════════════════════
       TESTIMONIALS
    ════════════════════════════════ */
    #testimonials { background: linear-gradient(to bottom, transparent, rgba(15,23,42,0.5)); }

    .testimonials-grid { display: grid; gap: 1.5rem; }
    @media(min-width:768px)  { .testimonials-grid { grid-template-columns: 1fr 1fr; } }
    @media(min-width:1024px) { .testimonials-grid { grid-template-columns: repeat(3,1fr); } }

    .tcard { padding: 1.5rem; height: 100%; position: relative; }
    .tcard .quote-icon { position: absolute; top: 1.5rem; right: 1.5rem; opacity: 0.15; font-size: 3rem; }
    .tcard-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
    .tcard-avatar {
      width: 3.5rem; height: 3.5rem; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.5rem;
    }
    .tcard-name { font-size: 1.1rem; font-weight: 600; }
    .tcard-role { font-size: 0.875rem; color: var(--text-muted); }
    .stars { display: flex; gap: 0.25rem; margin-bottom: 1rem; font-size: 0.9rem; }
    .tcard p { color: #CBD5E1; line-height: 1.6; font-size: 0.95rem; }

    .stats-row { display: grid; gap: 1.5rem; margin-top: 4rem; }
    @media(min-width:768px){ .stats-row { grid-template-columns: repeat(4,1fr); } }
    .stat-box { padding: 1.5rem; border-radius: 1rem; text-align: center; }
    .stat-box .sv { font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem; }
    .stat-box .sl { font-size: 0.875rem; color: var(--text-muted); }

    /* ════════════════════════════════
       FINAL CTA
    ════════════════════════════════ */
    #cta { position: relative; overflow: hidden; }
    #cta .cta-orb1 { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 50rem; height: 50rem; background: var(--purple); border-radius: 50%; filter: blur(200px); opacity: 0.15; pointer-events:none; }
    #cta .cta-orb2 { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); width: 37.5rem; height: 37.5rem; background: var(--cyan);   border-radius: 50%; filter: blur(200px); opacity: 0.15; pointer-events:none; }

    .cta-card { max-width: 62rem; margin: 0 auto; padding: 4rem 3rem; text-align: center; border-radius: 3rem; position: relative; overflow: hidden; }
    .cta-card h2 { font-size: clamp(2.5rem, 6vw, 4.5rem); line-height: 1.15; margin-bottom: 1.5rem; }
    .cta-card p  { font-size: 1.25rem; color: #CBD5E1; margin-bottom: 3rem; max-width: 36rem; margin-left: auto; margin-right: auto; }

    .cta-btns { display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin-bottom: 3rem; }
    .cta-primary {
      padding: 1rem 2.5rem; border-radius: 9999px; font-size: 1.1rem; font-weight: 600;
      background: linear-gradient(90deg, var(--purple), var(--cyan));
      box-shadow: 0 8px 32px rgba(124,58,237,0.5);
      transition: transform 0.15s, box-shadow 0.15s; color: #fff;
    }
    .cta-primary:hover { transform: scale(1.05); box-shadow: 0 12px 40px rgba(124,58,237,0.7); }
    .cta-secondary {
      padding: 1rem 2.5rem; border-radius: 9999px; font-size: 1.1rem;
      background: var(--card); border: 1px solid rgba(255,255,255,0.2);
      transition: background 0.15s; color: #fff;
    }
    .cta-secondary:hover { background: rgba(255,255,255,0.1); }

    .trust-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 2rem; font-size: 0.875rem; color: var(--text-muted); }
    .trust-row span { display: flex; align-items: center; gap: 0.5rem; }
    .trust-row .green-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); }

    /* Spinning rings on CTA */
    .ring1, .ring2 {
      position: absolute; border-radius: 50%; pointer-events: none;
      border: 2px solid rgba(124,58,237,0.15);
    }
    .ring1 { width: 6rem; height: 6rem; top: 2rem; right: 2rem; animation: spin 20s linear infinite; }
    .ring2 { width: 8rem; height: 8rem; bottom: 2rem; left: 2rem; border-color: rgba(6,182,212,0.15); animation: spin 25s linear infinite reverse; }

    /* ════════════════════════════════
       FOOTER
    ════════════════════════════════ */
    footer {
      border-top: 1px solid var(--border);
      background: linear-gradient(to bottom, transparent, rgba(15,23,42,0.8));
      padding: 4rem 1rem;
    }
    .footer-grid { display: grid; gap: 3rem; margin-bottom: 3rem; }
    @media(min-width:768px){ .footer-grid { grid-template-columns: 2fr 1fr 1fr; } }
    .footer-brand h3 { font-size: 2rem; font-weight: 800; margin-bottom: 1rem; }
    .footer-brand p  { color: var(--text-muted); max-width: 26rem; margin-bottom: 1.5rem; line-height: 1.6; }
    .social-row { display: flex; gap: 1rem; }
    .social-btn {
      width: 2.5rem; height: 2.5rem; border-radius: 50%;
      background: var(--card); border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem; color: var(--text-muted); transition: background 0.15s;
    }
    .social-btn:hover { background: rgba(255,255,255,0.1); }
    .footer-col h4 { color: #CBD5E1; margin-bottom: 1rem; font-weight: 600; }
    .footer-col ul  { list-style: none; }
    .footer-col li  { margin-bottom: 0.75rem; }
    .footer-col a   { color: var(--text-muted); transition: color 0.15s; font-size: 0.95rem; }
    .footer-col a:hover { color: #fff; }

    .supported-apps { border-top: 1px solid var(--border); padding: 3rem 0 2rem; text-align: center; }
    .supported-apps p { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1.5rem; }
    .app-chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 1rem; }
    .app-chip {
      display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
      padding: 0.75rem 1rem; background: var(--card); border: 1px solid var(--border);
      border-radius: 0.75rem; min-width: 5rem; transition: border-color 0.15s;
    }
    .app-chip:hover { border-color: rgba(255,255,255,0.2); }
    .app-chip span:first-child { font-size: 1.5rem; }
    .app-chip span:last-child  { font-size: 0.75rem; color: var(--text-muted); }

    .footer-bottom {
      border-top: 1px solid var(--border); padding-top: 2rem;
      display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 1rem;
    }
    .footer-bottom p { font-size: 0.875rem; color: var(--text-muted); }
    .footer-links { display: flex; gap: 1.5rem; }
    .footer-links a { font-size: 0.875rem; color: var(--text-muted); transition: color 0.15s; }
    .footer-links a:hover { color: #fff; }

    /* ── Utility ── */
    .highlight-green  { color: #4ade80; }
    .highlight-blue   { color: #60a5fa; }
    .highlight-purple { color: #c084fc; }
    .highlight-white  { color: #fff; font-weight: 600; }

    /* ── Scroll fade-in ── */
    .fade-in { opacity: 0; transform: translateY(30px); transition: opacity 0.6s ease, transform 0.6s ease; }
    .fade-in.visible { opacity: 1; transform: none; }

    /* Toast */
    #toast {
      position: fixed; bottom: 2rem; right: 2rem; z-index: 100;
      padding: 1rem 1.5rem; border-radius: 1rem;
      background: rgba(15,23,42,0.95); border: 1px solid var(--border);
      font-size: 0.9rem; color: #fff;
      transform: translateY(4rem); opacity: 0;
      transition: transform 0.3s, opacity 0.3s;
    }
    #toast.show { transform: none; opacity: 1; }
  </style>
</head>
<body>

<!-- HERO ──────────────────────────────────────────────────────── -->
<section id="hero">
  <div class="orb orb1"></div>
  <div class="orb orb2"></div>

  <!-- Twinkling stars -->
  <div class="stars" id="starfield"></div>

  <!-- Floating price cards -->
  <div class="floating-card left">
    <div class="card">
      <div class="row">
        <div class="icon-circle grad-purple-cyan">🚗</div>
        <div>
          <p style="font-size:0.75rem;color:#94A3B8">Uber</p>
          <p style="font-weight:600">₹240</p>
        </div>
      </div>
    </div>
  </div>
  <div class="floating-card right">
    <div class="card">
      <div class="row">
        <div class="icon-circle" style="background:linear-gradient(135deg,#06B6D4,#0891B2)">📉</div>
        <div>
          <p style="font-size:0.75rem;color:#94A3B8">Rapido</p>
          <p style="font-weight:600">₹158</p>
        </div>
      </div>
    </div>
  </div>

  <div class="hero-content">
    <div class="pill">
      <span>⚡</span>
      <span>Compare 6+ ride services instantly</span>
    </div>
    <h1 class="text-grad-white">Find the Cheapest<br>Ride in Seconds</h1>
    <p>Compare Uber, Ola, Rapido &amp; more instantly.</p>
    <button class="compare-btn" style="max-width:16rem;margin:0 auto;display:block" onclick="document.getElementById('search').scrollIntoView({behavior:'smooth'})">
      Compare Prices →
    </button>
    <div class="dot-row">
      <span style="animation-delay:0s"></span>
      <span style="animation-delay:0.2s"></span>
      <span style="animation-delay:0.4s"></span>
      <span style="animation-delay:0.6s"></span>
      <span style="animation-delay:0.8s"></span>
    </div>
  </div>
</section>

<!-- SEARCH ─────────────────────────────────────────────────────── -->
<section id="search">
  <div class="container">
    <div class="grid">
      <!-- Form -->
      <div class="card search-form fade-in">
        <h2 class="text-grad">Start Your Search</h2>

        <div class="input-group">
          <label>Pickup Location</label>
          <div class="input-wrap" id="pickupWrap">
            <span class="icon" style="color:#c084fc">📍</span>
            <input type="text" id="pickupInput" placeholder="Search for a location..." autocomplete="off" />
            <div class="suggestions" id="pickupSugg"></div>
          </div>
        </div>

        <div class="input-group">
          <label>Destination</label>
          <div class="input-wrap" id="destWrap">
            <span class="icon" style="color:#22d3ee">🧭</span>
            <input type="text" id="destInput" placeholder="Search for a location..." autocomplete="off" />
            <div class="suggestions" id="destSugg"></div>
          </div>
        </div>

        <div style="margin-bottom:1.5rem">
          <label style="display:block;font-size:0.875rem;color:#94A3B8;margin-bottom:0.75rem">Ride Type</label>
          <div class="ride-types" id="rideTypes">
            <button class="ride-type-btn active" data-type="any">
              <div class="rt-icon">🚗</div>Any
            </button>
            <button class="ride-type-btn" data-type="economy">
              <div class="rt-icon">💰</div>Economy
            </button>
            <button class="ride-type-btn" data-type="premium">
              <div class="rt-icon">⭐</div>Premium
            </button>
          </div>
        </div>

        <button class="compare-btn" id="compareBtn">Compare Prices ⚡</button>
      </div>

      <!-- Map placeholder -->
      <div class="card map-placeholder fade-in">
        <div class="grid-bg"></div>
        <div style="text-align:center;position:relative;z-index:1">
          <div class="map-pin-anim">📍</div>
          <p style="color:#94A3B8;margin-top:1rem">Enter locations to see route</p>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- RESULTS ────────────────────────────────────────────────────── -->
<section id="results">
  <div class="container">
    <div class="section-header fade-in">
      <h2 class="text-grad-hero">Live Price Comparison</h2>
      <p>Real-time prices from 6 ride services</p>
    </div>
    <div class="results-grid" id="rideCards">
      {% for ride in ride_data %}
      <div class="card ride-card fade-in" style="transition-delay:{{ loop.index0 * 0.08 }}s">
        <div class="card ride-card-inner">
          {% if ride.badge %}
          <div class="ride-badge
            {% if ride.badge == 'cheapest' %}grad-green-emerald
            {% elif ride.badge == 'fastest' %}grad-blue-cyan
            {% else %}grad-purple-pink{% endif %}">
            {% if ride.badge == 'cheapest' %}📉
            {% elif ride.badge == 'fastest' %}⚡
            {% else %}🏆{% endif %}
            {{ ride.badge }}
          </div>
          {% endif %}
          {% if ride.surge %}
          <div class="surge-badge">Surge</div>
          {% endif %}
          <div class="ride-logo-box grad-{{ ride.gradient }}">{{ ride.logo }}</div>
          <div class="ride-name">{{ ride.name }}</div>
          <div class="ride-type">{{ ride.vehicle }}</div>
          <div style="display:flex;align-items:baseline">
            <span class="ride-price text-grad-white">₹{{ ride.price }}</span>
            {% if ride.savings %}
            <span class="ride-savings">Save ₹{{ ride.savings }}</span>
            {% endif %}
          </div>
          <div class="ride-eta">⏱ {{ ride.eta }} away</div>
          <button class="book-btn grad-{{ ride.gradient }}" onclick="bookRide('{{ ride.name }}')">Book Now</button>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<!-- AI RECOMMENDATION ──────────────────────────────────────────── -->
<section id="ai">
  <div class="container">
    <div class="card ai-card fade-in">
      <div class="ai-badge-row">
        <div class="ai-spin">✨</div>
        <div class="ai-badge-text">
          <h3>AI Smart Recommendation</h3>
          <p>Powered by intelligent analysis</p>
        </div>
      </div>

      <div class="ai-rec green">
        <div class="ai-rec-icon" style="background:rgba(34,197,94,0.15)">📉</div>
        <div>
          <h4>Best Value Right Now</h4>
          <p><span class="highlight-green">Rapido</span> saves you <span class="highlight-white">₹82</span> compared to the average price.</p>
        </div>
      </div>

      <div class="ai-rec blue">
        <div class="ai-rec-icon" style="background:rgba(59,130,246,0.15)">⏱</div>
        <div>
          <h4>Fastest Option</h4>
          <p><span class="highlight-blue">Ola</span> arrives <span class="highlight-white">2 minutes faster</span> than other options.</p>
        </div>
      </div>

      <div class="ai-rec purple">
        <div class="ai-rec-icon" style="background:rgba(124,58,237,0.15)">✨</div>
        <div>
          <h4>Surge Alert</h4>
          <p>Prices are <span class="highlight-purple">15% higher</span> than usual. Consider waiting 20 minutes for better rates.</p>
        </div>
      </div>

      <div class="ai-stats">
        <div><div class="stat-val text-grad">₹82</div><div class="stat-lbl">Avg Savings</div></div>
        <div><div class="stat-val text-grad">4.2</div><div class="stat-lbl">Min ETA</div></div>
        <div><div class="stat-val text-grad">6</div><div class="stat-lbl">Options</div></div>
      </div>
    </div>
  </div>
</section>

<!-- PRICE TREND ────────────────────────────────────────────────── -->
<section id="trend">
  <div class="container">
    <div class="section-header fade-in">
      <div class="pill"><span style="color:#4ade80">📈</span> Real-time analytics</div>
      <h2 class="text-grad-hero">Price Trends</h2>
      <p>Know when to book for the best rates</p>
    </div>
    <div class="card trend-card fade-in">
      <div class="trend-header">
        <div>
          <h3>Today's Fare Analysis</h3>
          <p>Hourly average prices across platforms</p>
        </div>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:#7C3AED"></div>Uber</div>
          <div class="legend-item"><div class="legend-dot" style="background:#06B6D4"></div>Ola</div>
          <div class="legend-item"><div class="legend-dot" style="background:#22C55E"></div>Rapido</div>
        </div>
      </div>
      <div class="chart-wrap">
        <canvas id="trendChart"></canvas>
      </div>
      <div class="peak-grid">
        <div class="peak-card red">
          <h4 style="color:#f87171">Peak Hours</h4>
          <div class="pv">6–9 PM</div>
          <p>+45% surge pricing</p>
        </div>
        <div class="peak-card green">
          <h4 style="color:#4ade80">Best Time</h4>
          <div class="pv">10 AM – 2 PM</div>
          <p>Lowest fares</p>
        </div>
        <div class="peak-card yellow">
          <h4 style="color:#facc15">Morning Rush</h4>
          <div class="pv">7–9 AM</div>
          <p>+30% average</p>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- FEATURES ───────────────────────────────────────────────────── -->
<section id="features">
  <div class="container">
    <div class="section-header fade-in">
      <h2 class="text-grad-hero">Powerful Features</h2>
      <p>Everything you need to save money on rides</p>
    </div>
    <div class="features-grid">
      {% for f in features %}
      <div class="card feature-card fade-in" style="transition-delay:{{ loop.index0 * 0.08 }}s">
        <div class="feature-icon grad-{{ f.gradient }}">{{ f.icon }}</div>
        <h3>{{ f.title }}</h3>
        <p>{{ f.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<!-- APP SHOWCASE ───────────────────────────────────────────────── -->
<section id="showcase">
  <div class="container">
    <div class="section-header fade-in">
      <h2 class="text-grad-hero">Experience the App</h2>
      <p>Beautiful interface, powerful features</p>
    </div>
    <div class="phones-grid">
      <!-- Phone 1: Search -->
      <div class="fade-in" style="text-align:center">
        <div class="phone" style="animation:float 3s ease-in-out infinite">
          <div class="notch"></div>
          <div class="phone-screen">
            <h3>Search</h3>
            <div class="phone-input"><div class="dot" style="background:#7C3AED"></div><div class="phone-bar" style="width:8rem"></div></div>
            <div class="phone-input"><div class="dot" style="background:#06B6D4"></div><div class="phone-bar" style="width:6rem"></div></div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;margin:1rem 0">
              <div style="padding:0.5rem;background:var(--card);border:1px solid var(--border);border-radius:0.5rem;text-align:center;font-size:1.2rem">🚗</div>
              <div style="padding:0.5rem;background:var(--card);border:1px solid var(--border);border-radius:0.5rem;text-align:center;font-size:1.2rem">💰</div>
              <div style="padding:0.5rem;background:var(--card);border:1px solid var(--border);border-radius:0.5rem;text-align:center;font-size:1.2rem">⭐</div>
            </div>
            <div class="phone-btn grad-purple-cyan"></div>
          </div>
          <div class="phone-glow" style="background:linear-gradient(to top,rgba(124,58,237,0.2),transparent)"></div>
        </div>
        <p style="color:#94A3B8;margin-top:1rem;font-size:0.9rem">Quick Search</p>
      </div>

      <!-- Phone 2: Results (centre) -->
      <div class="fade-in" style="text-align:center;transition-delay:0.1s">
        <div class="phone center" style="animation:float 3s ease-in-out infinite;animation-delay:1s">
          <div class="notch"></div>
          <div class="phone-screen">
            <h3>Live Results</h3>
            <div class="phone-ride">
              <div class="ph-icon grad-yellow-orange"></div>
              <div><div class="phone-bar-sm" style="width:4rem;margin-bottom:4px"></div><div class="phone-bar-sm" style="width:3rem;background:#111827"></div></div>
              <div class="ph-price"></div>
              <div style="position:absolute;top:-4px;right:-4px;background:#22C55E;border-radius:9999px;font-size:0.55rem;padding:1px 6px">BEST</div>
            </div>
            <div class="phone-ride">
              <div class="ph-icon grad-green-emerald"></div>
              <div><div class="phone-bar-sm" style="width:4rem;margin-bottom:4px"></div><div class="phone-bar-sm" style="width:3rem;background:#111827"></div></div>
              <div class="ph-price"></div>
            </div>
            <div class="phone-ride">
              <div class="ph-icon grad-blue-cyan"></div>
              <div><div class="phone-bar-sm" style="width:4rem;margin-bottom:4px"></div><div class="phone-bar-sm" style="width:3rem;background:#111827"></div></div>
              <div class="ph-price"></div>
            </div>
          </div>
          <div class="phone-glow" style="background:linear-gradient(to top,rgba(6,182,212,0.3),transparent)"></div>
        </div>
        <p style="color:#94A3B8;margin-top:1rem;font-size:0.9rem">Price Comparison</p>
      </div>

      <!-- Phone 3: Analytics -->
      <div class="fade-in" style="text-align:center;transition-delay:0.2s">
        <div class="phone" style="animation:float 3s ease-in-out infinite;animation-delay:2s">
          <div class="notch"></div>
          <div class="phone-screen">
            <h3>Analytics</h3>
            <div class="phone-stat-grid">
              <div class="phone-stat"><div class="phone-bar-sm" style="width:3rem;background:linear-gradient(90deg,#7C3AED,#06B6D4);height:1rem;border-radius:4px;margin-bottom:6px"></div><div class="phone-bar-sm" style="width:4rem"></div></div>
              <div class="phone-stat"><div class="phone-bar-sm" style="width:3rem;background:linear-gradient(90deg,#7C3AED,#06B6D4);height:1rem;border-radius:4px;margin-bottom:6px"></div><div class="phone-bar-sm" style="width:4rem"></div></div>
              <div class="phone-stat"><div class="phone-bar-sm" style="width:3rem;background:linear-gradient(90deg,#7C3AED,#06B6D4);height:1rem;border-radius:4px;margin-bottom:6px"></div><div class="phone-bar-sm" style="width:4rem"></div></div>
              <div class="phone-stat"><div class="phone-bar-sm" style="width:3rem;background:linear-gradient(90deg,#7C3AED,#06B6D4);height:1rem;border-radius:4px;margin-bottom:6px"></div><div class="phone-bar-sm" style="width:4rem"></div></div>
            </div>
            <div class="phone-chart">
              <div class="phone-bars">
                {% for h in [40,60,45,70,50,80,65] %}
                <div class="phone-bar-item" style="height:{{ h }}%"></div>
                {% endfor %}
              </div>
            </div>
          </div>
          <div class="phone-glow" style="background:linear-gradient(to top,rgba(59,130,246,0.2),transparent)"></div>
        </div>
        <p style="color:#94A3B8;margin-top:1rem;font-size:0.9rem">Ride Analytics</p>
      </div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS ───────────────────────────────────────────────── -->
<section id="testimonials">
  <div class="container">
    <div class="section-header fade-in">
      <h2 class="text-grad-hero">Loved by Thousands</h2>
      <p>Join 50,000+ users saving money daily</p>
    </div>
    <div class="testimonials-grid">
      {% for t in testimonials %}
      <div class="card tcard fade-in" style="transition-delay:{{ loop.index0 * 0.08 }}s">
        <div class="quote-icon">❝</div>
        <div class="tcard-header">
          <div class="tcard-avatar grad-{{ t.gradient }}">{{ t.avatar }}</div>
          <div>
            <div class="tcard-name">{{ t.name }}</div>
            <div class="tcard-role">{{ t.role }}</div>
          </div>
        </div>
        <div class="stars">{% for _ in range(t.rating) %}⭐{% endfor %}</div>
        <p>{{ t.text }}</p>
      </div>
      {% endfor %}
    </div>
    <div class="stats-row">
      {% for s in [("50K+","Active Users"),("₹2.5Cr+","Total Saved"),("4.9/5","App Rating"),("1M+","Rides Compared")] %}
      <div class="card stat-box fade-in">
        <div class="sv text-grad">{{ s[0] }}</div>
        <div class="sl">{{ s[1] }}</div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<!-- FINAL CTA ──────────────────────────────────────────────────── -->
<section id="cta">
  <div class="cta-orb1"></div>
  <div class="cta-orb2"></div>
  <div class="container">
    <div class="card cta-card fade-in">
      <div class="ring1"></div>
      <div class="ring2"></div>
      <h2 class="text-grad-hero">Stop Overpaying<br>for Rides</h2>
      <p>Join thousands of smart commuters saving money every day with Real Time Taxi Comparer</p>
      <div class="cta-btns">
        <button class="cta-primary" onclick="document.getElementById('search').scrollIntoView({behavior:'smooth'})">
          Start Comparing →
        </button>
        <button class="cta-secondary" onclick="document.getElementById('features').scrollIntoView({behavior:'smooth'})">
          Learn More
        </button>
      </div>
      <div class="trust-row">
        <span><div class="green-dot"></div>100% Free</span>
        <span><div class="green-dot"></div>No Sign-up Required</span>
        <span><div class="green-dot"></div>Privacy Protected</span>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER ─────────────────────────────────────────────────────── -->
<footer>
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <h3 class="text-grad">Real Time Taxi Comparer</h3>
        <p>The smartest way to compare ride prices. Save money on every trip with real-time fare comparisons across all major platforms.</p>
        <div class="social-row">
          <a class="social-btn" href="#" title="Twitter">🐦</a>
          <a class="social-btn" href="#" title="LinkedIn">💼</a>
          <a class="social-btn" href="#" title="Instagram">📷</a>
          <a class="social-btn" href="#" title="GitHub">🐙</a>
        </div>
      </div>
      <div class="footer-col">
        <h4>Product</h4>
        <ul>
          <li><a href="#">Features</a></li>
          <li><a href="#">Pricing</a></li>
          <li><a href="#">How it Works</a></li>
          <li><a href="#">FAQ</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Company</h4>
        <ul>
          <li><a href="#">About Us</a></li>
          <li><a href="#">Careers</a></li>
          <li><a href="#">Blog</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="supported-apps">
      <p>Comparing prices from</p>
      <div class="app-chips">
        <div class="app-chip"><span>🚗</span><span>Uber</span></div>
        <div class="app-chip"><span>🚕</span><span>Ola</span></div>
        <div class="app-chip"><span>🏍️</span><span>Rapido</span></div>
        <div class="app-chip"><span>🛺</span><span>Namma Yatri</span></div>
        <div class="app-chip"><span>⚡</span><span>BluSmart</span></div>
        <div class="app-chip"><span>➕</span><span>More</span></div>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2026 Real Time Taxi Comparer. All rights reserved.</p>
      <div class="footer-links">
        <a href="#">Privacy Policy</a>
        <a href="#">Terms of Service</a>
        <a href="#">Cookie Policy</a>
      </div>
    </div>
  </div>
</footer>

<!-- Toast -->
<div id="toast">📱 Opening booking app...</div>

<!-- ── Scripts ──────────────────────────────────────────────────── -->
<script>
// ── Starfield ────────────────────────────────────────────────────
(function(){
  const sf = document.getElementById('starfield');
  for(let i=0;i<20;i++){
    const s = document.createElement('div');
    s.className = 'star';
    s.style.left = Math.random()*100 + '%';
    s.style.top  = Math.random()*100 + '%';
    s.style.animationDelay = (Math.random()*2) + 's';
    s.style.animationDuration = (2 + Math.random()*2) + 's';
    sf.appendChild(s);
  }
})();

// ── Scroll fade-in observer ──────────────────────────────────────
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if(e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.12 });
document.querySelectorAll('.fade-in').forEach(el => io.observe(el));

// ── Ride type selector ───────────────────────────────────────────
let selectedRideType = 'any';
document.querySelectorAll('.ride-type-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.ride-type-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedRideType = btn.dataset.type;
  });
});

// ── Autocomplete ─────────────────────────────────────────────────
let pickupTimer, destTimer;

function buildSuggestions(containerEl, results, inputEl) {
  containerEl.innerHTML = '';
  if (!results.length) { containerEl.classList.remove('open'); return; }
  results.forEach(r => {
    const item = document.createElement('div');
    item.className = 'suggestion-item';
    item.innerHTML = `<span class="si-icon">📍</span><div><div class="si-main">${r.main_text}</div><div class="si-sub">${r.secondary_text}</div></div>`;
    item.addEventListener('mousedown', () => {
      inputEl.value = r.description;
      containerEl.classList.remove('open');
    });
    containerEl.appendChild(item);
  });
  containerEl.classList.add('open');
}

async function fetchSuggestions(query) {
  if (query.length < 2) return [];
  const res = await fetch(`/api/places?q=${encodeURIComponent(query)}`);
  return res.json();
}

const pickupInput = document.getElementById('pickupInput');
const destInput   = document.getElementById('destInput');
const pickupSugg  = document.getElementById('pickupSugg');
const destSugg    = document.getElementById('destSugg');

pickupInput.addEventListener('input', () => {
  clearTimeout(pickupTimer);
  pickupTimer = setTimeout(async () => {
    const results = await fetchSuggestions(pickupInput.value);
    buildSuggestions(pickupSugg, results, pickupInput);
  }, 350);
});

destInput.addEventListener('input', () => {
  clearTimeout(destTimer);
  destTimer = setTimeout(async () => {
    const results = await fetchSuggestions(destInput.value);
    buildSuggestions(destSugg, results, destInput);
  }, 350);
});

document.addEventListener('click', (e) => {
  if (!document.getElementById('pickupWrap').contains(e.target)) pickupSugg.classList.remove('open');
  if (!document.getElementById('destWrap').contains(e.target))   destSugg.classList.remove('open');
});

// ── Compare button ───────────────────────────────────────────────
document.getElementById('compareBtn').addEventListener('click', async () => {
  const pickup = pickupInput.value.trim();
  const dest   = destInput.value.trim();
  if (!pickup || !dest) {
    showToast('⚠️ Please enter pickup and destination');
    return;
  }
  showToast('🔍 Comparing prices...');
  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pickup, destination: dest, rideType: selectedRideType })
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.error || 'Failed to compare fares');
    renderRideCards(payload.rides || []);
    document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
    showToast(`✅ ${payload.distance_km} km • ${payload.duration_min} min route loaded`);
  } catch (err) {
    showToast('⚠️ ' + (err.message || 'Could not fetch fares'));
  }
  return;
});

// ── Book a ride ───────────────────────────────────────────────────
function renderRideCards(rides) {
  const rideCards = document.getElementById('rideCards');
  if (!rides.length) {
    rideCards.innerHTML = '<div class="card ride-card fade-in visible" style="padding:1.5rem">No rides found for this route.</div>';
    return;
  }
  const badgeClass = { cheapest: 'grad-green-emerald', fastest: 'grad-blue-cyan', comfort: 'grad-purple-pink' };
  const badgeIcon = { cheapest: '📉', fastest: '⚡', comfort: '🏆' };
  rideCards.innerHTML = rides.map((ride) => `
    <div class="card ride-card fade-in visible">
      <div class="card ride-card-inner">
        ${ride.badge ? `<div class="ride-badge ${badgeClass[ride.badge] || 'grad-purple-pink'}">${badgeIcon[ride.badge] || '🏆'} ${ride.badge}</div>` : ''}
        ${ride.surge ? '<div class="surge-badge">Surge</div>' : ''}
        <div class="ride-logo-box grad-${ride.gradient}">${ride.logo}</div>
        <div class="ride-name">${ride.name}</div>
        <div class="ride-type">${ride.vehicle}</div>
        <div style="display:flex;align-items:baseline">
          <span class="ride-price text-grad-white">₹${ride.price}</span>
          ${ride.savings > 0 ? `<span class="ride-savings">Save ₹${ride.savings}</span>` : ''}
        </div>
        <div class="ride-eta">⏱ ${ride.eta} away</div>
        <button class="book-btn grad-${ride.gradient}" onclick="bookRide('${ride.name.replace(/'/g, "\\'")}')">Book Now</button>
      </div>
    </div>
  `).join('');
}

function bookRide(name) {
  showToast('📱 Opening ' + name + '...');
}

// ── Toast ─────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 2800);
}

// ── Price Trend Chart ─────────────────────────────────────────────
const trendData = {{ trend_data|tojson }};
const ctx = document.getElementById('trendChart').getContext('2d');

// gradient fill helpers
function makeGrad(color) {
  const g = ctx.createLinearGradient(0, 0, 0, 400);
  g.addColorStop(0, color + '4D');
  g.addColorStop(1, color + '00');
  return g;
}

new Chart(ctx, {
  type: 'line',
  data: {
    labels: trendData.map(d => d.time),
    datasets: [
      {
        label: 'Uber', data: trendData.map(d => d.uber),
        borderColor: '#7C3AED', borderWidth: 2,
        backgroundColor: makeGrad('#7C3AED'),
        fill: true, tension: 0.4, pointRadius: 3,
      },
      {
        label: 'Ola', data: trendData.map(d => d.ola),
        borderColor: '#06B6D4', borderWidth: 2,
        backgroundColor: makeGrad('#06B6D4'),
        fill: true, tension: 0.4, pointRadius: 3,
      },
      {
        label: 'Rapido', data: trendData.map(d => d.rapido),
        borderColor: '#22C55E', borderWidth: 2,
        backgroundColor: makeGrad('#22C55E'),
        fill: true, tension: 0.4, pointRadius: 3,
      },
    ]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15,23,42,0.95)',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        titleColor: '#F8FAFC',
        bodyColor: '#94A3B8',
        callbacks: { label: ctx => ' ₹' + ctx.raw }
      }
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94A3B8' } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94A3B8', callback: v => '₹' + v } }
    }
  }
});
</script>
</body>
</html>
"""

# ── Flask Route ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE,
        ride_data=RIDE_DATA,
        trend_data=TREND_DATA,
        features=FEATURES,
        testimonials=TESTIMONIALS,
    )


if __name__ == "__main__":
    # Get the machine's IP address
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    
    print("=" * 60)
    print("  Real Time Taxi Comparer – Taxi Fare Comparison App")
    print("=" * 60)
    print(f"\n✅ Server Running!\n")
    print(f"🏠 Local Access:")
    print(f"   http://localhost:5000")
    print(f"\n🌐 Share with Others (Same Network):")
    print(f"   http://{ip_address}:5000")
    print(f"\n📱 Device IP: {ip_address}")
    print(f"   Share this IP with others to access your app!\n")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host="0.0.0.0", port=5000)
