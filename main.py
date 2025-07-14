import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re

# Set page configuration
st.set_page_config(
    page_title="Liberalita EDH Inscriptions",
    page_icon="🏛️",
    layout="wide"
)

# Title and description
st.title("🏛️ Liberalita EDH Inscriptions")
st.markdown("Explore inscriptions containing 'liberalita' from the Epigraphic Database Heidelberg")

# Load data function
@st.cache_data
def load_data(uploaded_file):
    """Load and preprocess the CSV data"""
    try:
        # Load the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Handle missing location data (lines 30 and 68 - using column 'ancient find spot' as fallback)
        # Note: pandas uses 0-based indexing, so line 30 is index 29, line 68 is index 67
        if len(df) > 29 and (pd.isna(df.iloc[29]['modern find spot']) or df.iloc[29]['modern find spot'] == ''):
            df.at[29, 'modern find spot'] = df.iloc[29]['ancient find spot']
        if len(df) > 67 and (pd.isna(df.iloc[67]['modern find spot']) or df.iloc[67]['modern find spot'] == ''):
            df.at[67, 'modern find spot'] = df.iloc[67]['ancient find spot']
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Define the special inscriptions from the PDF (women-related liberalitas inscriptions)
@st.cache_data
def get_women_inscriptions():
    """Return list of inscription IDs that are related to women from the PDF"""
    # Based on the PDF data, these are the inscription references
    women_inscriptions = [
        "CILA 03-01",  # Hispania citerior (Castulo)
        "CIL VIII 937",  # Africa proconsularis (Munificium Seressitanum)
        "CIL VIII 1223",  # Africa proconsularis (Vaga)
        "CIL VIII 1495",  # Africa proconsularis (Thugga)
        "CIL VIII 5142",  # Numidia (Thagaste)
        "CIL VIII 5365",  # Africa proconsularis (Calama)
        "CIL VIII 5366",  # Africa proconsularis (Calama)
        "CIL VIII 10523",  # Africa proconsularis (Ziqua)
        "CIL VIII 12058",  # Africa proconsularis (Muzuca)
        "CIL VIII 26273",  # Africa proconsularis (Uchi Maius)
        "IL Alg 02-03 10120",  # Numidia (Catellum Elefantum)
        "IL Afr 511",  # Africa proconsularis (Thibaris)
        "CIL X 6529",  # Latium et Campania (Cora)
        "AE 1955-151"  # Africa proconsularis (Hippo Regius)
    ]
    return women_inscriptions

def is_women_inscription(hd_no, transcription):
    """Check if this inscription is one of the women-related inscriptions from PDF"""
    women_refs = get_women_inscriptions()
    
    # Try to match based on common patterns in the transcription or reference
    for ref in women_refs:
        # Check if any part of the reference appears in the transcription or HD number
        if ref in str(transcription) or any(part in str(transcription) for part in ref.split() if len(part) > 3):
            return True
    
    # Additional checks based on content patterns from the PDF
    if pd.notna(transcription):
        transcription_str = str(transcription).lower()
        # Look for specific women's names or phrases from the PDF
        women_indicators = [
            'corneliae marullinae',
            'armenia auge',
            'bebenia pauliana',
            'surdinae',
            'asiciae victoriae',
            'iulia victoria',
            'anniae aeliae',
            'bultiae hortensiae',
            'clodia macrina',
            'valeriae marianillae',
            'clodia donata',
            'seiae potitiae',
            'tutiae',
            'vivia severa'
        ]
        
        for indicator in women_indicators:
            if indicator in transcription_str:
                return True
    
    return False

# File upload widget
st.sidebar.header("📁 Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Choose your liberalita_edh.csv file",
    type=['csv'],
    help="Upload your CSV file containing the liberalita inscriptions data"
)

# Load the data
df = None
if uploaded_file is not None:
    df = load_data(uploaded_file)
    if df is not None:
        st.sidebar.success(f"✅ File loaded successfully! ({len(df)} rows)")
        
        # Basic info about the dataset
        women_count = sum(is_women_inscription(row.get('hd-no.', ''), row.get('transcription', '')) for _, row in df.iterrows())
        st.sidebar.info(f"📊 Dataset Overview\n"
                       f"• Total inscriptions: {len(df)}\n"
                       f"• With locations: {len(df['modern find spot'].dropna())}\n"
                       f"• With transcriptions: {len(df['transcription'].dropna())}\n"
                       f"• Countries: {len(df['country'].dropna().unique())}\n"
                       f"• 👩 Women-related: {women_count}")
