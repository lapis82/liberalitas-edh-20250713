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
else:
    st.info("👈 Please upload your CSV file using the sidebar to get started!")

if df is not None:
    # Sidebar for filters
    st.sidebar.header("Filters")
    
    # Basic info about the dataset
    st.sidebar.info(f"Total inscriptions: {len(df)}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📍 Location Map", "📜 Transcriptions", "📊 Statistics"])
    
    with tab1:
        st.header("Geographic Distribution of Liberalita Inscriptions")
        
        # Clean and process location data
        locations = df['modern find spot'].dropna().str.strip()
        locations = locations[locations != '']
        
        if len(locations) > 0:
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
                            
                            map_data.append({
                                'latitude': lat,
                                'longitude': lng,
                                'location': row.get('modern find spot', 'Unknown'),
                                'ancient_location': row.get('ancient find spot', 'Unknown'),
                                'country': row.get('country', 'Unknown'),
                                'transcription': str(row.get('transcription', ''))[:100] + '...' if len(str(row.get('transcription', ''))) > 100 else str(row.get('transcription', ''))
                            })
                        except:
                            continue
                
                if map_data:
                    map_df = pd.DataFrame(map_data)
                    
                    # Create the map
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
                            'longitude': False
                        },
                        zoom=3,
                        title="Geographic Distribution of Liberalita Inscriptions"
                    )
                    
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        height=600,
                        margin={"r":0,"t":0,"l":0,"b":0}
                    )
                    
                    st.plotly_chart(fig_map, use_container_width=True)
                    
                    # Show map statistics
                    st.info(f"📍 Showing {len(map_df)} inscriptions with coordinate data")
                else:
                    st.warning("No valid coordinate data found for mapping")
            
            # Create a simple frequency map
            location_counts = Counter(locations)
            
            # Create a DataFrame for visualization
            location_df = pd.DataFrame(list(location_counts.items()), 
                                     columns=['Location', 'Count'])
            
            # Display location statistics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Location Frequency")
                st.dataframe(location_df.sort_values('Count', ascending=False))
            
            with col2:
                st.subheader("Top Locations")
                if len(location_df) > 0:
                    fig = px.bar(location_df.head(10), 
                               x='Count', 
                               y='Location',
                               orientation='h',
                               title="Top 10 Locations by Inscription Count")
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available for chart")
            
            # Search for specific locations
            st.subheader("Search Locations")
            search_term = st.text_input("Enter location name to search:")
            if search_term:
                filtered_locations = location_df[
                    location_df['Location'].str.contains(search_term, case=False, na=False)
                ]
                if not filtered_locations.empty:
                    st.dataframe(filtered_locations)
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
            st.subheader("Search Transcriptions")
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
                    
                    # Highlight "liberalita" in the text
                    if pd.notna(row['Transcription']):
                        highlighted = re.sub(r'(liberalita[e]?)', r'**\1**', 
                                           str(row['Transcription']), flags=re.IGNORECASE)
                        st.markdown("**Highlighted text:**")
                        st.markdown(highlighted)
        else:
            st.warning("No transcription data available in 'transcription' column.")
    
    with tab3:
        st.header("Statistics and Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dataset Overview")
            st.metric("Total Inscriptions", len(df))
            st.metric("Inscriptions with Modern Locations", len(df['modern find spot'].dropna()))
            st.metric("Inscriptions with Transcriptions", len(df['transcription'].dropna()))
            st.metric("Unique Modern Locations", len(df['modern find spot'].dropna().unique()))
            st.metric("Countries Represented", len(df['country'].dropna().unique()))
        
        with col2:
            st.subheader("Data Completeness")
            completeness = {}
            key_columns = ['transcription', 'modern find spot', 'ancient find spot', 'country', 'province / Italic region']
            for col in key_columns:
                if col in df.columns:
                    completeness[col] = (df[col].notna().sum() / len(df)) * 100
            
            if completeness:
                completeness_df = pd.DataFrame(list(completeness.items()), 
                                             columns=['Column', 'Completeness (%)'])
                
                # Clean up column names for display
                column_names = {
                    'transcription': 'Transcriptions',
                    'modern find spot': 'Modern Locations',
                    'ancient find spot': 'Ancient Locations',
                    'country': 'Countries',
                    'province / Italic region': 'Provinces'
                }
                completeness_df['Column'] = completeness_df['Column'].map(column_names)
                
                if len(completeness_df) > 0:
                    fig = px.bar(completeness_df, 
                               x='Column', 
                               y='Completeness (%)',
                               title="Data Completeness by Column")
                    fig.update_xaxis(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for completeness chart")
        
        # Word analysis in transcriptions
        if 'transcription' in df.columns:
            st.subheader("Word Analysis in Transcriptions")
            all_text = ' '.join(df['transcription'].dropna().astype(str))
            
            # Simple word frequency (excluding common words)
            words = re.findall(r'\b\w+\b', all_text.lower())
            common_words = {'et', 'in', 'de', 'ad', 'ex', 'cum', 'pro', 'ab', 'per', 'sub'}
            filtered_words = [word for word in words if len(word) > 2 and word not in common_words]
            
            if filtered_words:
                word_counts = Counter(filtered_words)
                top_words = dict(word_counts.most_common(15))
                
                word_df = pd.DataFrame(list(top_words.items()), 
                                     columns=['Word', 'Frequency'])
                
                fig = px.bar(word_df, 
                           x='Frequency', 
                           y='Word',
                           orientation='h',
                           title="Most Frequent Words in Transcriptions")
                if len(word_df) > 0:
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

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
