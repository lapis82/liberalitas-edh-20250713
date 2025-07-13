import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Page setup
st.set_page_config(page_title="Liberalitas Inscriptions", layout="wide")
st.title("📜 Inscriptions Containing 'Liberalitas'")
st.markdown("This app shows where inscriptions mentioning **liberalitas** were found, with transcriptions and locations visualized on a map.")

# File upload
uploaded_file = st.file_uploader("📁 Upload the CSV file (`liberalita_edh.csv`)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Handle fallback: replace missing modern find spot with ancient for lines 30 and 68
    fallback_rows = [29, 67]  # zero-based index
    for idx in fallback_rows:
        if pd.isna(df.loc[idx, "modern find spot"]) or df.loc[idx, "modern find spot"] == "":
            df.loc[idx, "modern find spot"] = df.loc[idx, "ancient find spot"]

    # Drop rows missing both transcription and location
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
            pass
        return None, None

    # Create map
    m = folium.Map(location=[41.9, 12.5], zoom_start=5, tiles="CartoDB positron")

    st.subheader("🗺️ Map of Inscriptions")
    for i, row in df.iterrows():
        place = row["modern find spot"]
        transcription = row["transcription"]
        coords = row.get("coordinates (lat,lng)", "")
        if pd.notna(coords):
            try:
                lat, lon = map(float, coords.split(","))
            except:
                lat, lon = geocode_location(place)
        else:
            lat, lon = geocode_location(place)

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

    st_folium(m, width=1000, height=600)

    st.subheader("📜 Full Transcriptions")
    for i, row in df.iterrows():
        place = row["modern find spot"]
        transcription = row["transcription"]
        st.markdown(f"**📍 {place}**")
        st.code(transcription, language="latin")
else:
    st.info("Please upload the `liberalita_edh.csv` file to begin.")