else:
    st.info("👈 Please upload your CSV file using the sidebar to get started!")

if df is not None:
    # Main content area - now three tabs including women's inscriptions
    tab1, tab2, tab3 = st.tabs(["📍 Location Map", "📜 Transcriptions", "👩 Women's Liberalitas"])
    
    with tab1:
        st.header("Geographic Distribution of Liberalita Inscriptions")
        
        # Clean and process location data with country information
        location_data = []
        for idx, row in df.iterrows():
            modern_spot = row.get('modern find spot')
            country = row.get('country', '')
            
            if pd.notna(modern_spot) and str(modern_spot).strip() != '':
                # Combine location with country for better display
                if pd.notna(country) and str(country).strip() != '':
                    location_display = f"{modern_spot} ({country})"
                else:
                    location_display = str(modern_spot)
                location_data.append(location_display)
        
        if len(location_data) > 0:
            # Create geographic map if coordinates are available
            if 'coordinates (lat,lng)' in df.columns:
                st.subheader("Geographic Map of Inscriptions")
                
                # Parse coordinates and create map data
                map_data = []
                for idx, row in df.iterrows():
                    coords = row.get('coordinates (lat,lng)')
                    if pd.notna(coords) and coords != '':
                        try:
                            # Parse coordinates (format: "lat,lng")
                            lat, lng = coords.split(',')
                            lat, lng = float(lat.strip()), float(lng.strip())
                            
                            # Check if this is a women-related inscription
                            is_women = is_women_inscription(row.get('hd-no.', ''), row.get('transcription', ''))
                            
                            map_data.append({
                                'latitude': lat,
                                'longitude': lng,
                                'location': row.get('modern find spot', 'Unknown'),
                                'ancient_location': row.get('ancient find spot', 'Unknown'),
                                'country': row.get('country', 'Unknown'),
                                'transcription': str(row.get('transcription', ''))[:100] + '...' if len(str(row.get('transcription', ''))) > 100 else str(row.get('transcription', '')),
                                'is_women': is_women,
                                'category': 'Women-related Liberalitas' if is_women else 'General Liberalitas'
                            })
                        except:
                            continue
                
                if map_data:
                    map_df = pd.DataFrame(map_data)
                    
                    # Create the map with different colors for women vs general inscriptions
                    fig_map = px.scatter_mapbox(
                        map_df,
                        lat='latitude',
                        lon='longitude',
                        hover_name='location',
                        hover_data={
                            'ancient_location': True,
                            'country': True,
                            'transcription': True,
                            'latitude': False,
                            'longitude': False,
                            'is_women': False,
                            'category': False
                        },
                        color='category',
                        color_discrete_map={
                            'Women-related Liberalitas': 'red',
                            'General Liberalitas': 'blue'
                        },
                        zoom=3,
                        title="Geographic Distribution of Liberalita Inscriptions"
                    )
                    
                    # Make hover box transparent and improve styling
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        height=600,
                        margin={"r":0,"t":0,"l":0,"b":0},
                        hoverlabel=dict(
                            bgcolor="rgba(255,255,255,0.8)",  # Semi-transparent white background
                            bordercolor="rgba(0,0,0,0.3)",    # Light border
                            font_size=12,
                            font_family="Arial"
                        )
                    )
                    
                    # Update hover template for better formatting
                    fig_map.update_traces(
                        hovertemplate="<b>%{hovertext}</b><br>" +
                                      "Ancient: %{customdata[0]}<br>" +
                                      "Country: %{customdata[1]}<br>" +
                                      "Transcription: %{customdata[2]}<br>" +
                                      "<extra></extra>"  # This removes the default box
                    )
                    
                    st.plotly_chart(fig_map, use_container_width=True)
                    
                    # Show map statistics
                    women_count = len(map_df[map_df['is_women'] == True])
                    total_count = len(map_df)
                    st.info(f"📍 Showing {total_count} inscriptions with coordinate data | 🔴 {women_count} women-related | 🔵 {total_count - women_count} general")
                else:
                    st.warning("No valid coordinate data found for mapping")
            
            # Create a frequency chart with country information
            location_counts = Counter(location_data)
            
            # Create a DataFrame for visualization
            location_df = pd.DataFrame(list(location_counts.items()), 
                                     columns=['Location', 'Count'])
            
            # Display location statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Location Frequency")
                st.dataframe(location_df.sort_values('Count', ascending=False), use_container_width=True)
            
            with col2:
                st.subheader("Top Locations")
                if len(location_df) > 0:
                    # Limit location names for better display
                    display_df = location_df.head(10).copy()
                    # Truncate long location names for better chart readability
                    display_df['Location_Short'] = display_df['Location'].apply(
                        lambda x: x[:30] + '...' if len(x) > 30 else x
                    )
                    
                    fig = px.bar(display_df, 
                               x='Count', 
                               y='Location_Short',
                               orientation='h',
                               title="Top 10 Locations by Inscription Count",
                               hover_data={'Location': True, 'Location_Short': False})
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        yaxis_title="Location"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available for chart")
            
            # Search for specific locations
            st.subheader("🔍 Search Locations")
            search_term = st.text_input("Enter location name to search:")
            if search_term:
                filtered_locations = location_df[
                    location_df['Location'].str.contains(search_term, case=False, na=False)
                ]
                if not filtered_locations.empty:
                    st.dataframe(filtered_locations, use_container_width=True)
                else:
                    st.info("No locations found matching your search.")
        else:
            st.warning("No location data available in 'modern find spot' column.")
    
    with tab2:
        st.header("Inscription Transcriptions")
        
        # Display transcriptions with location info
        transcriptions = df[['transcription', 'modern find spot', 'ancient find spot', 'country', 'province / Italic region']].copy()
        transcriptions.columns = ['Transcription', 'Modern Location', 'Ancient Location', 'Country', 'Province']
        
        # Remove empty transcriptions
        transcriptions = transcriptions.dropna(subset=['Transcription'])
        transcriptions = transcriptions[transcriptions['Transcription'].str.strip() != '']
        
        if len(transcriptions) > 0:
            # Search functionality
            st.subheader("🔍 Search Transcriptions")
            search_transcription = st.text_input("Search in transcriptions:")
            
            if search_transcription:
                filtered_transcriptions = transcriptions[
                    transcriptions['Transcription'].str.contains(search_transcription, case=False, na=False)
                ]
                st.write(f"Found {len(filtered_transcriptions)} matching transcriptions:")
                transcriptions_to_show = filtered_transcriptions
            else:
                transcriptions_to_show = transcriptions
            
            # Display transcriptions
            st.subheader("All Transcriptions")
            for idx, row in transcriptions_to_show.iterrows():
                # Create a more detailed title for each inscription
                title_parts = []
                if pd.notna(row['Modern Location']) and row['Modern Location'] != '':
                    title_parts.append(row['Modern Location'])
                if pd.notna(row['Country']) and row['Country'] != '':
                    title_parts.append(row['Country'])
                
                title = f"Inscription {idx + 1}"
                if title_parts:
                    title += f" - {', '.join(title_parts)}"
                
                with st.expander(title):
                    # Location information
                    col1, col2 = st.columns(2)
                    with col1:
                        if pd.notna(row['Modern Location']) and row['Modern Location'] != '':
                            st.write("**Modern Location:**", row['Modern Location'])
                        if pd.notna(row['Ancient Location']) and row['Ancient Location'] != '':
                            st.write("**Ancient Location:**", row['Ancient Location'])
                    with col2:
                        if pd.notna(row['Country']) and row['Country'] != '':
                            st.write("**Country:**", row['Country'])
                        if pd.notna(row['Province']) and row['Province'] != '':
                            st.write("**Province:**", row['Province'])
                    
                    # Transcription
                    st.write("**Transcription:**")
                    st.text(row['Transcription'])
                    
                    # Highlight "liberalita" in red
                    if pd.notna(row['Transcription']):
                        highlighted = re.sub(r'(liberalita[e]?)', r'<span style="color: red; font-weight: bold;">\1</span>', 
                                           str(row['Transcription']), flags=re.IGNORECASE)
                        st.markdown("**Highlighted text:**")
                        st.markdown(highlighted, unsafe_allow_html=True)
        else:
            st.warning("No transcription data available in 'transcription' column.")
    
    with tab3:
        st.header("👩 Women's Liberalitas Inscriptions")
        st.markdown("**Special collection based on research about women and liberalitas**")
        
        # Filter for women-related inscriptions
        women_inscriptions = []
        for idx, row in df.iterrows():
            if is_women_inscription(row.get('hd-no.', ''), row.get('transcription', '')):
                women_inscriptions.append((idx, row))
        
        if women_inscriptions:
            st.subheader(f"Found {len(women_inscriptions)} Women-Related Inscriptions")
            st.markdown("These inscriptions are highlighted in **red** on the map and relate to women's liberalitas activities.")
            
            # Display women's inscriptions with special formatting
            for idx, (original_idx, row) in enumerate(women_inscriptions, 1):
                # Create title with location info
                title_parts = []
                if pd.notna(row.get('modern find spot')) and row.get('modern find spot') != '':
                    title_parts.append(row.get('modern find spot'))
                if pd.notna(row.get('country')) and row.get('country') != '':
                    title_parts.append(row.get('country'))
                
                title = f"🔴 Women's Inscription {idx}"
                if title_parts:
                    title += f" - {', '.join(title_parts)}"
                
                with st.expander(title, expanded=False):
                    # Create columns for better layout
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Location Information:**")
                        if pd.notna(row.get('modern find spot')):
                            st.write("Modern:", row.get('modern find spot'))
                        if pd.notna(row.get('ancient find spot')):
                            st.write("Ancient:", row.get('ancient find spot'))
                        if pd.notna(row.get('country')):
                            st.write("Country:", row.get('country'))
                    
                    with col2:
                        st.write("**Additional Details:**")
                        if pd.notna(row.get('province / Italic region')):
                            st.write("Province:", row.get('province / Italic region'))
                        if pd.notna(row.get('chronological data')):
                            st.write("Date:", row.get('chronological data'))
                        if pd.notna(row.get('type of monument')):
                            st.write("Monument:", row.get('type of monument'))
                    
                    with col3:
                        st.write("**Reference:**")
                        if pd.notna(row.get('hd-no.')):
                            st.write("HD No.:", row.get('hd-no.'))
                        if pd.notna(row.get('material')):
                            st.write("Material:", row.get('material'))
                    
                    # Full transcription with highlighting
                    st.write("**Complete Transcription:**")
                    if pd.notna(row.get('transcription')):
                        transcription = str(row.get('transcription'))
                        # Highlight liberalita in red
                        highlighted = re.sub(r'(liberalita[e]?)', r'<span style="color: red; font-weight: bold;">\1</span>', 
                                           transcription, flags=re.IGNORECASE)
                        st.markdown(highlighted, unsafe_allow_html=True)
                        
                        # Show raw text in a code block for copying
                        with st.expander("📋 Raw text (for copying)"):
                            st.code(transcription, language=None)
                    else:
                        st.write("No transcription available")
                    
                    # Commentary if available
                    if pd.notna(row.get('commentary')):
                        st.write("**Commentary:**")
                        st.write(row.get('commentary'))
            
            # Summary statistics for women's inscriptions
            st.subheader("📊 Women's Inscriptions Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                # Count by country
                countries = [row.get('country') for _, row in women_inscriptions if pd.notna(row.get('country'))]
                country_counts = Counter(countries)
                if country_counts:
                    st.write("**Distribution by Country:**")
                    for country, count in country_counts.most_common():
                        st.write(f"• {country}: {count}")
            
            with col2:
                # Count by province
                provinces = [row.get('province / Italic region') for _, row in women_inscriptions if pd.notna(row.get('province / Italic region'))]
                province_counts = Counter(provinces)
                if province_counts:
                    st.write("**Distribution by Province:**")
                    for province, count in province_counts.most_common():
                        st.write(f"• {province}: {count}")
        
        else:
            st.info("No women-related liberalitas inscriptions found in the current dataset.")
            st.markdown("""
            **Expected inscriptions from research:**
            - CILA 03-01 (Hispania citerior - Castulo)
            - CIL VIII series (Africa proconsularis)
            - IL Alg series (Numidia)
            - CIL X 6529 (Latium et Campania)
            - AE 1955-151 (Africa proconsularis)
            """)

else:
    st.markdown("""
    ## Welcome to the Liberalita EDH Explorer! 🏛️
    
    This app helps you explore inscriptions containing 'liberalita' from the Epigraphic Database Heidelberg.
    
    **To get started:**
    1. Click on the **"Browse files"** button in the sidebar
    2. Select your `liberalita_edh.csv` file
    3. Explore the locations and transcriptions!
    
    **Your CSV file should contain:**
    - **transcription**: Transcriptions of inscriptions
    - **modern find spot**: Modern locations where inscriptions were found
    - **ancient find spot**: Ancient location data (used as fallback)
    - **country**: Country information
    - **province / Italic region**: Provincial information
    """)
