import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Streamlit page config
st.set_page_config(page_title="Liberalitas Inscriptions", layout="wide")
st.title("📜 Inscriptions Containing 'Liberalitas'")
st.markdown(
    "This app shows where inscriptions mentioning **liberalitas** were found, "
    "with transcription texts and map locations based on archaeological records."
)

# ✅ Read CSV file directly (must be in same folder as this script)
df = pd.read_csv("liberalita_edh.csv")

# Handle missing location data: replace with fallback for specific rows
fallback_rows = [29, 67]  # Index for rows 30 and 68
for idx in fallback_rows:
    if pd.isna(df.loc[idx, "modern find spot"]) or df.loc[idx, "modern find spot"] == "":
        df.loc[idx, "modern find spot"] = df.loc[idx, "ancient find spot"]

# Remove rows with missing transcription or place
df = df.dropna(subset=["transcription", "modern find spot"])

# Initialize geocoder
geolocator = Nominatim(user_agent="liberalitas_app")

@st.cache_data(show_spinner=False)
def geocode_location(place):
    try:
        location = geolocator.geocode(place)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

# Create map
m = folium.Map(location=[41.9, 12.5], zoom_start=5, tiles="CartoDB positron")

# Add markers to map
for i, row in df.iterrows():
    place = row["modern find spot"]
    transcription = row["transcription"]
    
    # Use coordinates column if available
    coords = row.get("coordinates (lat,lng)", "")
    if pd.notna(coords):
        try:
            lat, lon = map(float, coords.split(","))
        except:
            lat, lon = geocode_location(place)
    else:
        lat, lon = geocode_location(place)

    # Only add if coordinates found
    if lat and lon:
        popup_html = f"""
            <strong>{place}</strong><br>
            <pre style='font-size:12px'>{transcription[:500]}...</pre>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=place,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

# Show map
st.subheader("🗺️ Map of Inscriptions")
st_folium(m, width=1000, height=600)

# Show full transcription list
st.subheader("📜 Full Transcriptions")
for i, row in df.iterrows():
    st.markdown(f"**📍 {row['modern find spot']}**")
    st.code(row["transcription"], language="latin")

