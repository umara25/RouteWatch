import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

def main():
    st.set_page_config(page_title="Report Local Issues", layout="wide")

    # Check if logged in (if you’re using login logic)

    # Initialize a geolocator
    geolocator = Nominatim(user_agent="my_streamlit_app")

    st.title("Report Local Issues")
    st.write("Use the form on the **left** to add a location. The **map** on the **right** shows reported issues.")

    if "markers" not in st.session_state:
        st.session_state["markers"] = []

    # Two columns
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.header("Add a Marker")

        # Separate inputs: street & city
        street_name = st.text_input("Street Name:")
        city = st.text_input("City:")

        # Combine them
        full_address = f"{street_name}, {city}".strip()

        uploaded_image = st.file_uploader("Upload an image:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.image(uploaded_image, caption="Preview", width=150)

        description = st.text_input("Description of the issue:", "Pothole needs fixing")

        # Add Marker button
        if st.button("Add Marker"):
            if not street_name.strip() or not city.strip():
                st.warning("Please enter both street name and city.")
            else:
                try:
                    location = geolocator.geocode(full_address)
                    if location is None:
                        st.error("Could not find that location. Try something else.")
                    else:
                        marker_info = {
                            "lat": location.latitude,
                            "lon": location.longitude,
                            "description": description,
                            "image_name": uploaded_image.name if uploaded_image else None,
                            "image_data": uploaded_image.getvalue() if uploaded_image else None,
                        }
                        st.session_state["markers"].append(marker_info)
                        st.success(f"Marker added for '{full_address}'.")
                except Exception as e:
                    st.error(f"Error geocoding address: {e}")

    # Right column: map
    with col_right:
        st.header("Map View")

        if st.session_state["markers"]:
            last_marker = st.session_state["markers"][-1]
            center_lat = last_marker["lat"]
            center_lon = last_marker["lon"]
        else:
            center_lat, center_lon = 44.2334,  -76.4930  # default NYC

        # Create Folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        # Plot each marker
        for i, marker in enumerate(st.session_state["markers"], start=1):
            popup_text = f"Issue #{i}: {marker['description']}"
            folium.Marker(
                location=[marker["lat"], marker["lon"]],
                popup=popup_text,
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m)

        st_folium(m, width=700, height=500)

        # Show a list of issues
        if st.session_state["markers"]:
            st.subheader("Reported Issues")
            for i, marker in enumerate(st.session_state["markers"], start=1):
                st.markdown(f"**Issue #{i}** — {marker['description']}")
                st.markdown(f"*Location:* {marker['lat']}, {marker['lon']}")
                if marker["image_data"]:
                    st.image(marker["image_data"], caption=f"Uploaded: {marker['image_name']}", use_column_width=True)
                st.markdown("---")

if __name__ == "__main__":
    main()
