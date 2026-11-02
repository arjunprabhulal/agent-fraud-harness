"""One-time SerpApi Google Hotels snapshot, same params as the original planner (gemini2_travel_v2.py)."""
import os, json, sys, time, requests
TRIPS = [("Las Vegas","2026-12-07","2026-12-10"),("Chicago","2026-12-07","2026-12-10"),
         ("Seattle","2026-12-07","2026-12-10"),("Boston","2026-12-07","2026-12-10"),
         ("Denver","2026-12-07","2026-12-10"),("San Diego","2026-12-07","2026-12-10"),
         ("Nashville","2026-12-07","2026-12-10"),("Miami","2026-12-07","2026-12-10")]
out = {}
for loc, ci, co in TRIPS:
    p = {"api_key": os.environ["SERP_API_KEY"], "engine": "google_hotels", "q": loc, "hl": "en", "gl": "us",
         "check_in_date": ci, "check_out_date": co, "currency": "USD", "sort_by": 3, "rating": 8}
    r = requests.get("https://serpapi.com/search.json", params=p, timeout=60).json()
    if "error" in r: print(loc, "ERROR", r["error"]); continue
    props = []
    for h in r.get("properties", []):
        price = (h.get("rate_per_night") or {}).get("extracted_lowest")
        if price is None or not h.get("property_token"): continue
        props.append({"id": h["property_token"], "source": "google_hotels", "name": h.get("name"),
                      "price": price, "rating": h.get("overall_rating"), "reviews": h.get("reviews"),
                      "location": loc, "hotel_class": h.get("extracted_hotel_class"),
                      "amenities": (h.get("amenities") or [])[:6]})
    out[loc] = {"check_in": ci, "check_out": co, "retrieved": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "search_id": r.get("search_metadata", {}).get("id"), "properties": props}
    print(loc, len(props))
json.dump(out, open(sys.argv[1], "w"), indent=1)
