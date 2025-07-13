import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Streamlit page setup
st.set_page_config(page_title="Liberalitas Inscriptions", layout="wide")
st.title("📜 Inscriptions Containing 'Liberalitas'")
st.markdown(
    "This app shows where inscriptions mentioning **liberalitas** were found, "
    "with transcription texts and locations based on archaeological records."
)

# ✅ Load the CSV file directly
df = pd.read_csv("liberalita_edh.csv")

# Handle missing location data for rows 30 and 68
fallback_rows = [29, 67]  # index is zero-based
for idx in fallback_rows:
    if pd.isna(df.loc[idx, "modern find spot"]) or df.loc[idx, "modern find spot"] == "":
        df.loc[idx, "modern find spot"] = df.loc[idx, "ancient find spot"]

# Drop rows missing transcription or coordinates
df = df.dropna(subset=["transcription", "modern find spot", "coordinates (lat,lng)"])

# Create a folium map centered on Italy
m = folium.Map(location=[41.9, 12.5], zoom_start=5, tiles="CartoDB positron")

# Add markers to the map using coordinates only
for i, row in df.iterrows():
    place = row["modern find spot"]
    transcription = row["transcription"]
    coords = row["coordinates (lat,lng)"]

    try:
        lat, lon = map(float, coords.split(","))
    except:
        continue  # skip invalid coordinate format

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

# Show the map
st.subheader("🗺️ Map of Inscriptions")
st_folium(m, width=1000, height=600)

# Show all transcription texts below
st.subheader("📜 Full Transcriptions")
for i, row in df.iterrows():
    st.markdown(f"**📍 {row['modern find spot']}**")
    st.code(row["transcription"], language="latin")
