import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
import polyline
import math

def main():
    st.set_page_config(page_title="Local Map", layout="wide")

    # 2) Retrieve markers (issues) from Report.py
    markers = st.session_state.get("markers", [])

    st.title("Optimized Your Trip")
    st.write("""
    Using your data to deliver the best route fastest route, counting a one minute penalty per pothole 
    """)

    geolocator = Nominatim(user_agent="optimized_trip_app")

    # Layout
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Plan Your Route")

        start_address = st.text_input("Start Address (street, city)", "")
        dest_address = st.text_input("Destination Address (street, city)", "")

        # Distance threshold for an issue to be considered "near" the route
        threshold_m = st.number_input(
            "Issue proximity threshold (meters)",
            value=150,
            step=50,
            help="Any issue within this distance of the route adds 3 minutes to the route's adjusted time."
        )

        if st.button("Find Best Route"):
            # Geocode addresses
            start_loc = geolocator.geocode(start_address)
            if not start_loc:
                st.error(f"Could not find location for: {start_address}")
                st.stop()

            dest_loc = geolocator.geocode(dest_address)
            if not dest_loc:
                st.error(f"Could not find location for: {dest_address}")
                st.stop()

            start_lat, start_lon = start_loc.latitude, start_loc.longitude
            dest_lat, dest_lon = dest_loc.latitude, dest_loc.longitude

            # OSRM request for up to 5 routes
            # NOTE: If you get 400 errors, try changing "&alternatives=5" to "&alternatives=true"
            osrm_url = (
                f"http://router.project-osrm.org/route/v1/driving/"
                f"{start_lon},{start_lat};{dest_lon},{dest_lat}"
                "?overview=full&geometries=polyline&steps=true"
                "&alternatives=true"
            )

            resp = requests.get(osrm_url)
            if resp.status_code != 200:
                st.error(f"OSRM request failed with code {resp.status_code}. "
                         "Try using '&alternatives=true' if you see 400 errors.")
                st.stop()

            data = resp.json()
            routes = data.get("routes", [])
            if not routes:
                st.error("No routes found from OSRM.")
                st.stop()

            best_route = None
            best_adjusted_time = None

            # Evaluate each route: base_duration + (near_issue_count * 180)
            for route in routes:
                duration_s = route["duration"]
                geometry = route["geometry"]
                route_points = polyline.decode(geometry)

                # Count how many issues lie within threshold_m
                near_count = count_issues_near_route(route_points, markers, threshold_m)

                # 3 minutes = 180 seconds penalty per near issue
                adjusted_time_s = duration_s + (near_count * 180)

                if best_route is None or adjusted_time_s < best_adjusted_time:
                    best_route = route
                    best_adjusted_time = adjusted_time_s

            # Store the chosen route info
            st.session_state["best_route"] = best_route
            st.session_state["start_coords"] = (start_lat, start_lon)
            st.session_state["dest_coords"] = (dest_lat, dest_lon)
            st.session_state["threshold_m"] = threshold_m

            # Summarize the chosen route
            chosen_geometry = best_route["geometry"]
            chosen_steps = best_route["legs"][0].get("steps", [])
            chosen_points = polyline.decode(chosen_geometry)

            chosen_near_count = count_issues_near_route(chosen_points, markers, threshold_m)
            chosen_duration_s = best_route["duration"]
            chosen_time_min = int(chosen_duration_s // 60)
            chosen_time_sec = int(chosen_duration_s % 60)
            chosen_adjusted_s = chosen_duration_s + (chosen_near_count * 180)

            # Show final result
            st.success(
                f"**Chosen route** has {chosen_near_count} nearby issue(s) (within {threshold_m}m). "
                f"Base time: ~{chosen_time_min} min {chosen_time_sec} sec.\n\n"
                f"**Adjusted time** (with penalties): ~{int(chosen_adjusted_s // 60)} min "
                f"{int(chosen_adjusted_s % 60)} sec."
            )

    # Right column: map + step instructions
    with col_right:
        st.subheader("Map & Directions")

        if "best_route" in st.session_state:
            route = st.session_state["best_route"]
            start_lat, start_lon = st.session_state["start_coords"]
            dest_lat, dest_lon = st.session_state["dest_coords"]
            geometry = route["geometry"]
            steps = route["legs"][0].get("steps", [])
            decoded_points = polyline.decode(geometry)

            # Center map
            mid_lat = (start_lat + dest_lat) / 2
            mid_lon = (start_lon + dest_lon) / 2
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=13)

            # Mark start/dest
            folium.Marker([start_lat, start_lon], popup="Start",
                          icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([dest_lat, dest_lon], popup="Destination",
                          icon=folium.Icon(color="blue")).add_to(m)

            # Draw route in red
            folium.PolyLine(decoded_points, color="red", weight=5).add_to(m)

            # Show all issue markers
            for i, issue in enumerate(markers, start=1):
                folium.Marker(
                    [issue["lat"], issue["lon"]],
                    popup=f"Issue #{i}: {issue['description']}",
                    icon=folium.Icon(color="red", icon="info-sign")
                ).add_to(m)

            st_folium(m, width=700, height=500)

            # Turn-by-turn instructions
            st.subheader("Turn-by-Turn Instructions")
            for i, step in enumerate(steps, start=1):
                maneuver = step.get("maneuver", {})
                instruction = maneuver.get("instruction", "[No instruction]")
                distance = step.get("distance", 0)
                st.write(f"**Step {i}**: {instruction} (distance: {distance:.0f} m)")
        else:
            st.info("Enter addresses and click 'Find Best Route' to see your route.")


def count_issues_near_route(route_points, markers, threshold_m):
    """Return how many unique markers are within threshold_m of any point on the route."""
    if not markers:
        return 0

    near_indices = set()
    for idx, issue in enumerate(markers):
        i_lat = issue["lat"]
        i_lon = issue["lon"]
        for (r_lat, r_lon) in route_points:
            dist_m = haversine_distance(r_lat, r_lon, i_lat, i_lon)
            if dist_m <= threshold_m:
                near_indices.add(idx)
                break  # No need to check more route points for this issue

    return len(near_indices)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Return distance in meters using the Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

if __name__ == "__main__":
    main()
